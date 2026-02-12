"""Skill evaluator using Claude API for classification."""

import json
import re
import requests
from pathlib import Path
from typing import List, Optional
import sys

from pydantic import BaseModel, Field, ValidationError

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config


class SkillInfo(BaseModel):
    """Information about a discovered skill."""
    name: str
    description: str


class SkillRanking(BaseModel):
    """Ranking result for a skill."""
    skill: str
    confidence: float = Field(ge=0.0, le=1.0)


class EvaluationResponse(BaseModel):
    """Response from Claude API classification."""
    candidates: List[SkillRanking]


class SkillEvaluator:
    """Evaluate skills using backend API or direct Claude API."""

    def __init__(self):
        self.config = Config
        self.client = None
        self._skills_cache: Optional[List[SkillInfo]] = None

    def _init_client(self):
        """Initialize Anthropic client lazily (for legacy mode only)."""
        if not self.config.USE_BACKEND_API and not self.client:
            if not self.config.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not set")

            # Import anthropic only when needed (legacy mode)
            import anthropic

            # MiniMax requires special authentication header
            self.client = anthropic.Anthropic(
                api_key=self.config.ANTHROPIC_API_KEY,
                base_url=self.config.ANTHROPIC_BASE_URL,
                default_headers={
                    "Authorization": f"Bearer {self.config.ANTHROPIC_API_KEY}"
                }
            )

    def discover_skills(self) -> List[SkillInfo]:
        """Discover skills from .claude/skills/ directory."""
        if self._skills_cache:
            return self._skills_cache

        skills = []
        skills_dir = self.config.get_skills_dir()

        if not skills_dir.exists():
            return skills

        for skill_file in skills_dir.rglob("SKILL.md"):
            skill_info = self._parse_skill_file(skill_file)
            if skill_info:
                skills.append(skill_info)

        self._skills_cache = skills
        return skills

    def _parse_skill_file(self, skill_path: Path) -> Optional[SkillInfo]:
        """Parse SKILL.md file to extract name and description."""
        try:
            content = skill_path.read_text(encoding="utf-8")

            # Try to extract YAML frontmatter
            yaml_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)

            name = None
            description = None

            if yaml_match:
                yaml_content = yaml_match.group(1)

                # Extract name
                name_match = re.search(r'^name:\s*(.+)$', yaml_content, re.MULTILINE)
                if name_match:
                    name = name_match.group(1).strip().strip('"\'')

                # Extract description
                desc_match = re.search(r'^description:\s*(.+)$', yaml_content, re.MULTILINE)
                if desc_match:
                    description = desc_match.group(1).strip().strip('"\'')

            # Fallback: use directory name if no name found
            if not name:
                name = skill_path.parent.name

            # Fallback: use first paragraph as description
            if not description:
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('---'):
                        description = line[:200]
                        break

            if not description:
                description = f"Skill: {name}"

            return SkillInfo(name=name, description=description)

        except Exception as e:
            print(f"Warning: Failed to parse {skill_path}: {e}", file=sys.stderr)
            return None

    def build_classification_prompt(self, user_prompt: str, skills: List[SkillInfo]) -> str:
        """Build deterministic classification prompt."""
        skill_list = "\n".join([
            f"- {skill.name}: {skill.description}"
            for skill in skills
        ])

        prompt = f"""You are a deterministic skill classifier.

Return ONLY valid JSON.

Available skills:
{skill_list}

User prompt:
\"\"\"
{user_prompt}
\"\"\"

Return JSON:
{{
  "candidates": [
    {{"skill": "skill_name", "confidence": 0.0-1.0}}
  ]
}}

Rules:
- Include ALL skills
- Sort by confidence descending
- No explanation
- No extra text"""

        return prompt

    def call_backend_api(self, user_prompt: str, skills: List[SkillInfo]) -> dict:
        """Call backend API for skill evaluation."""
        backend_url = self.config.get_backend_url()

        # 准备请求数据
        request_data = {
            "user_prompt": user_prompt,
            "skills": [
                {"name": skill.name, "description": skill.description}
                for skill in skills
            ]
        }

        try:
            response = requests.post(
                f"{backend_url}/skill_evaluator/evaluate",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=60  # 60秒超时
            )
            response.raise_for_status()

            # 后端返回格式: {"status": {...}, "result": {"candidates": [...]}}
            response_json = response.json()
            if response_json.get("status", {}).get("code") != 0:
                raise RuntimeError(f"Backend API error: {response_json.get('status', {}).get('message', 'Unknown error')}")

            return response_json.get("result", {})

        except requests.RequestException as e:
            raise RuntimeError(f"Backend API request failed: {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse backend API response: {e}")

    def call_claude_api(self, prompt: str) -> dict:
        """Call Claude API for classification."""
        self._init_client()

        try:
            message = self.client.messages.create(
                model=self.config.CLAUDE_MODEL,
                max_tokens=self.config.MAX_TOKENS,
                temperature=self.config.TEMPERATURE,
                system="You are a skill classification system. Return only valid JSON.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract text from response, skipping thinking blocks (for MiniMax)
            response_text = None
            for block in message.content:
                if block.type == "text":
                    response_text = block.text
                    break

            if not response_text:
                raise ValueError("No text block found in response")

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                raise ValueError(f"No JSON found in response: {response_text}")

            return json.loads(json_match.group(0))

        except anthropic.APIError as e:
            raise RuntimeError(f"Claude API error: {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse JSON response: {e}")

    def evaluate(self, user_prompt: str) -> List[SkillRanking]:
        """Main entry point: evaluate which skills to activate."""
        # Discover skills
        skills = self.discover_skills()

        if not skills:
            return []

        # Choose API based on configuration
        if self.config.USE_BACKEND_API:
            # 使用后端API
            response_data = self.call_backend_api(user_prompt, skills)
        else:
            # 使用直接大模型API (legacy mode)
            prompt = self.build_classification_prompt(user_prompt, skills)
            response_data = self.call_claude_api(prompt)

        # Validate and parse response
        try:
            evaluation = EvaluationResponse(**response_data)
            return evaluation.candidates
        except ValidationError as e:
            raise RuntimeError(f"Invalid response format: {e}")

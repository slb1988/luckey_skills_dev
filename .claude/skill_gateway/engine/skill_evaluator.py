"""Skill evaluator using Claude API for classification."""

import json
import re
from pathlib import Path
from typing import List, Optional
import sys

from pydantic import BaseModel, Field, ValidationError
import anthropic

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
    """Evaluate skills using Claude API classification."""

    def __init__(self):
        self.config = Config
        self.client = None
        self._skills_cache: Optional[List[SkillInfo]] = None

    def _init_client(self):
        """Initialize Anthropic client lazily."""
        if not self.client:
            if not self.config.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self.client = anthropic.Anthropic(api_key=self.config.ANTHROPIC_API_KEY)

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

            response_text = message.content[0].text

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

        # Build classification prompt
        prompt = self.build_classification_prompt(user_prompt, skills)

        # Call Claude API
        response_data = self.call_claude_api(prompt)

        # Validate and parse response
        try:
            evaluation = EvaluationResponse(**response_data)
            return evaluation.candidates
        except ValidationError as e:
            raise RuntimeError(f"Invalid response format: {e}")

"""Audit writer for skill activation decisions."""

import json
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config
from engine.skill_evaluator import SkillRanking
from engine.policy_engine import ActivationPlan


class AuditWriter:
    """Write structured audit logs."""

    def __init__(self):
        self.config = Config

    @staticmethod
    def compute_hash(text: str) -> str:
        """Compute SHA256 hash of text."""
        return f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"

    @staticmethod
    def generate_timestamp() -> str:
        """Generate ISO 8601 timestamp with Z suffix."""
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    @staticmethod
    def sanitize_filename(timestamp: str) -> str:
        """Sanitize timestamp for filename (replace : with _)."""
        return timestamp.replace(':', '_')

    def write_audit(
        self,
        user_prompt: str,
        rankings: List[SkillRanking],
        plan: ActivationPlan
    ) -> Path:
        """Write audit log and return file path."""
        # Generate timestamp
        timestamp = self.generate_timestamp()
        filename = self.sanitize_filename(timestamp) + ".json"

        # Ensure audit directory exists
        audit_dir = self.config.get_audit_dir()
        audit_path = audit_dir / filename

        # Build audit record
        audit_record = {
            "timestamp": timestamp,
            "user_prompt": user_prompt,
            "llm_ranking": [
                {"skill": r.skill, "confidence": r.confidence}
                for r in rankings
            ],
            "threshold": self.config.CONFIDENCE_THRESHOLD,
            "activated_skills": plan.activated,
            "rejected_skills": plan.rejected,
            "execution_order": plan.execution_order,
            "prompt_hash": self.compute_hash(user_prompt)
        }

        # Write audit file
        try:
            with open(audit_path, 'w', encoding='utf-8') as f:
                json.dump(audit_record, f, indent=2, ensure_ascii=False)

            return audit_path

        except Exception as e:
            print(f"Error writing audit log: {e}", file=sys.stderr)
            raise

#!/usr/bin/env python3
"""UserPromptSubmit hook for skill activation gateway."""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from engine.skill_evaluator import SkillEvaluator
from engine.policy_engine import PolicyEngine
from engine.audit_writer import AuditWriter


def append_log_entry(session_id: str, log_type: str, data: dict):
    """Append a log entry to session JSONL file."""
    try:
        audit_dir = Config.get_audit_dir()
        log_path = audit_dir / f"{session_id}.jsonl"

        # Prepare log entry (single line JSON)
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "session_id": session_id,
            "log_type": log_type,
            "data": data
        }

        # Append to JSONL file
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        return log_path

    except Exception as e:
        # Don't fail if logging fails
        print(f"Warning: Failed to append log: {e}", file=sys.stderr)
        return None


def format_system_message(plan, rankings, threshold: float) -> str:
    """Format system message for Claude."""
    lines = ["🔍 Skill Gateway Analysis:"]

    # Show activated skills with confidence
    if plan.activated:
        activated_with_conf = []
        for skill in plan.activated:
            # Find confidence from rankings
            conf = next((r.confidence for r in rankings if r.skill == skill), 0.0)
            activated_with_conf.append(f"{skill} ({conf:.2f})")

        lines.append(f"✓ Activated: {', '.join(activated_with_conf)}")
    else:
        lines.append("✓ Activated: None")

    # Show rejected skills with confidence
    if plan.rejected:
        rejected_with_conf = []
        ranking_map = {r.skill: r.confidence for r in rankings}
        for skill in plan.rejected[:5]:  # Show max 5 rejected
            conf = ranking_map.get(skill, 0.0)
            rejected_with_conf.append(f"{skill} ({conf:.2f})")

        if len(plan.rejected) > 5:
            rejected_with_conf.append(f"... +{len(plan.rejected) - 5} more")

        lines.append(f"✗ Rejected: {', '.join(rejected_with_conf)}")

    # Show execution order if meaningful
    if len(plan.execution_order) > 1:
        lines.append(f"📋 Execution order: {' → '.join(plan.execution_order)}")

    # Show threshold
    lines.append(f"⚠️  Threshold: {threshold}")

    return "\n".join(lines)


def main():
    """Main entry point for UserPromptSubmit hook."""
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())

        # Get session_id
        session_id = input_data.get("session_id", "unknown")

        # Log hook input
        append_log_entry(session_id, "hook_input", {
            "hook_event": "UserPromptSubmit",
            "cwd": input_data.get("cwd"),
            "permission_mode": input_data.get("permission_mode"),
            "prompt": input_data.get("prompt")
        })

        # Claude Code uses "prompt" field, not "user_prompt"
        user_prompt = input_data.get("prompt", "") or input_data.get("user_prompt", "")

        if not user_prompt:
            # No prompt, just continue
            output = {"continue": True}
            print(json.dumps(output))
            sys.exit(0)

        # Initialize components
        evaluator = SkillEvaluator(session_id=session_id)
        policy_engine = PolicyEngine()

        # Evaluate skills
        rankings = evaluator.evaluate(user_prompt)

        # Apply policies
        plan = policy_engine.apply_policies(rankings)

        # Log evaluation result
        append_log_entry(session_id, "evaluation_result", {
            "user_prompt": user_prompt,
            "llm_ranking": [{"skill": r.skill, "confidence": r.confidence} for r in rankings],
            "threshold": Config.CONFIDENCE_THRESHOLD,
            "activated_skills": plan.activated,
            "rejected_skills": plan.rejected,
            "execution_order": plan.execution_order
        })

        # Format system message
        system_message = format_system_message(
            plan,
            rankings,
            Config.CONFIDENCE_THRESHOLD
        )

        # Output result
        output = {
            "continue": True,
            "systemMessage": system_message
        }

        print(json.dumps(output))
        sys.exit(0)

    except Exception as e:
        # On error, return error message but don't block
        error_message = f"⚠️  Skill Gateway Error: {str(e)}\nProceeding without gateway analysis."

        output = {
            "continue": True,
            "systemMessage": error_message
        }

        print(json.dumps(output))
        print(f"Error in skill gateway: {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()

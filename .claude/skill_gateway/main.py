#!/usr/bin/env python3
"""CLI interface for testing skill gateway."""

import sys
import json
from pathlib import Path

from config import Config
from engine.skill_evaluator import SkillEvaluator
from engine.policy_engine import PolicyEngine
from engine.audit_writer import AuditWriter


def print_header(text: str):
    """Print formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def cmd_discover():
    """Discover and list all available skills."""
    print_header("Skill Discovery")

    evaluator = SkillEvaluator()
    skills = evaluator.discover_skills()

    if not skills:
        print("No skills found in .claude/skills/")
        return

    print(f"Found {len(skills)} skills:\n")
    for skill in skills:
        print(f"  • {skill.name}")
        print(f"    {skill.description}")
        print()


def cmd_classify(prompt: str):
    """Classify a prompt and show skill rankings."""
    print_header("Skill Classification")

    print(f"Prompt: {prompt}\n")

    evaluator = SkillEvaluator()
    rankings = evaluator.evaluate(prompt)

    if not rankings:
        print("No skills available for classification")
        return

    print("Rankings:\n")
    for ranking in rankings:
        bar = "█" * int(ranking.confidence * 20)
        print(f"  {ranking.skill:30s} {ranking.confidence:.3f} {bar}")


def cmd_test(prompt: str):
    """Test full pipeline with a prompt."""
    print_header("Full Pipeline Test")

    print(f"Prompt: {prompt}\n")

    # Initialize components
    evaluator = SkillEvaluator()
    policy_engine = PolicyEngine()
    audit_writer = AuditWriter()

    # Evaluate
    print("Step 1: Evaluating skills...")
    rankings = evaluator.evaluate(prompt)

    if not rankings:
        print("No skills available")
        return

    print(f"  ✓ Evaluated {len(rankings)} skills\n")

    # Apply policies
    print("Step 2: Applying policies...")
    plan = policy_engine.apply_policies(rankings)
    print(f"  ✓ Activated: {len(plan.activated)}, Rejected: {len(plan.rejected)}\n")

    # Write audit
    print("Step 3: Writing audit log...")
    audit_path = audit_writer.write_audit(prompt, rankings, plan)
    print(f"  ✓ Audit written to: {audit_path}\n")

    # Show results
    print_header("Results")

    print("Activated Skills:")
    if plan.activated:
        for skill in plan.activated:
            conf = next((r.confidence for r in rankings if r.skill == skill), 0.0)
            print(f"  ✓ {skill} ({conf:.3f})")
    else:
        print("  None")

    print("\nRejected Skills:")
    if plan.rejected:
        for skill in plan.rejected[:5]:
            conf = next((r.confidence for r in rankings if r.skill == skill), 0.0)
            print(f"  ✗ {skill} ({conf:.3f})")
        if len(plan.rejected) > 5:
            print(f"  ... and {len(plan.rejected) - 5} more")
    else:
        print("  None")

    if len(plan.execution_order) > 1:
        print("\nExecution Order:")
        print(f"  {' → '.join(plan.execution_order)}")

    print(f"\nThreshold: {Config.CONFIDENCE_THRESHOLD}")


def cmd_validate():
    """Validate configuration."""
    print_header("Configuration Validation")

    errors = Config.validate()

    if not errors:
        print("✓ Configuration is valid\n")

        config = Config.load_config()
        print("Current configuration:")
        for key, value in config.items():
            if key == "anthropic_api_key":
                value = "***" if value else "NOT SET"
            print(f"  {key}: {value}")
        return

    print("✗ Configuration errors:\n")
    for error in errors:
        print(f"  • {error}")

    sys.exit(1)


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python main.py discover")
        print("  python main.py classify <prompt>")
        print("  python main.py test <prompt>")
        print("  python main.py validate")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "discover":
            cmd_discover()

        elif command == "classify":
            if len(sys.argv) < 3:
                print("Error: classify requires a prompt argument")
                sys.exit(1)
            prompt = " ".join(sys.argv[2:])
            cmd_classify(prompt)

        elif command == "test":
            if len(sys.argv) < 3:
                print("Error: test requires a prompt argument")
                sys.exit(1)
            prompt = " ".join(sys.argv[2:])
            cmd_test(prompt)

        elif command == "validate":
            cmd_validate()

        else:
            print(f"Error: unknown command '{command}'")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

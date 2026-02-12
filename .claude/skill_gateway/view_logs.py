#!/usr/bin/env python3
"""View and analyze JSONL audit logs."""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from config import Config


def parse_timestamp(ts: str) -> datetime:
    """Parse ISO timestamp."""
    return datetime.fromisoformat(ts.replace('Z', '+00:00'))


def format_log_entry(entry: dict, index: int) -> str:
    """Format a single log entry for display."""
    ts = parse_timestamp(entry['timestamp'])
    log_type = entry['log_type']
    data = entry['data']

    lines = [f"\n[{index}] {ts.strftime('%H:%M:%S')} | {log_type}"]

    if log_type == "hook_input":
        lines.append(f"  Prompt: {data.get('prompt', 'N/A')[:80]}")
        lines.append(f"  CWD: {data.get('cwd', 'N/A')}")

    elif log_type == "backend_request":
        req = data.get('request', {})
        lines.append(f"  User Prompt: {req.get('user_prompt', 'N/A')[:80]}")
        lines.append(f"  Skills Count: {len(req.get('skills', []))}")
        lines.append(f"  Backend URL: {data.get('backend_url', 'N/A')}")

        if data.get('error'):
            lines.append(f"  ❌ Error: {data['error']}")
        elif data.get('response'):
            resp = data['response']
            result = resp.get('result', {})
            candidates = result.get('candidates', [])
            lines.append(f"  ✓ Response: {len(candidates)} candidates")

    elif log_type == "evaluation_result":
        lines.append(f"  Activated: {', '.join(data.get('activated_skills', []))}")
        lines.append(f"  Rejected: {len(data.get('rejected_skills', []))} skills")
        lines.append(f"  Execution Order: {' → '.join(data.get('execution_order', []))}")

    return '\n'.join(lines)


def view_log(session_id: str, tail: int = None):
    """View logs for a session."""
    audit_dir = Config.get_audit_dir()
    log_file = audit_dir / f"{session_id}.jsonl"

    if not log_file.exists():
        print(f"❌ Log file not found: {log_file}")
        return

    print(f"📋 Viewing logs: {log_file}")
    print(f"{'=' * 80}")

    entries = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    # Apply tail limit
    if tail:
        entries = entries[-tail:]

    for i, entry in enumerate(entries, 1):
        print(format_log_entry(entry, i))

    print(f"\n{'=' * 80}")
    print(f"Total entries: {len(entries)}")


def list_sessions():
    """List all session log files."""
    audit_dir = Config.get_audit_dir()
    log_files = sorted(audit_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not log_files:
        print("No log files found.")
        return

    print(f"📂 Found {len(log_files)} session logs:")
    print(f"{'=' * 80}")

    for log_file in log_files[:20]:  # Show latest 20
        session_id = log_file.stem
        size = log_file.stat().st_size
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)

        # Count entries
        with open(log_file, 'r', encoding='utf-8') as f:
            entry_count = sum(1 for line in f if line.strip())

        print(f"{session_id}")
        print(f"  Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Size: {size} bytes | Entries: {entry_count}")
        print()


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python view_logs.py list                    # List all sessions")
        print("  python view_logs.py <session-id>            # View all logs for a session")
        print("  python view_logs.py <session-id> --tail 10  # View last 10 entries")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        list_sessions()
    else:
        session_id = command
        tail = None

        if "--tail" in sys.argv:
            tail_index = sys.argv.index("--tail")
            if tail_index + 1 < len(sys.argv):
                tail = int(sys.argv[tail_index + 1])

        view_log(session_id, tail)


if __name__ == "__main__":
    main()

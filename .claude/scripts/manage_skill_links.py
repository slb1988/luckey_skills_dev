#!/usr/bin/env python3
"""
Claude Skills Symlink Manager

This script manages symlinks for nested skills in plugin packs, making them
discoverable by Claude Code.

Usage:
    python manage_skill_links.py setup      # Create symlinks for nested skills
    python manage_skill_links.py cleanup    # Remove managed symlinks
    python manage_skill_links.py status     # Show current status
"""

import argparse
import json
import os
import platform
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set


class Colors:
    """ANSI color codes for terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RED = '\033[91m'
    CYAN = '\033[96m'

    @staticmethod
    def disable():
        """Disable colors for non-interactive terminals"""
        Colors.RESET = ''
        Colors.BOLD = ''
        Colors.GREEN = ''
        Colors.YELLOW = ''
        Colors.BLUE = ''
        Colors.RED = ''
        Colors.CYAN = ''


def get_platform() -> str:
    """Detect the current platform"""
    system = platform.system()
    if system == "Windows":
        return "windows"
    elif system == "Darwin":
        return "mac"
    elif system == "Linux":
        return "linux"
    else:
        return "unknown"


def create_symlink(target: Path, link: Path) -> Tuple[bool, str]:
    """
    Create a symlink in a cross-platform manner.
    On Windows, uses junction points (mklink /J) which don't require admin privileges.
    On macOS/Linux, uses standard symlinks.

    Args:
        target: Path to the target directory
        link: Path where the symlink should be created

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Ensure target exists
        if not target.exists():
            return False, f"Target does not exist: {target}"

        # Check if link already exists
        if link.exists() or is_junction_or_symlink(link):
            if is_junction_or_symlink(link):
                try:
                    existing_target = get_link_target(link).resolve()
                    if existing_target == target.resolve():
                        return True, "Already exists with correct target"
                except Exception:
                    pass
            return False, f"Link already exists: {link}"

        # On Windows, use junction points which don't require admin privileges
        if platform.system() == "Windows":
            import subprocess
            # mklink /J creates a directory junction
            # Note: target must be absolute path for junctions
            target_abs = target.resolve()
            result = subprocess.run(
                ['cmd', '/c', 'mklink', '/J', str(link), str(target_abs)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True, "Created successfully (junction)"
            else:
                return False, f"Failed to create junction: {result.stderr}"
        else:
            # On macOS/Linux, use standard symlinks
            os.symlink(target, link, target_is_directory=True)
            return True, "Created successfully"

    except OSError as e:
        return False, str(e)


def is_junction_or_symlink(path: Path) -> bool:
    """
    Check if a path is a symlink or Windows junction.

    Args:
        path: Path to check

    Returns:
        True if the path is a symlink or junction
    """
    # Standard symlink check
    if path.is_symlink():
        return True

    # Windows junction check (junctions are not detected by is_symlink)
    if platform.system() == "Windows" and path.exists():
        try:
            import stat
            # Junctions have the reparse point attribute
            st = os.stat(path, follow_symlinks=False)
            # Check for reparse point (directory junction)
            if st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                return True
        except (AttributeError, OSError):
            pass

    return False


def get_link_target(link: Path) -> Path:
    """
    Get the target of a symlink or Windows junction.

    Args:
        link: Path to symlink/junction

    Returns:
        Target path (normalized, without \\?\ prefix)
    """
    try:
        # Try standard readlink first
        target = link.readlink()
        # On Windows, remove the \\?\ prefix if present
        target_str = str(target)
        if target_str.startswith('\\\\?\\'):
            target = Path(target_str[4:])
        return target
    except (OSError, NotImplementedError):
        # On Windows, for junctions, we can use resolve()
        if platform.system() == "Windows":
            resolved = link.resolve()
            # If resolve() returns a different path, it's a link
            if resolved != link.absolute():
                return resolved
    return link


def is_managed_symlink(link: Path, skills_dir: Path) -> bool:
    """
    Check if a symlink/junction is managed by this script (points to a plugin pack).

    Args:
        link: Path to check
        skills_dir: Root skills directory

    Returns:
        True if this is a managed symlink/junction
    """
    if not is_junction_or_symlink(link):
        return False

    try:
        target = get_link_target(link)
        # Make target absolute if it's relative
        if not target.is_absolute():
            target = (link.parent / target).resolve()
        else:
            target = target.resolve()

        # Resolve skills_dir to absolute path for comparison
        skills_dir = skills_dir.resolve()

        # Check if target is inside a plugin pack
        for item in skills_dir.iterdir():
            if not item.is_dir() or is_junction_or_symlink(item):
                continue
            plugin_marker = item / ".claude-plugin" / "marketplace.json"
            if plugin_marker.exists():
                try:
                    item_resolved = item.resolve()
                    # Check if target is inside this plugin pack
                    if target.is_relative_to(item_resolved):
                        return True
                except (ValueError, AttributeError):
                    # is_relative_to not available in Python < 3.9
                    try:
                        target.relative_to(item_resolved)
                        return True
                    except ValueError:
                        pass
    except Exception:
        pass

    return False


def find_plugin_packs(skills_dir: Path) -> Dict[str, List[Path]]:
    """
    Find all plugin packs and their nested skills.

    Args:
        skills_dir: Path to the skills directory

    Returns:
        Dict mapping plugin pack names to lists of nested skill paths
    """
    plugin_packs = {}

    for item in skills_dir.iterdir():
        if not item.is_dir() or is_junction_or_symlink(item):
            continue

        marketplace_file = item / ".claude-plugin" / "marketplace.json"
        if not marketplace_file.exists():
            continue

        try:
            with open(marketplace_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            nested_skills = []

            # Handle both direct 'skills' array and 'plugins' array structure
            # Direct skills array
            if 'skills' in data:
                skills_list = data['skills']
                for skill in skills_list:
                    if isinstance(skill, dict):
                        skill_path = skill.get('path', '')
                    else:
                        skill_path = skill  # Handle string paths directly

                    if skill_path:
                        full_path = item / skill_path
                        if full_path.exists() and (full_path / "SKILL.md").exists():
                            nested_skills.append(full_path)

            # Plugins array structure (e.g., axton-obsidian-visual-skills)
            if 'plugins' in data:
                for plugin in data['plugins']:
                    plugin_skills = plugin.get('skills', [])
                    for skill_path in plugin_skills:
                        # Handle relative paths (./excalidraw-diagram -> excalidraw-diagram)
                        if skill_path.startswith('./'):
                            skill_path = skill_path[2:]

                        full_path = item / skill_path
                        if full_path.exists() and (full_path / "SKILL.md").exists():
                            nested_skills.append(full_path)

            if nested_skills:
                plugin_packs[item.name] = nested_skills

        except (json.JSONDecodeError, OSError) as e:
            print(f"{Colors.YELLOW}Warning: Could not parse {marketplace_file}: {e}{Colors.RESET}")

    return plugin_packs


def find_standalone_skills(skills_dir: Path) -> List[Path]:
    """
    Find all standalone skills (direct subdirectories with SKILL.md).

    Args:
        skills_dir: Path to the skills directory

    Returns:
        List of paths to standalone skills
    """
    standalone = []

    for item in skills_dir.iterdir():
        if not item.is_dir() or is_junction_or_symlink(item):
            continue

        # Check if it has SKILL.md directly
        if (item / "SKILL.md").exists():
            # Make sure it's not a plugin pack
            if not (item / ".claude-plugin" / "marketplace.json").exists():
                standalone.append(item)

    return standalone


def setup_links(skills_dir: Path, verbose: bool = False, dry_run: bool = False) -> Dict[str, List[str]]:
    """
    Create symlinks for all nested skills in plugin packs.

    Args:
        skills_dir: Path to the skills directory
        verbose: Print detailed output
        dry_run: Show what would be done without actually doing it

    Returns:
        Dict with 'created', 'skipped', and 'errors' lists
    """
    result = {
        'created': [],
        'skipped': [],
        'errors': []
    }

    plugin_packs = find_plugin_packs(skills_dir)

    if not plugin_packs:
        print(f"{Colors.YELLOW}No plugin packs found with nested skills.{Colors.RESET}")
        return result

    total_skills = sum(len(skills) for skills in plugin_packs.values())
    print(f"Found {len(plugin_packs)} plugin pack(s) with {total_skills} nested skill(s)")
    print()

    if dry_run:
        print(f"{Colors.CYAN}DRY RUN MODE - No changes will be made{Colors.RESET}")
        print()

    print("Creating symlinks:")

    for pack_name, nested_skills in plugin_packs.items():
        if verbose:
            print(f"\n{Colors.BLUE}Plugin Pack: {pack_name}{Colors.RESET}")

        for skill_path in nested_skills:
            skill_name = skill_path.name
            link_path = skills_dir / skill_name

            if dry_run:
                if link_path.exists() or link_path.is_symlink():
                    print(f"  {Colors.YELLOW}[SKIP]{Colors.RESET} {skill_name} (already exists)")
                    result['skipped'].append(skill_name)
                else:
                    print(f"  {Colors.GREEN}[WOULD CREATE]{Colors.RESET} {skill_name} → {pack_name}/{skill_name}/")
                    result['created'].append(skill_name)
                continue

            success, message = create_symlink(skill_path, link_path)

            if success:
                if message == "Already exists with correct target":
                    print(f"  {Colors.YELLOW}✓{Colors.RESET} {skill_name} (already linked)")
                    result['skipped'].append(skill_name)
                else:
                    print(f"  {Colors.GREEN}✓{Colors.RESET} {skill_name} → {pack_name}/{skill_name}/")
                    result['created'].append(skill_name)
            else:
                print(f"  {Colors.RED}✗{Colors.RESET} {skill_name}: {message}")
                result['errors'].append(f"{skill_name}: {message}")

    print()
    if not dry_run:
        print(f"Successfully created {len(result['created'])} symlink(s)")
        if result['skipped']:
            print(f"Skipped {len(result['skipped'])} existing link(s)")
        if result['errors']:
            print(f"{Colors.RED}Failed to create {len(result['errors'])} symlink(s){Colors.RESET}")

    return result


def cleanup_links(skills_dir: Path, verbose: bool = False, dry_run: bool = False) -> Dict[str, List[str]]:
    """
    Remove all managed symlinks.

    Args:
        skills_dir: Path to the skills directory
        verbose: Print detailed output
        dry_run: Show what would be done without actually doing it

    Returns:
        Dict with 'removed' and 'errors' lists
    """
    result = {
        'removed': [],
        'errors': []
    }

    if dry_run:
        print(f"{Colors.CYAN}DRY RUN MODE - No changes will be made{Colors.RESET}")
        print()

    print("Removing managed symlinks:")

    managed_links = []
    for item in skills_dir.iterdir():
        if is_managed_symlink(item, skills_dir):
            managed_links.append(item)

    if not managed_links:
        print(f"  {Colors.YELLOW}No managed symlinks found{Colors.RESET}")
        return result

    for link in managed_links:
        try:
            if dry_run:
                print(f"  {Colors.GREEN}[WOULD REMOVE]{Colors.RESET} {link.name}")
                result['removed'].append(link.name)
            else:
                link.unlink()
                print(f"  {Colors.GREEN}✓{Colors.RESET} {link.name}")
                result['removed'].append(link.name)
        except Exception as e:
            print(f"  {Colors.RED}✗{Colors.RESET} {link.name}: {e}")
            result['errors'].append(f"{link.name}: {e}")

    print()
    if not dry_run:
        print(f"Successfully removed {len(result['removed'])} symlink(s)")
        if result['errors']:
            print(f"{Colors.RED}Failed to remove {len(result['errors'])} symlink(s){Colors.RESET}")

    return result


def show_status(skills_dir: Path) -> None:
    """
    Show the current status of skills and symlinks.

    Args:
        skills_dir: Path to the skills directory
    """
    print(f"{Colors.BOLD}Claude Skills Directory:{Colors.RESET} {skills_dir}")
    print()

    # Find standalone skills
    standalone_skills = find_standalone_skills(skills_dir)
    print(f"{Colors.BOLD}Standalone Skills ({len(standalone_skills)}):{Colors.RESET}")
    if standalone_skills:
        for skill in sorted(standalone_skills, key=lambda x: x.name):
            print(f"  {Colors.GREEN}✓{Colors.RESET} {skill.name}")
    else:
        print(f"  {Colors.YELLOW}(None){Colors.RESET}")
    print()

    # Find plugin packs
    plugin_packs = find_plugin_packs(skills_dir)
    print(f"{Colors.BOLD}Plugin Packs ({len(plugin_packs)}):{Colors.RESET}")
    if plugin_packs:
        for pack_name, nested_skills in sorted(plugin_packs.items()):
            print(f"  {Colors.BLUE}📦{Colors.RESET} {pack_name}")
            print(f"     Contains {len(nested_skills)} nested skill(s):")
            for skill in nested_skills:
                print(f"     - {skill.name}")
    else:
        print(f"  {Colors.YELLOW}(None){Colors.RESET}")
    print()

    # Find active symlinks/junctions
    active_links = []
    for item in skills_dir.iterdir():
        if is_managed_symlink(item, skills_dir):
            try:
                target = get_link_target(item)
                if not target.is_absolute():
                    target = (item.parent / target).resolve()
                else:
                    target = target.resolve()
                active_links.append((item.name, target))
            except Exception:
                active_links.append((item.name, "unknown"))

    print(f"{Colors.BOLD}Active Symlinks ({len(active_links)}):{Colors.RESET}")
    if active_links:
        for link_name, target in sorted(active_links):
            if isinstance(target, Path):
                rel_target = target.relative_to(skills_dir) if target != "unknown" else "unknown"
                print(f"  {Colors.CYAN}→{Colors.RESET} {link_name} → {rel_target}")
            else:
                print(f"  {Colors.CYAN}→{Colors.RESET} {link_name} → {target}")
    else:
        print(f"  {Colors.YELLOW}(No symlinks currently active){Colors.RESET}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Manage symlinks for nested skills in Claude plugin packs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_skill_links.py setup
  python manage_skill_links.py cleanup
  python manage_skill_links.py status
  python manage_skill_links.py setup --dry-run
  python manage_skill_links.py setup --skills-dir /custom/path
        """
    )

    parser.add_argument(
        'command',
        choices=['setup', 'cleanup', 'status'],
        help='Command to execute'
    )

    parser.add_argument(
        '--skills-dir',
        type=Path,
        default=None,
        help='Path to skills directory (default: .claude/skills relative to script)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print detailed output'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually doing it'
    )

    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )

    args = parser.parse_args()

    # Disable colors if requested or not in a TTY
    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    # Determine skills directory
    if args.skills_dir:
        skills_dir = args.skills_dir.resolve()
    else:
        # Default: .claude/skills relative to the script location
        script_dir = Path(__file__).parent
        skills_dir = (script_dir.parent / "skills").resolve()

    # Validate skills directory
    if not skills_dir.exists():
        print(f"{Colors.RED}Error: Skills directory does not exist: {skills_dir}{Colors.RESET}")
        sys.exit(1)

    if not skills_dir.is_dir():
        print(f"{Colors.RED}Error: Skills path is not a directory: {skills_dir}{Colors.RESET}")
        sys.exit(1)

    # Execute command
    try:
        if args.command == 'setup':
            print(f"{Colors.BOLD}Setting up symlinks for nested skills...{Colors.RESET}")
            print()
            result = setup_links(skills_dir, args.verbose, args.dry_run)
            if result['errors'] and not args.dry_run:
                sys.exit(1)

        elif args.command == 'cleanup':
            print(f"{Colors.BOLD}Cleaning up managed symlinks...{Colors.RESET}")
            print()
            result = cleanup_links(skills_dir, args.verbose, args.dry_run)
            if result['errors'] and not args.dry_run:
                sys.exit(1)

        elif args.command == 'status':
            show_status(skills_dir)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Operation cancelled by user{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"{Colors.RED}Unexpected error: {e}{Colors.RESET}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

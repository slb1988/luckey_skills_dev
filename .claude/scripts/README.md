# Claude Skills Link Manager

This script manages directory junctions (Windows) or symlinks (macOS/Linux) for nested skills in Claude plugin packs, making them discoverable by Claude Code.

## Problem

Claude Code expects skills to be organized as direct subdirectories in `.claude/skills/`, each containing a `SKILL.md` file. However, some skills are distributed as plugin packs with nested directory structures that Claude Code doesn't automatically recognize.

For example:
```
.claude/skills/
└── axton-obsidian-visual-skills/       # Plugin pack
    ├── .claude-plugin/marketplace.json  # Defines 3 nested skills
    ├── excalidraw-diagram/SKILL.md
    ├── mermaid-visualizer/SKILL.md
    └── obsidian-canvas-creator/SKILL.md
```

The nested skills are not recognized because Claude Code doesn't recursively scan plugin packs.

## Solution

This script creates directory junctions (Windows) or symlinks (macOS/Linux) at the top level of `.claude/skills/` that point to nested skills within plugin packs, making them discoverable:

```
.claude/skills/
├── axton-obsidian-visual-skills/       # Original plugin pack (preserved)
├── excalidraw-diagram → axton-obsidian-visual-skills/excalidraw-diagram/
├── mermaid-visualizer → axton-obsidian-visual-skills/mermaid-visualizer/
└── obsidian-canvas-creator → axton-obsidian-visual-skills/obsidian-canvas-creator/
```

On Windows, directory junctions are used instead of symlinks because they don't require administrator privileges.

## Usage

### View Current Status

```bash
python .claude/scripts/manage_skill_links.py status
```

Shows:
- Standalone skills (direct subdirectories with SKILL.md)
- Plugin packs and their nested skills
- Currently active junctions/symlinks

### Create Junctions/Symlinks

```bash
python .claude/scripts/manage_skill_links.py setup
```

Creates directory junctions (Windows) or symlinks (macOS/Linux) for all nested skills in plugin packs.

**Preview changes without making them:**
```bash
python .claude/scripts/manage_skill_links.py setup --dry-run
```

### Remove Junctions/Symlinks

```bash
python .claude/scripts/manage_skill_links.py cleanup
```

Removes all managed junctions/symlinks, reverting to the original directory structure.

**Preview what will be removed:**
```bash
python .claude/scripts/manage_skill_links.py cleanup --dry-run
```

### Options

- `--skills-dir PATH` - Specify a custom skills directory (default: `.claude/skills`)
- `--verbose` / `-v` - Show detailed output
- `--dry-run` - Preview changes without executing them
- `--no-color` - Disable colored output

### Examples

```bash
# Setup with verbose output
python .claude/scripts/manage_skill_links.py setup --verbose

# Use custom skills directory
python .claude/scripts/manage_skill_links.py setup --skills-dir /path/to/skills

# Check what cleanup would do
python .claude/scripts/manage_skill_links.py cleanup --dry-run
```

## Cross-Platform Support

The script works on Mac, Linux, and Windows.

### Windows Implementation

On Windows, the script uses **directory junctions** (`mklink /J`) instead of symlinks:

- **No admin privileges required** - Junctions can be created by any user
- **Same functionality** - Junctions work identically to symlinks for directory links
- **Automatic detection** - The script automatically detects Windows and uses junctions

No special configuration or permissions needed on Windows!

## How It Works

1. **Detection**: Scans `.claude/skills/` for directories containing `.claude-plugin/marketplace.json`
2. **Parsing**: Reads marketplace.json to identify nested skill paths
3. **Validation**: Verifies each nested directory contains a `SKILL.md` file
4. **Linking**: Creates directory junctions (Windows) or symlinks (macOS/Linux) at the top level pointing to nested skills
5. **Cleanup**: Removes only junctions/symlinks that point to plugin pack subdirectories

## Safety Features

- Only removes junctions/symlinks (never deletes actual directories)
- Detects conflicts before creating links
- Validates paths before operations
- Dry-run mode for previewing changes
- Clear error messages with recovery suggestions
- Path normalization (handles Windows `\\?\` prefix automatically)

## Plugin Pack Structure

The script supports marketplace.json files with either structure:

### Direct skills array:
```json
{
  "skills": [
    {"path": "skill1"},
    {"path": "skill2"}
  ]
}
```

### Plugins array (recommended):
```json
{
  "plugins": [
    {
      "skills": [
        "./skill1",
        "./skill2"
      ]
    }
  ]
}
```

## Verification

After running `setup`, verify the links:

**Mac/Linux:**
```bash
ls -la .claude/skills/
```

**Windows (Git Bash):**
```bash
ls -la .claude/skills/
```

**Windows (PowerShell):**
```powershell
Get-ChildItem .claude/skills/ | Select-Object Mode, Name, Target
```

**Using the script:**
```bash
python .claude/scripts/manage_skill_links.py status
```

You should see directory junctions (Windows) or symlinks (indicated by `l` on Unix) pointing to plugin pack subdirectories.

## Troubleshooting

### Junctions/Symlinks not created

1. Check that the plugin pack has `.claude-plugin/marketplace.json`
2. Verify nested directories contain `SKILL.md` files
3. Run with `--verbose` to see detailed error messages
4. Check for conflicts with existing directories (use `--dry-run` first)

### Skills still not recognized by Claude Code

1. Verify junctions/symlinks exist: `python .claude/scripts/manage_skill_links.py status`
2. Restart Claude Code to refresh the skills list
3. Check that linked directories contain valid `SKILL.md` files

### Junction shows as directory on Windows

This is normal! Windows directory junctions appear as regular directories in most tools, but they function as links. Verify with:
```bash
python .claude/scripts/manage_skill_links.py status
```

## License

Same as the parent project.

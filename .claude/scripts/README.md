# Claude Skills Symlink Manager

This script manages symlinks for nested skills in Claude plugin packs, making them discoverable by Claude Code.

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

This script creates symlinks at the top level of `.claude/skills/` that point to nested skills within plugin packs, making them discoverable:

```
.claude/skills/
├── axton-obsidian-visual-skills/       # Original plugin pack (preserved)
├── excalidraw-diagram → axton-obsidian-visual-skills/excalidraw-diagram/
├── mermaid-visualizer → axton-obsidian-visual-skills/mermaid-visualizer/
└── obsidian-canvas-creator → axton-obsidian-visual-skills/obsidian-canvas-creator/
```

## Usage

### View Current Status

```bash
python .claude/scripts/manage_skill_links.py status
```

Shows:
- Standalone skills (direct subdirectories with SKILL.md)
- Plugin packs and their nested skills
- Currently active symlinks

### Create Symlinks

```bash
python .claude/scripts/manage_skill_links.py setup
```

Creates symlinks for all nested skills in plugin packs.

**Preview changes without making them:**
```bash
python .claude/scripts/manage_skill_links.py setup --dry-run
```

### Remove Symlinks

```bash
python .claude/scripts/manage_skill_links.py cleanup
```

Removes all managed symlinks, reverting to the original directory structure.

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

### Windows Requirements

On Windows, creating symlinks requires one of:

1. **Developer Mode** (recommended):
   - Settings → Update & Security → Developer Options → Enable Developer Mode
   - No admin privileges needed after enabling

2. **Administrator privileges**:
   - Run Command Prompt or PowerShell as Administrator

The script will provide clear error messages if permissions are insufficient.

## How It Works

1. **Detection**: Scans `.claude/skills/` for directories containing `.claude-plugin/marketplace.json`
2. **Parsing**: Reads marketplace.json to identify nested skill paths
3. **Validation**: Verifies each nested directory contains a `SKILL.md` file
4. **Linking**: Creates symlinks at the top level pointing to nested skills
5. **Cleanup**: Removes only symlinks that point to plugin pack subdirectories

## Safety Features

- Only removes symlinks (never deletes actual directories)
- Detects conflicts before creating symlinks
- Validates paths before operations
- Dry-run mode for previewing changes
- Clear error messages with recovery suggestions

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

After running `setup`, verify the symlinks:

**Mac/Linux:**
```bash
ls -la .claude/skills/
```

**Windows (PowerShell):**
```powershell
Get-ChildItem .claude/skills/ | Select-Object Mode, Name, Target
```

You should see symlinks (indicated by `l` on Unix or `SYMLINK` mode on Windows) pointing to plugin pack subdirectories.

## Troubleshooting

### Symlinks not created

1. Check that the plugin pack has `.claude-plugin/marketplace.json`
2. Verify nested directories contain `SKILL.md` files
3. Run with `--verbose` to see detailed error messages

### Permission denied on Windows

Enable Developer Mode or run as Administrator (see Windows Requirements above).

### Skills still not recognized by Claude Code

1. Verify symlinks exist: `python .claude/scripts/manage_skill_links.py status`
2. Restart Claude Code to refresh the skills list
3. Check that symlinked directories contain valid `SKILL.md` files

## License

Same as the parent project.

# Claude Skills Management Guide

This document describes how to manage Claude Code skills using git submodules in the `luckey_skills` repository.

## Overview

The `luckey_skills_dev` repository uses a symlink (`.claude/skills → /Users/sun/Documents/GitHub/luckey_skills`) to point to the actual skills repository. All skill management should be done in the `luckey_skills` repository.

## Adding a New Git Submodule

Follow these steps to add a new GitHub repository as a git submodule:

### Step 1: Navigate to the Skills Repository

```bash
cd /Users/sun/Documents/GitHub/luckey_skills
```

### Step 2: Add the Submodule

```bash
git submodule add <GITHUB_REPO_URL> <DIRECTORY_NAME>
```

Example:
```bash
git submodule add https://github.com/teng-lin/notebooklm-py.git notebooklm-py
```

### Step 3: Initialize and Update the Submodule

```bash
git submodule update --init --recursive
```

### Step 4: Make the Skill Discoverable (if needed)

**For plugin packs with marketplace.json:**

If the submodule contains a `.claude-plugin/marketplace.json` file (like `axton-obsidian-visual-skills`), use the symlink manager script:

```bash
cd /Users/sun/Documents/GitHub/luckey_skills_dev
python .claude/scripts/manage_skill_links.py setup
```

This will automatically create symlinks to all nested skills defined in the marketplace.json.

**For standalone skills with non-root SKILL.md:**

If the SKILL.md file is not at the root of the submodule, create a manual symlink:

```bash
cd /Users/sun/Documents/GitHub/luckey_skills
ln -s <submodule-name>/<path-to-skill-dir> <skill-name>
```

Example:
```bash
ln -s notebooklm-py/src/notebooklm/data notebooklm
```

**For standalone skills with root SKILL.md:**

No additional steps needed. Claude Code will discover the skill automatically.

### Step 5: Commit the Changes

```bash
git add .gitmodules <submodule-directory> <any-symlinks>
git commit -m "Add <skill-name> as git submodule

- Added <GITHUB_REPO_URL> as a submodule
- [Additional notes about setup if applicable]

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### Step 6: Push to Remote (Optional)

```bash
git push origin main
```

## Managing Existing Submodules

### Update All Submodules

```bash
cd /Users/sun/Documents/GitHub/luckey_skills
git submodule update --remote --merge
```

### Update a Specific Submodule

```bash
cd /Users/sun/Documents/GitHub/luckey_skills/<submodule-name>
git pull origin main
cd ..
git add <submodule-name>
git commit -m "Update <submodule-name> to latest version"
```

### Clone Repository with Submodules

When cloning the luckey_skills repository on a new machine:

```bash
git clone <luckey_skills-repo-url>
cd luckey_skills
git submodule update --init --recursive
```

Or clone with submodules in one command:

```bash
git clone --recurse-submodules <luckey_skills-repo-url>
```

## Current Submodules

### axton-obsidian-visual-skills
- **URL**: https://github.com/axtonliu/axton-obsidian-visual-skills.git
- **Type**: Plugin pack with marketplace.json
- **Skills**: excalidraw-diagram, mermaid-visualizer, obsidian-canvas-creator
- **Setup**: Managed by `manage_skill_links.py`

### notebooklm-py
- **URL**: https://github.com/teng-lin/notebooklm-py.git
- **Type**: Standalone skill with Python library
- **Skills**: notebooklm
- **SKILL.md Location**: `/src/notebooklm/data/SKILL.md`
- **Setup**: Manual symlink (`notebooklm → notebooklm-py/src/notebooklm/data`)
- **Dependencies**: Python 3.10+, httpx, click, rich

## Removing a Submodule

If you need to remove a submodule:

```bash
cd /Users/sun/Documents/GitHub/luckey_skills

# Remove the submodule entry from .git/config
git submodule deinit -f <submodule-name>

# Remove the submodule directory from .git/modules
rm -rf .git/modules/<submodule-name>

# Remove the submodule entry from the working tree
git rm -f <submodule-name>

# Remove any associated symlinks
rm <symlink-name>

# Commit the changes
git commit -m "Remove <submodule-name> submodule"
```

## Troubleshooting

### Skill Not Discovered by Claude Code

1. Check that the skill directory contains a `SKILL.md` file
2. For plugin packs, run `python .claude/scripts/manage_skill_links.py status` to check symlinks
3. For nested skills, ensure symlinks are created correctly
4. Restart Claude Code to refresh the skills list

### Submodule Update Conflicts

If you encounter conflicts when updating submodules:

```bash
cd <submodule-directory>
git status
# Resolve conflicts manually
git add .
git commit -m "Resolve conflicts"
cd ..
git add <submodule-directory>
git commit -m "Update submodule with conflict resolution"
```

### Permission Issues with Symlinks

On Windows, symlink creation may require:
- Developer Mode enabled, OR
- Running as Administrator

See `.claude/scripts/README.md` for more details.

## Best Practices

1. **Always commit submodule updates**: When a submodule is updated, commit the change in the parent repository
2. **Use descriptive commit messages**: Include the submodule URL and setup notes
3. **Document custom symlinks**: Add entries to the "Current Submodules" section when creating manual symlinks
4. **Keep CLAUDE.md updated**: Add new submodules to the documentation as they are added
5. **Test skill discovery**: After adding a submodule, verify the skill appears in Claude Code

## References

- [Git Submodules Documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [Claude Code Skills Guide](https://github.com/anthropics/claude-code)
- [manage_skill_links.py README](.claude/scripts/README.md)

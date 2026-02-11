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

## Skill Activation Gateway

The Skill Activation Gateway is a deterministic AI system that provides audit and observability for skill activation decisions. It intercepts user prompts via a UserPromptSubmit hook and uses Claude API (temperature=0) to classify which skills should be activated.

### Architecture

- **Location**: `.claude/skill_gateway/`
- **Hook**: Configured in `.claude/settings.local.json` under `hooks.UserPromptSubmit`
- **Components**:
  - `hooks/user_prompt_submit.py`: Entry point for UserPromptSubmit hook
  - `engine/skill_evaluator.py`: Claude API classification
  - `engine/policy_engine.py`: Policy enforcement (thresholds, conflicts, dependencies)
  - `engine/audit_writer.py`: Structured audit logging
  - `config.py`: Configuration management
  - `main.py`: CLI for testing and validation

### Configuration

Set the `ANTHROPIC_API_KEY` environment variable:

```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

Configuration in `config.py`:
- **Model**: claude-sonnet-4-5-20250929
- **Temperature**: 0 (deterministic)
- **Confidence Threshold**: 0.75

### Testing

Install dependencies:

```bash
cd .claude/skill_gateway
pip install -r requirements.txt
```

Test commands:

```bash
# Discover available skills
python main.py discover

# Classify a prompt
python main.py classify "Create a Mermaid diagram showing the process flow"

# Test full pipeline
python main.py test "Create a Mermaid diagram showing the process flow"

# Validate configuration
python main.py validate
```

### How It Works

1. User submits a prompt in Claude Code
2. UserPromptSubmit hook triggers `user_prompt_submit.py`
3. Skill evaluator discovers skills from `.claude/skills/`
4. Claude API classifies skill relevance (confidence scores 0.0-1.0)
5. Policy engine applies:
   - Threshold filtering (default: 0.75)
   - Conflict resolution
   - Dependency resolution
   - Execution order determination
6. Audit writer logs decision to `.audit/`
7. SystemMessage is injected into Claude's context with recommendations

### Registry Files

Located in `.claude/skill_gateway/registry/`:

**skill_conflicts.json**: Define conflicting skills
```json
{
  "conflicts": [
    {
      "skills": ["mermaid-visualizer", "excalidraw-diagram"],
      "reason": "Both are diagram generation tools"
    }
  ]
}
```

**skill_dependencies.json**: Define skill dependencies
```json
{
  "dependencies": {
    "skill-name": ["dependency1", "dependency2"]
  }
}
```

### Audit Logs

Audit logs are stored in `.claude/skill_gateway/.audit/` with ISO 8601 timestamps:

```json
{
  "timestamp": "2026-02-11T10:32:21Z",
  "user_prompt": "Create a Mermaid diagram",
  "llm_ranking": [
    {"skill": "mermaid-visualizer", "confidence": 0.92}
  ],
  "threshold": 0.75,
  "activated_skills": ["mermaid-visualizer"],
  "rejected_skills": [],
  "execution_order": ["mermaid-visualizer"],
  "prompt_hash": "sha256:..."
}
```

Audit logs are gitignored and remain local for analysis.

### Customization

**Adjust confidence threshold**: Edit `CONFIDENCE_THRESHOLD` in `config.py`

**Add conflict rules**: Edit `.claude/skill_gateway/registry/skill_conflicts.json`

**Add dependencies**: Edit `.claude/skill_gateway/registry/skill_dependencies.json`

**Disable gateway**: Remove or comment out the UserPromptSubmit hook in `.claude/settings.local.json`

### Troubleshooting

**Gateway not running**:
1. Check `ANTHROPIC_API_KEY` is set: `echo $ANTHROPIC_API_KEY`
2. Verify dependencies: `pip list | grep -E "anthropic|pydantic"`
3. Test hook manually:
   ```bash
   echo '{"user_prompt": "test"}' | python3 .claude/skill_gateway/hooks/user_prompt_submit.py
   ```

**No skills discovered**:
1. Verify `.claude/skills/` symlink: `ls -la .claude/skills`
2. Check for SKILL.md files: `find .claude/skills -name "SKILL.md"`
3. Run: `python .claude/skill_gateway/main.py discover`

**Classification errors**:
1. Check audit logs: `ls -lt .claude/skill_gateway/.audit/ | head`
2. Review stderr output in Claude Code
3. Validate configuration: `python .claude/skill_gateway/main.py validate`

### Portability

The entire `.claude` directory is portable. To use in another project:

1. Copy `.claude/` directory
2. Set `ANTHROPIC_API_KEY` environment variable
3. Install dependencies: `pip install -r .claude/skill_gateway/requirements.txt`
4. Skills are auto-discovered from `.claude/skills/`

The hook configuration uses `${CLAUDE_PROJECT_DIR}` for portable paths.

## References

- [Git Submodules Documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [Claude Code Skills Guide](https://github.com/anthropics/claude-code)
- [manage_skill_links.py README](.claude/scripts/README.md)

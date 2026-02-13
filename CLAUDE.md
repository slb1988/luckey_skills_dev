# Claude Skills Management Guide

This document describes how to manage Claude Code skills using git submodules in the `luckey_skills` repository.

## Overview

The `luckey_skills_dev` repository uses `.claude/skills` as a git submodule pointing to the `luckey_skills` repository (https://github.com/slb1988/luckey_skills.git). All skill management should be done within this submodule.

The `manage_skill_links.py` script automatically creates directory junctions (Windows) or symlinks (macOS/Linux) to make nested skills in plugin packs discoverable by Claude Code. On Windows, junctions are used instead of symlinks as they don't require administrator privileges.

## Adding a New Git Submodule

Follow these steps to add a new GitHub repository as a git submodule:

### Step 1: Navigate to the Skills Directory

```bash
cd .claude/skills
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

**Note:** If submodules appear empty after cloning, run:
```bash
cd <submodule-directory>
git reset --hard HEAD
```

### Step 4: Make the Skill Discoverable (if needed)

**For plugin packs with marketplace.json:**

If the submodule contains a `.claude-plugin/marketplace.json` file (like `axton-obsidian-visual-skills`), use the symlink manager script:

```bash
# From project root
python .claude/scripts/manage_skill_links.py setup
```

This will automatically create directory junctions (Windows) or symlinks (macOS/Linux) to all nested skills defined in the marketplace.json. No administrator privileges required on Windows!

**For standalone skills with non-root SKILL.md:**

If the SKILL.md file is not at the root of the submodule, create a manual junction/symlink:

Windows:
```bash
cd .claude/skills
mklink /J <skill-name> <submodule-name>\<path-to-skill-dir>
```

macOS/Linux:
```bash
cd .claude/skills
ln -s <submodule-name>/<path-to-skill-dir> <skill-name>
```

Example:
```bash
# Windows
mklink /J notebooklm notebooklm-py\src\notebooklm\data

# macOS/Linux
ln -s notebooklm-py/src/notebooklm/data notebooklm
```

**For standalone skills with root SKILL.md:**

No additional steps needed. Claude Code will discover the skill automatically.

### Step 5: Commit the Changes

```bash
# In .claude/skills directory
git add .gitmodules <submodule-directory> <any-junctions-or-symlinks>
git commit -m "Add <skill-name> as git submodule

- Added <GITHUB_REPO_URL> as a submodule
- [Additional notes about setup if applicable]

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Note:** Git does not track junction/symlink targets on Windows, only their existence. Make sure to document any manual junctions in this file's "Current Submodules" section.

### Step 6: Push to Remote (Optional)

```bash
git push origin main
```

## Managing Existing Submodules

### Update All Submodules

```bash
cd .claude/skills
git submodule update --remote --merge
```

### Update a Specific Submodule

```bash
cd .claude/skills/<submodule-name>
git pull origin main
cd ..
git add <submodule-name>
git commit -m "Update <submodule-name> to latest version"
```

### Clone Repository with Submodules

When cloning the luckey_skills_dev repository on a new machine:

```bash
git clone https://github.com/<your-username>/luckey_skills_dev.git
cd luckey_skills_dev
git submodule update --init --recursive

# If .claude/skills submodule has nested submodules, initialize them too:
cd .claude/skills
git submodule update --init --recursive
cd ../..

# Create junctions/symlinks for plugin packs:
python .claude/scripts/manage_skill_links.py setup
```

Or clone with submodules in one command:

```bash
git clone --recurse-submodules https://github.com/<your-username>/luckey_skills_dev.git
cd luckey_skills_dev
python .claude/scripts/manage_skill_links.py setup
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
cd .claude/skills

# Remove the submodule entry from .git/config
git submodule deinit -f <submodule-name>

# Remove the submodule directory from .git/modules
rm -rf .git/modules/<submodule-name>

# Remove the submodule entry from the working tree
git rm -f <submodule-name>

# Remove any associated junctions/symlinks (if applicable)
# Windows: rmdir <junction-name> (DO NOT use /S flag!)
# macOS/Linux: rm <symlink-name>

# Or use the cleanup script:
cd ../..
python .claude/scripts/manage_skill_links.py cleanup

# Commit the changes
cd .claude/skills
git commit -m "Remove <submodule-name> submodule"
```

## Symlink Manager Script

The `manage_skill_links.py` script automates the creation and management of directory junctions (Windows) or symlinks (macOS/Linux) for nested skills in plugin packs.

### Features

- **No Admin Required (Windows)**: Uses directory junctions (`mklink /J`) instead of symlinks, which don't require administrator privileges
- **Cross-Platform**: Automatically detects OS and uses appropriate link type (junction on Windows, symlink on macOS/Linux)
- **Smart Detection**: Automatically finds plugin packs with `.claude-plugin/marketplace.json` and creates links for all nested skills
- **Safe Operations**: Checks for existing links and prevents accidental overwrites
- **Path Normalization**: Handles Windows long path prefix (`\\?\`) automatically

### Commands

```bash
# Show current status of skills and links
python .claude/scripts/manage_skill_links.py status

# Create junctions/symlinks for all nested skills
python .claude/scripts/manage_skill_links.py setup

# Preview what would be created (without making changes)
python .claude/scripts/manage_skill_links.py setup --dry-run

# Remove all managed junctions/symlinks
python .claude/scripts/manage_skill_links.py cleanup

# Preview what would be removed (without making changes)
python .claude/scripts/manage_skill_links.py cleanup --dry-run
```

### How It Works

1. **Discovery**: Scans `.claude/skills` for directories containing `.claude-plugin/marketplace.json`
2. **Extraction**: Reads the marketplace.json to find nested skill paths
3. **Link Creation**: Creates directory junctions (Windows) or symlinks (macOS/Linux) at the root of `.claude/skills`
4. **Verification**: Links point to the nested skill directories within plugin packs

Example:
```
.claude/skills/
├── axton-obsidian-visual-skills/          # Plugin pack (submodule)
│   ├── .claude-plugin/marketplace.json
│   ├── excalidraw-diagram/                # Nested skill
│   ├── mermaid-visualizer/                # Nested skill
│   └── obsidian-canvas-creator/           # Nested skill
├── excalidraw-diagram/                    # → Junction to axton-obsidian-visual-skills/excalidraw-diagram
├── mermaid-visualizer/                    # → Junction to axton-obsidian-visual-skills/mermaid-visualizer
└── obsidian-canvas-creator/               # → Junction to axton-obsidian-visual-skills/obsidian-canvas-creator
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

### Empty Submodule Directories

If a submodule directory appears empty after cloning or updating:

```bash
cd .claude/skills/<submodule-name>
git reset --hard HEAD
```

This forces Git to checkout all files in the submodule.

## Best Practices

1. **Always commit submodule updates**: When a submodule is updated, commit the change in both the submodule and parent repository
2. **Use descriptive commit messages**: Include the submodule URL and setup notes
3. **Use the script for plugin packs**: Always use `manage_skill_links.py setup` for plugin packs instead of creating manual junctions/symlinks
4. **Document custom junctions/symlinks**: Add entries to the "Current Submodules" section when creating manual links
5. **Keep CLAUDE.md updated**: Add new submodules to the documentation as they are added
6. **Test skill discovery**: After adding a submodule, verify the skill appears in Claude Code (check with `manage_skill_links.py status`)

## Skill Activation Gateway

智能技能激活网关，基于 LLM 的确定性分类系统，为技能激活决策提供审计和可观测性。

### 核心功能

- **自动分类**: 拦截用户提示，使用 LLM 评估技能相关性 (置信度 0.0-1.0)
- **策略执行**: 阈值过滤、冲突解析、依赖管理、执行顺序
- **审计日志**: 完整记录每次决策，包含时间戳、评分、哈希值
- **无阻塞**: 发生错误时继续执行，不影响 Claude Code 正常使用

### 架构

```
.claude/skill_gateway/
├── config.py              # 配置（API、阈值）
├── main.py                # CLI 测试工具
├── hooks/
│   └── user_prompt_submit.py    # UserPromptSubmit hook 入口
├── engine/
│   ├── skill_evaluator.py       # LLM 分类
│   ├── policy_engine.py         # 策略引擎
│   └── audit_writer.py          # 审计日志
└── registry/
    ├── skill_conflicts.json     # 冲突规则
    └── skill_dependencies.json  # 依赖规则
```

### 快速开始

**1. 安装依赖**
```bash
pip install -r .claude/skill_gateway/requirements.txt
```

**2. 测试系统**
```bash
# 验证配置
python3 .claude/skill_gateway/main.py validate

# 发现技能
python3 .claude/skill_gateway/main.py discover

# 分类测试
python3 .claude/skill_gateway/main.py classify "创建流程图"
```

**3. 自动运行**
系统已配置为 UserPromptSubmit hook，每次提交提示时自动运行。

### 当前配置

- **API**: MiniMax API (兼容 Anthropic SDK)
- **模型**: MiniMax-M2.1
- **温度**: 0.0 (确定性输出)
- **阈值**: 0.75 (可在 `config.py` 调整)
- **API Key**: 在 `config.py` 中配置（非环境变量）

详见: `.claude/skill_gateway/MINIMAX_SETUP.md`

### 定制化

**调整阈值**: 编辑 `config.py` 中的 `CONFIDENCE_THRESHOLD`

**冲突规则**: 编辑 `registry/skill_conflicts.json`
```json
{
  "conflicts": [
    {"skills": ["skill-a", "skill-b"], "reason": "描述"}
  ]
}
```

**依赖规则**: 编辑 `registry/skill_dependencies.json`
```json
{
  "dependencies": {
    "skill-name": ["dependency1", "dependency2"]
  }
}
```

**禁用网关**: 在 `.claude/settings.local.json` 中注释掉 `hooks.UserPromptSubmit`

### 审计日志

位置: `.claude/skill_gateway/.audit/<session-id>.jsonl`（已 gitignore）

**格式**: JSON Lines (JSONL) - 每行一个 JSON 对象，方便追加和逐行解析

示例 `.jsonl` 文件内容:
```jsonl
{"timestamp":"2026-02-12T14:47:04Z","session_id":"abc-123","log_type":"hook_input","data":{"prompt":"创建流程图"}}
{"timestamp":"2026-02-12T14:47:05Z","session_id":"abc-123","log_type":"backend_request","data":{"request":{...},"response":{...}}}
{"timestamp":"2026-02-12T14:47:05Z","session_id":"abc-123","log_type":"evaluation_result","data":{"activated_skills":["mermaid-visualizer"]}}
```

**日志类型**:
- `hook_input`: UserPromptSubmit hook 触发时的输入
- `backend_request`: 后端 API 请求/响应详情
- `evaluation_result`: 最终的技能激活决策

**查看日志**:
```bash
# 列出所有会话
python .claude/skill_gateway/view_logs.py list

# 查看特定会话的日志
python .claude/skill_gateway/view_logs.py <session-id>

# 只看最后 10 条
python .claude/skill_gateway/view_logs.py <session-id> --tail 10
```

详见: `.claude/skill_gateway/LOGGING.md`

### 测试验证

已通过场景:
- ✅ 单技能激活
- ✅ 多技能激活 + 执行顺序
- ✅ 冲突解析（自动移除低置信度冲突项）
- ✅ 阈值过滤（< 0.75 不激活）
- ✅ 中英文支持
- ✅ Hook 集成

详见: `.claude/skill_gateway/TEST_RESULTS.md`

### 未来迭代方向

- 支持更多 LLM 提供商
- 动态阈值调整
- 技能性能分析
- 用户反馈学习
- Web UI 审计查看器

### 故障排查

```bash
# 验证配置
python3 .claude/skill_gateway/main.py validate

# 查看最新审计日志
ls -lt .claude/skill_gateway/.audit/ | head

# 手动测试 hook
echo '{"user_prompt": "test"}' | \
  python3 .claude/skill_gateway/hooks/user_prompt_submit.py
```

## References

- [Git Submodules Documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [Claude Code Skills Guide](https://github.com/anthropics/claude-code)
- [manage_skill_links.py README](.claude/scripts/README.md)

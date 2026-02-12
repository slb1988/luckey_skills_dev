# Skill Gateway Debug Guide

## 输入日志记录

UserPromptSubmit hook 会自动记录每次调用的输入数据，用于调试和分析。

### 日志位置

```
.claude/skill_gateway/.audit/
```

### 文件命名格式

```
{timestamp}_{session_id}_input.json
```

示例:
- `2026-02-12T13_31_35_068862Z_test-session-123_input.json`
- `2026-02-12T13_33_04_675037Z_unknown_input.json` (无 session_id)

### 日志内容

```json
{
  "timestamp": "2026-02-12T13:31:35.068862Z",
  "session_id": "test-session-123",
  "hook_event": "UserPromptSubmit",
  "input_data": {
    "session_id": "test-session-123",
    "user_prompt": "创建一个测试图表",
    "cwd": "/test/path",
    "hook_event_name": "UserPromptSubmit"
  }
}
```

### 字段说明

- **timestamp**: ISO 8601 格式的 UTC 时间戳
- **session_id**: Claude Code 会话 ID（如果有）
- **hook_event**: Hook 事件名称（固定为 "UserPromptSubmit"）
- **input_data**: Hook 接收到的完整输入数据
  - `session_id`: 会话标识符
  - `user_prompt`: 用户输入的提示
  - `cwd`: 当前工作目录
  - `hook_event_name`: Hook 事件名称

## 审计日志

技能激活决策的审计日志与输入日志存储在同一目录。

### 文件命名格式

```
{timestamp}.json
```

示例:
- `2026-02-12T00_47_38.926558Z.json`

### 日志内容

```json
{
  "timestamp": "2026-02-12T00:47:38.926558Z",
  "user_prompt": "创建一个 Mermaid 序列图",
  "llm_ranking": [
    {"skill": "mermaid-visualizer", "confidence": 0.95},
    {"skill": "notebooklm", "confidence": 0.95}
  ],
  "threshold": 0.75,
  "activated_skills": ["notebooklm", "mermaid-visualizer"],
  "rejected_skills": [],
  "execution_order": ["mermaid-visualizer", "notebooklm"],
  "prompt_hash": "sha256:adb852425..."
}
```

## 日志关联

可以通过时间戳关联输入日志和审计日志：

```bash
# 查看最近的输入日志
ls -lt .claude/skill_gateway/.audit/*_input.json | head -5

# 查看最近的审计日志
ls -lt .claude/skill_gateway/.audit/*.json | grep -v "_input.json" | head -5

# 查看特定会话的所有日志
ls -lt .claude/skill_gateway/.audit/*test-session-123* | head -10
```

## 调试工作流

### 1. 查看 Hook 输入

```bash
# 查看最新的输入日志
cat $(ls -t .claude/skill_gateway/.audit/*_input.json | head -1)
```

### 2. 检查技能评估

```bash
# 查看最新的审计日志
cat $(ls -t .claude/skill_gateway/.audit/*.json | grep -v "_input.json" | head -1)
```

### 3. 手动测试 Hook

```bash
echo '{"session_id": "debug-001", "user_prompt": "创建流程图"}' | \
  python3 .claude/skill_gateway/hooks/user_prompt_submit.py
```

### 4. 清理旧日志

```bash
# 删除 7 天前的日志
find .claude/skill_gateway/.audit/ -name "*.json" -mtime +7 -delete

# 只保留最近 50 条日志
ls -t .claude/skill_gateway/.audit/*.json | tail -n +51 | xargs rm -f
```

## 常见问题排查

### Hook 未执行

1. 检查 hook 配置:
   ```bash
   cat .claude/settings.local.json | grep -A 10 "UserPromptSubmit"
   ```

2. 验证脚本权限:
   ```bash
   ls -la .claude/skill_gateway/hooks/user_prompt_submit.py
   ```

3. 手动测试:
   ```bash
   echo '{"user_prompt": "test"}' | python3 .claude/skill_gateway/hooks/user_prompt_submit.py
   ```

### 无输入日志生成

1. 检查 .audit 目录权限:
   ```bash
   ls -lad .claude/skill_gateway/.audit/
   ```

2. 查看 stderr 输出（在 Claude Code 终端中）

3. 验证写入权限:
   ```bash
   touch .claude/skill_gateway/.audit/test.json && rm .claude/skill_gateway/.audit/test.json
   ```

### 后端 API 连接失败

当前配置使用后端 API (`USE_BACKEND_API=True`)。如果看到连接错误：

1. 检查后端服务状态:
   ```bash
   curl http://127.0.0.1:5000/health || echo "Backend not running"
   ```

2. 临时切换到直接 API 模式:
   编辑 `config.py`:
   ```python
   USE_BACKEND_API: bool = False  # 使用直接大模型API
   ```

3. 查看后端日志（如果有后端服务）

## 性能分析

### 统计日志数量

```bash
# 输入日志
ls -1 .claude/skill_gateway/.audit/*_input.json 2>/dev/null | wc -l

# 审计日志
ls -1 .claude/skill_gateway/.audit/*.json 2>/dev/null | grep -v "_input.json" | wc -l
```

### 分析激活率

```bash
# 统计激活技能的日志数量
grep -l '"activated_skills": \[' .claude/skill_gateway/.audit/*.json | \
  grep -v "_input.json" | wc -l
```

### 查看高频技能

```bash
# 统计每个技能的激活次数
grep -h '"activated_skills"' .claude/skill_gateway/.audit/*.json | \
  grep -v "_input.json" | \
  grep -o '"[a-z-]*"' | sort | uniq -c | sort -rn
```

## 日志保留策略

建议保留策略：
- **开发环境**: 保留 7-30 天
- **生产环境**: 保留 30-90 天
- **长期分析**: 定期导出到外部存储

所有日志文件已在 `.gitignore` 中配置，不会被提交到版本控制。

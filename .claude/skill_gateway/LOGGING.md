# Skill Gateway Logging Guide

## 日志格式：JSON Lines (JSONL)

所有审计日志使用 **JSON Lines** 格式（也称 NDJSON），每行是一个独立的 JSON 对象，方便追加和逐行解析。

### 日志位置

```
.claude/skill_gateway/.audit/<session-id>.jsonl
```

每个 Claude Code 会话有一个唯一的 session ID，该会话的所有日志都追加到同一个 `.jsonl` 文件中。

## 日志类型

每条日志都包含以下字段：

```json
{
  "timestamp": "2026-02-12T14:47:04.343317Z",
  "session_id": "test-jsonl-123",
  "log_type": "hook_input",
  "data": { ... }
}
```

### 1. hook_input

**时机**: UserPromptSubmit hook 触发时

**内容**:
```json
{
  "log_type": "hook_input",
  "data": {
    "hook_event": "UserPromptSubmit",
    "cwd": "/path/to/working/directory",
    "permission_mode": "default",
    "prompt": "用户输入的提示"
  }
}
```

### 2. backend_request

**时机**: 调用后端 API 评估技能时（成功或失败都会记录）

**内容**:
```json
{
  "log_type": "backend_request",
  "data": {
    "request": {
      "user_prompt": "用户提示",
      "skills": [
        {"name": "技能名", "description": "技能描述"}
      ]
    },
    "response": {
      "status": {"code": 0, "message": "OK"},
      "result": {
        "candidates": [
          {"skill": "技能名", "confidence": 0.95}
        ]
      }
    },
    "error": null,  // 如果有错误，这里会记录错误信息
    "backend_url": "http://127.0.0.1:5000"
  }
}
```

### 3. evaluation_result

**时机**: 完成技能评估和策略应用后

**内容**:
```json
{
  "log_type": "evaluation_result",
  "data": {
    "user_prompt": "用户提示",
    "llm_ranking": [
      {"skill": "技能名", "confidence": 0.95}
    ],
    "threshold": 0.75,
    "activated_skills": ["技能1", "技能2"],
    "rejected_skills": ["技能3"],
    "execution_order": ["技能1", "技能2"]
  }
}
```

## 查看日志

### 使用命令行工具

```bash
# 列出所有会话日志
python .claude/skill_gateway/view_logs.py list

# 查看指定会话的完整日志
python .claude/skill_gateway/view_logs.py <session-id>

# 只查看最后 N 条日志
python .claude/skill_gateway/view_logs.py <session-id> --tail 10
```

### 手动查看

```bash
# 查看最新的会话日志
ls -t .claude/skill_gateway/.audit/*.jsonl | head -1 | xargs cat

# 使用 jq 美化输出
cat .claude/skill_gateway/.audit/<session-id>.jsonl | jq '.'

# 只查看后端请求日志
cat .claude/skill_gateway/.audit/<session-id>.jsonl | jq 'select(.log_type == "backend_request")'

# 统计每个会话的日志条目数
wc -l .claude/skill_gateway/.audit/*.jsonl
```

### Python 解析示例

```python
import json
from pathlib import Path

log_file = Path(".claude/skill_gateway/.audit/<session-id>.jsonl")

# 逐行读取
with open(log_file, 'r', encoding='utf-8') as f:
    for line in f:
        entry = json.loads(line)
        print(f"{entry['timestamp']} | {entry['log_type']}")

        # 处理不同类型的日志
        if entry['log_type'] == 'backend_request':
            data = entry['data']
            if data.get('error'):
                print(f"  ERROR: {data['error']}")
            else:
                result = data['response']['result']
                print(f"  Candidates: {len(result['candidates'])}")
```

## 日志示例

完整的一次技能评估流程会产生 3 条日志：

```jsonl
{"timestamp":"2026-02-12T14:47:04.343317Z","session_id":"test-123","log_type":"hook_input","data":{"hook_event":"UserPromptSubmit","cwd":"/project","prompt":"创建流程图"}}
{"timestamp":"2026-02-12T14:47:05.123456Z","session_id":"test-123","log_type":"backend_request","data":{"request":{"user_prompt":"创建流程图","skills":[{"name":"mermaid-visualizer","description":"..."}]},"response":{"status":{"code":0},"result":{"candidates":[{"skill":"mermaid-visualizer","confidence":0.95}]}},"error":null,"backend_url":"http://127.0.0.1:5000"}}
{"timestamp":"2026-02-12T14:47:05.234567Z","session_id":"test-123","log_type":"evaluation_result","data":{"user_prompt":"创建流程图","llm_ranking":[{"skill":"mermaid-visualizer","confidence":0.95}],"threshold":0.75,"activated_skills":["mermaid-visualizer"],"rejected_skills":[],"execution_order":["mermaid-visualizer"]}}
```

## 日志管理

### 清理旧日志

```bash
# 删除 30 天前的日志
find .claude/skill_gateway/.audit -name "*.jsonl" -mtime +30 -delete

# 只保留最近 100 个会话的日志
ls -t .claude/skill_gateway/.audit/*.jsonl | tail -n +101 | xargs rm -f
```

### 归档日志

```bash
# 压缩旧日志
tar -czf audit-logs-$(date +%Y%m%d).tar.gz .claude/skill_gateway/.audit/*.jsonl
mv audit-logs-*.tar.gz ~/archives/
```

## 故障排查

### 日志文件不存在

**原因**: hook 可能未被触发，或者 session_id 不正确

**排查**:
```bash
# 检查最新的日志文件
ls -lt .claude/skill_gateway/.audit/*.jsonl | head -5

# 查看 Claude Code 的 session ID
cat ~/.claude/projects/*/transcript.jsonl | jq '.session_id' | tail -1
```

### 日志条目不完整

**原因**: hook 执行过程中发生异常

**排查**:
```bash
# 检查最后一条日志的类型
tail -1 .claude/skill_gateway/.audit/<session-id>.jsonl | jq '.log_type'

# 如果只有 hook_input 但没有 backend_request，说明评估失败
# 查看错误信息（如果有）
tail -1 .claude/skill_gateway/.audit/<session-id>.jsonl | jq '.data.error'
```

### 后端请求记录为 error

**原因**: 后端 API 不可用或超时

**排查**:
```bash
# 查看错误详情
cat .claude/skill_gateway/.audit/<session-id>.jsonl | \
  jq 'select(.log_type == "backend_request" and .data.error != null)'

# 检查后端 URL
python -c "from config import Config; print(Config.get_backend_url())"

# 测试后端连接
curl -X POST http://127.0.0.1:5000/skill_evaluator/evaluate \
  -H "Content-Type: application/json" \
  -d '{"user_prompt":"test","skills":[]}'
```

## 最佳实践

1. **定期清理**: JSONL 文件会随着使用不断增长，建议定期清理旧日志
2. **使用 tail 参数**: 查看长日志时，使用 `--tail` 参数只看最新的几条
3. **结合 jq 使用**: 使用 `jq` 工具可以方便地过滤和格式化 JSONL 数据
4. **保留错误日志**: 出现错误时，保留相关的 `.jsonl` 文件用于调试
5. **监控文件大小**: 如果某个会话的 `.jsonl` 文件过大（>10MB），可能需要检查是否有异常循环

## 与后端 API 的集成

后端 API 也应该记录请求日志，建议格式：

```python
# 后端服务器日志 (示例)
import logging

logger = logging.getLogger('skill_evaluator')
logger.info('Request received', extra={
    'user_prompt': user_prompt,
    'skills_count': len(skills),
    'client_ip': request.remote_addr
})

# 响应后记录
logger.info('Response sent', extra={
    'candidates_count': len(candidates),
    'processing_time_ms': elapsed_ms
})
```

这样可以在前端（JSONL）和后端（服务器日志）都有完整的审计记录。

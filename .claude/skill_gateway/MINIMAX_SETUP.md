# MiniMax API Configuration

This skill gateway is configured to use MiniMax API (Anthropic-compatible) instead of the standard Anthropic API.

## Configuration Details

### API Settings
- **Base URL**: `https://api.minimaxi.com/anthropic`
- **Model**: `MiniMax-M2.1`
- **API Key**: Hardcoded in `config.py` (not using environment variables)
- **Temperature**: 0.0 (deterministic)

### Key Differences from Standard Anthropic API

1. **Authentication**: MiniMax requires explicit Bearer token in Authorization header
2. **Response Format**: Includes `ThinkingBlock` in addition to `TextBlock`
3. **Model Name**: Uses `MiniMax-M2.1` instead of Claude model names

## Implementation Details

### config.py
```python
ANTHROPIC_API_KEY = "sk-cp-hwuSmkJkDzEkH_kpLm6jUqEvKMQbJBMm0pkq4KhRHC94lnoHvhSLEJ-6fDRfycBmL_FSeIKOoiW443RUJvkaKkK-ABW4kBuY6_QbGjDh7TQ3aAACyMZdlgA"
ANTHROPIC_BASE_URL = "https://api.minimaxi.com/anthropic"
CLAUDE_MODEL = "MiniMax-M2.1"
```

### skill_evaluator.py
```python
# Client initialization with custom auth header
self.client = anthropic.Anthropic(
    api_key=self.config.ANTHROPIC_API_KEY,
    base_url=self.config.ANTHROPIC_BASE_URL,
    default_headers={
        "Authorization": f"Bearer {self.config.ANTHROPIC_API_KEY}"
    }
)

# Response parsing to handle ThinkingBlock
for block in message.content:
    if block.type == "text":
        response_text = block.text
        break
```

## Testing

All tests passed successfully:

```bash
# Validate configuration
python3 .claude/skill_gateway/main.py validate
# ✓ Configuration is valid

# Test skill discovery
python3 .claude/skill_gateway/main.py discover
# ✓ Found 6 skills

# Test classification
python3 .claude/skill_gateway/main.py classify "创建一个流程图"
# ✓ excalidraw-diagram (0.950), mermaid-visualizer (0.900)

# Test full pipeline
python3 .claude/skill_gateway/main.py test "创建 Mermaid 图表"
# ✓ Activated: mermaid-visualizer (1.000)

# Test hook
echo '{"user_prompt": "用 Excalidraw 创建架构图"}' | \
  python3 .claude/skill_gateway/hooks/user_prompt_submit.py
# ✓ Activated: excalidraw-diagram (1.00)
```

## Switching Back to Anthropic API

To switch back to standard Anthropic API:

1. Modify `config.py`:
   ```python
   ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
   ANTHROPIC_BASE_URL = None  # or remove this line
   CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
   ```

2. Modify `skill_evaluator.py`:
   ```python
   # Remove default_headers parameter
   self.client = anthropic.Anthropic(
       api_key=self.config.ANTHROPIC_API_KEY
   )

   # Simplify response parsing (optional)
   response_text = message.content[0].text
   ```

3. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY=your_anthropic_key
   ```

## Security Note

The API key is currently hardcoded in `config.py` for testing purposes. For production use, consider:
- Using environment variables
- Storing in secure vault (e.g., AWS Secrets Manager)
- Using key rotation policies
- Restricting file permissions: `chmod 600 .claude/skill_gateway/config.py`

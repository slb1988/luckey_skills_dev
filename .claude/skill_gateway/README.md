# Skill Activation Gateway

Deterministic AI skill activation gateway with audit and observability for Claude Code.

## Quick Start

### Prerequisites

1. Set API key:
   ```bash
   export ANTHROPIC_API_KEY=your_key_here
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Testing

```bash
# Validate configuration
python main.py validate

# Discover skills
python main.py discover

# Classify a prompt
python main.py classify "Create a Mermaid diagram showing process flow"

# Test full pipeline
python main.py test "Create a Mermaid diagram showing process flow"
```

### Test Hook Manually

```bash
echo '{"user_prompt": "Create a diagram"}' | python hooks/user_prompt_submit.py
```

## Directory Structure

```
skill_gateway/
├── config.py                   # Configuration
├── main.py                     # CLI for testing
├── requirements.txt            # Python dependencies
├── hooks/
│   └── user_prompt_submit.py  # UserPromptSubmit hook
├── engine/
│   ├── skill_evaluator.py     # Claude API classification
│   ├── policy_engine.py       # Policy enforcement
│   └── audit_writer.py        # Audit logging
├── registry/
│   ├── skill_conflicts.json   # Conflict rules
│   └── skill_dependencies.json # Dependency rules
└── .audit/                     # Audit logs (gitignored)
```

## How It Works

1. **Skill Discovery**: Scans `.claude/skills/` for SKILL.md files
2. **Classification**: Uses Claude API (temp=0) to rank skill relevance
3. **Policy Application**: Applies threshold, resolves conflicts, handles dependencies
4. **Audit Logging**: Writes structured JSON logs to `.audit/`
5. **SystemMessage**: Injects recommendations into Claude's context

## Configuration

Edit `config.py` to customize:

- `CONFIDENCE_THRESHOLD`: Minimum confidence to activate (default: 0.75)
- `CLAUDE_MODEL`: Model for classification
- `TEMPERATURE`: Temperature for deterministic results (0)

## Registry Files

### skill_conflicts.json

Define skills that shouldn't be activated together:

```json
{
  "conflicts": [
    {
      "skills": ["skill-a", "skill-b"],
      "reason": "Both serve similar purposes"
    }
  ]
}
```

### skill_dependencies.json

Define skill dependencies:

```json
{
  "dependencies": {
    "skill-a": ["dependency-1", "dependency-2"],
    "skill-b": []
  }
}
```

## Audit Logs

Logs are stored in `.audit/` with ISO 8601 timestamps:

```json
{
  "timestamp": "2026-02-11T10:32:21Z",
  "user_prompt": "Create a diagram",
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

## Troubleshooting

### No skills discovered

```bash
ls -la ../.claude/skills
find ../.claude/skills -name "SKILL.md"
```

### Hook not running

1. Check hook configuration in `../.claude/settings.local.json`
2. Verify script is executable: `ls -la hooks/user_prompt_submit.py`
3. Test manually: `echo '{"user_prompt": "test"}' | python hooks/user_prompt_submit.py`

### API errors

1. Verify API key: `echo $ANTHROPIC_API_KEY`
2. Check recent audit logs: `ls -lt .audit/ | head`
3. Review error messages in stderr

## Portability

The entire `.claude` directory is portable:

1. Copy `.claude/` to new project
2. Set `ANTHROPIC_API_KEY`
3. Install dependencies
4. Skills auto-discovered from `.claude/skills/`

## Development

The system is built with:
- **anthropic**: Claude API SDK
- **pydantic**: Data validation
- **httpx**: HTTP client (transitive dependency)

All components use Pydantic models for type safety and validation.

# Multi model integration

This repo exposes a single interface for OpenAI, Anthropic, Google Gemini, and Grok.

1. Copy `config/models.example.yaml` to `config/models.yaml`.
2. Add secrets in repo settings for the providers you use:
   - OPENAI_API_KEY
   - ANTHROPIC_API_KEY
   - GOOGLE_API_KEY
   - XAI_API_KEY
3. Probe locally:
   ```
   python scripts/llm_probe.py --provider openai --model gpt-4o-mini --prompt "Zero slop test."
   ```
4. Run a multi provider bench:
   ```
   python scripts/multi_bench.py --prompt "Compare providers for this task."
   ```

The router strips emojis, en dash, em dash, and nbsp by default.
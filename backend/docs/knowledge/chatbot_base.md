# Chatbot Base Quick Notes

## Provider pipeline

Every user message follows the same path.

```txt
React GUI
-> POST /api/chat
-> AgentCore
-> Memory + optional knowledge snippets
-> selected provider
-> assistant response
```

## Supported providers

- `mock`: local echo-style response for testing.
- `openai`: OpenAI-compatible Chat Completions.
- `gemini`: Google Gemini `generateContent`.
- `claude`: Anthropic Messages API.
- `ollama`: local Ollama `/api/chat`.
- `lmstudio`: LM Studio OpenAI-compatible local server.

## Security

API keys entered in the GUI are sent only with the current local request. They are not written to files or browser storage by this template.

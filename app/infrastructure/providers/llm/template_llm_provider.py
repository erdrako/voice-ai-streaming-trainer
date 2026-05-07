from collections.abc import AsyncIterator


class TemplateLanguageModelProvider:
    """
    Template implementation for a future LLM provider.

    Example future providers:
    - vLLM
    - OpenAI Responses API
    - Azure OpenAI
    - Anthropic
    - Google Gemini
    - An internal model gateway

    Implementation checklist:
    1. Convert the app's conversation format into the provider payload.
    2. Yield small text deltas from the provider stream.
    3. Hide provider-specific event formats inside this adapter.
    4. Register the provider in `composition/container.py`.

    This template is intentionally not wired at runtime.
    """

    async def stream_response(self, conversation: list[dict[str, str]]) -> AsyncIterator[str]:
        raise NotImplementedError("Template implementation for streamed LLM response.")
        yield ""  # Keeps this method typed as an async generator.

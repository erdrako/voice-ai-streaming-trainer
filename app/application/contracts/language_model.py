from collections.abc import AsyncIterator
from typing import Protocol


class LanguageModelProvider(Protocol):
    """
    Application contract for LLM providers.

    The use case only requires a stream of text deltas from a conversation. It
    does not care whether those deltas come from Ollama, vLLM, OpenAI, Azure,
    Google, Anthropic, or an internal inference service.

    Expansion point:
    - Add a provider under `app/infrastructure/providers/llm/`.
    - Keep this contract stable as long as the workflow still needs streamed
      text deltas.
    - Register the provider in the composition root to swap implementations.
    """

    async def stream_response(self, conversation: list[dict[str, str]]) -> AsyncIterator[str]:
        """Yield response text chunks for the given conversation history."""

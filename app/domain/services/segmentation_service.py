import re


class SegmentationService:
    """
    Domain service that decides when generated text is ready for TTS.

    The LLM streams tiny deltas. TTS works better when it receives phrases or
    sentences. This service bridges that mismatch without knowing anything
    about Piper, WebSockets, or Ollama.

    Expansion point:
    - Replace the regex strategy with NLP sentence segmentation.
    - Add language-specific behavior for Spanish/English punctuation.
    - Add max-length splitting for providers that reject long TTS requests.
    """

    def extract_ready_segments(self, buffer: str) -> tuple[list[str], str]:
        """
        Return complete speakable segments plus the incomplete remainder.

        Variables:
        - `buffer`: accumulated LLM text not yet sent to TTS.
        - `segments`: finished sentences/fragments that can be synthesized now.
        - `remainder`: text that should wait for more LLM deltas.
        """

        matches = list(re.finditer(r"[^.!?\n]+[.!?\n]+", buffer))
        if not matches:
            return [], buffer

        last_end = matches[-1].end()
        segments = [match.group(0).strip() for match in matches if match.group(0).strip()]
        return segments, buffer[last_end:]

    def has_speakable_text(self, text: str) -> bool:
        """
        Reject punctuation-only segments so TTS does not synthesize stray quotes.

        This is a tiny but practical example of a domain rule protecting an
        infrastructure provider from bad input.
        """

        return bool(re.search(r"[A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ]", text))

class AudioFormatService:
    """
    Domain service for audio-format decisions.

    This logic is not infrastructure because it does not call a provider. It is
    a small domain rule: given a MIME type from the browser, choose the suffix
    needed when creating a temp file for STT.

    Expansion point:
    - Add normalization rules here if browsers start sending other formats.
    - If conversion becomes necessary, delegate to an infrastructure audio
      transcoder provider instead of making this class call ffmpeg directly.
    """

    def suffix_for_mime_type(self, mime_type: str) -> str:
        """Return a safe file suffix for a browser-provided audio MIME type."""

        if "mp4" in mime_type:
            return ".mp4"
        if "mpeg" in mime_type or "mp3" in mime_type:
            return ".mp3"
        if "wav" in mime_type:
            return ".wav"
        return ".webm"

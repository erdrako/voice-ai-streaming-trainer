from app.domain.services.audio_format_service import AudioFormatService


def test_audio_suffix_detects_common_formats():
    service = AudioFormatService()

    assert service.suffix_for_mime_type("audio/wav") == ".wav"
    assert service.suffix_for_mime_type("audio/mp4") == ".mp4"
    assert service.suffix_for_mime_type("audio/mpeg") == ".mp3"
    assert service.suffix_for_mime_type("audio/webm;codecs=opus") == ".webm"

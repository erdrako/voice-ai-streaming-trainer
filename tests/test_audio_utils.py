from app.main import audio_suffix


def test_audio_suffix_detects_common_formats():
    assert audio_suffix("audio/wav") == ".wav"
    assert audio_suffix("audio/mp4") == ".mp4"
    assert audio_suffix("audio/mpeg") == ".mp3"
    assert audio_suffix("audio/webm;codecs=opus") == ".webm"


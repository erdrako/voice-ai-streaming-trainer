from app.session import VoiceSession


def test_voice_session_buffers_audio_and_resets_utterance():
    session = VoiceSession(session_id="s1")

    session.append_audio(b"abc")
    session.start_utterance("audio/wav")

    assert session.audio_buffer == bytearray()
    assert session.mime_type == "audio/wav"


def test_voice_session_tracks_conversation():
    session = VoiceSession(session_id="s1")

    session.add_user_text("hola")
    session.add_assistant_text("buenas")

    assert session.conversation == [
        {"role": "user", "content": "hola"},
        {"role": "assistant", "content": "buenas"},
    ]


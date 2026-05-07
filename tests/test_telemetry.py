from app.main import sanitize_payload


def test_sanitize_payload_replaces_audio_with_size():
    payload = sanitize_payload({"audio": "abcd", "segment": 1})

    assert payload == {"segment": 1, "audio_base64_chars": 4}

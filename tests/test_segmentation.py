from app.session import extract_ready_segments, has_speakable_text


def test_extract_ready_segments_returns_complete_sentences_and_remainder():
    segments, remainder = extract_ready_segments("Hola mundo. Esto sigue")

    assert segments == ["Hola mundo."]
    assert remainder == " Esto sigue"


def test_has_speakable_text_rejects_punctuation_only_segments():
    assert has_speakable_text("Hola")
    assert not has_speakable_text('"')

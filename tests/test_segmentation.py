from app.domain.services.segmentation_service import SegmentationService


def test_extract_ready_segments_returns_complete_sentences_and_remainder():
    service = SegmentationService()

    segments, remainder = service.extract_ready_segments("Hola mundo. Esto sigue")

    assert segments == ["Hola mundo."]
    assert remainder == " Esto sigue"


def test_has_speakable_text_rejects_punctuation_only_segments():
    service = SegmentationService()

    assert service.has_speakable_text("Hola")
    assert not service.has_speakable_text('"')

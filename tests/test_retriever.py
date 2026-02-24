from crawler.embedder import _build_perfume_text


def test_build_text_includes_sections():
    payload = {
        "brand": "Test",
        "name": "Sample",
        "year": 2024,
        "concentration": "EDP",
        "gender": "Unisex",
        "accords": [{"name": "Floral", "strength": 0.8}],
        "top_notes": ["Rose"],
        "middle_notes": ["Jasmine"],
        "base_notes": ["Amber"],
    }
    text = _build_perfume_text(payload)
    assert "Test Sample" in text
    assert "향 계열: Floral" in text
    assert "탑노트: Rose" in text

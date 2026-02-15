from inventorybot.entities import Item, Location
from inventorybot.telegram_text import (
    build_summary_for_caption,
    fit_text_to_limit,
    render_summary,
    truncate_preserving_words,
)


def make_item(description: str | None = "Descricao curta") -> Item:
    return Item(
        name="Item X",
        description=description,
        quantity=1,
        size="M",
        location=Location(name="Casa"),
        tags=["tag1", "tag2"],
    )


def test_truncate_preserving_words_respects_limit():
    text = "um texto muito longo"
    result = truncate_preserving_words(text, 10)
    assert len(result) <= 10
    assert result.endswith("...")


def test_fit_text_to_limit_fallback_truncation():
    text = "x" * 200

    def reducer(_text: str, _limit: int) -> str:
        raise RuntimeError("boom")

    result = fit_text_to_limit(text, 50, reducer)
    assert len(result) <= 50


def test_build_summary_for_caption_no_overflow():
    item = make_item("Descricao curta")
    full_summary = render_summary(item)
    caption, summary, was_shortened = build_summary_for_caption(item, 2000, None)
    assert caption == full_summary
    assert summary == full_summary
    assert not was_shortened


def test_build_summary_for_caption_overflow_uses_reducer():
    item = make_item("x" * 2000)
    called = {"value": False}

    def reducer(text: str, limit: int) -> str:
        called["value"] = True
        return "Nome curto\nDescricao curta"

    caption, summary, was_shortened = build_summary_for_caption(item, 200, reducer)
    assert called["value"]
    assert len(summary) > 200
    assert len(caption) <= 200
    assert "Nome curto" in caption
    assert "Descricao curta" in caption
    assert was_shortened

from __future__ import annotations

from typing import Callable

from inventorybot.entities import Item

try:
    from telegram.constants import MessageLimit

    CAPTION_LIMIT = MessageLimit.CAPTION_LENGTH
    TEXT_LIMIT = MessageLimit.MAX_TEXT_LENGTH
except Exception:
    # Fallback to documented Telegram limits
    CAPTION_LIMIT = 1024
    TEXT_LIMIT = 4096


TextReducer = Callable[[str, int], str]


def truncate_preserving_words(text: str, limit: int, suffix: str = "...") -> str:
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    if limit <= len(suffix):
        return suffix[:limit]

    max_len = limit - len(suffix)
    truncated = text[:max_len]

    cut = None
    for i in range(len(truncated) - 1, -1, -1):
        if truncated[i].isspace():
            cut = i
            break
    if cut is not None and cut > 0:
        truncated = truncated[:cut]

    return truncated.rstrip() + suffix


def fit_text_to_limit(
    text: str, limit: int, reducer: TextReducer | None = None
) -> str:
    if len(text) <= limit:
        return text

    if reducer is not None:
        try:
            reduced = (reducer(text, limit) or "").strip()
            if reduced:
                if len(reduced) > limit:
                    reduced = truncate_preserving_words(reduced, limit)
                return reduced
        except Exception:
            pass

    return truncate_preserving_words(text, limit)


def render_summary(
    item: Item,
    description_override: str | None = None,
    name_override: str | None = None,
) -> str:
    status_txt = item.status.value if item.status else "-"
    if description_override is None:
        description_txt = item.description or ""
    else:
        description_txt = description_override
    if name_override is None:
        name_txt = item.name
    else:
        name_txt = name_override

    return (
        "📦 **Item atual:**\n\n"
        f"🧾 Nome: {name_txt}\n"
        f"📝 Descrição: {description_txt}\n"
        f"📊 Quantidade: {item.quantity}\n"
        f"📏 Tamanho: {item.size}\n"
        f"📦 Localização: {item.location}\n"
        f"🏷️ Tags: {', '.join(item.tags) if item.tags else '*Nenhuma*'}\n"
        f"🔖 Status: {status_txt}"
    )


def _split_name_description(text: str) -> tuple[str, str]:
    if "\n" in text:
        name_part, desc_part = text.split("\n", 1)
        return name_part.strip(), desc_part.strip()
    return text.strip(), ""


def _shrink_name_description(
    name: str, description: str, available: int
) -> tuple[str, str]:
    if available <= 0:
        return "", ""
    if not description:
        return truncate_preserving_words(name, available), ""
    if not name:
        return "", truncate_preserving_words(description, available)

    total_len = len(name) + len(description)
    if total_len <= available:
        return name, description

    name_budget = max(1, round(available * len(name) / total_len))
    desc_budget = available - name_budget
    if desc_budget < 1:
        desc_budget = 1
        name_budget = max(0, available - desc_budget)

    new_name = truncate_preserving_words(name, name_budget)
    new_description = truncate_preserving_words(description, desc_budget)
    return new_name, new_description


def build_summary_for_caption(
    item: Item,
    caption_limit: int,
    reducer: TextReducer | None = None,
) -> tuple[str, str, bool]:
    full_summary = render_summary(item)
    if len(full_summary) <= caption_limit:
        return full_summary, full_summary, False

    name = item.name or ""
    description = item.description or ""
    summary_without_name_desc = render_summary(
        item, description_override="", name_override=""
    )
    available = caption_limit - len(summary_without_name_desc)

    if available <= 0:
        short_caption = truncate_preserving_words(full_summary, caption_limit)
        return short_caption, full_summary, True

    new_name = name
    new_description = description

    combined = f"{name}\n{description}" if description else name
    combined_limit = available + (1 if description else 0)
    reduced = None
    if reducer is not None and combined:
        try:
            reduced = (reducer(combined, combined_limit) or "").strip()
        except Exception:
            reduced = None

    if reduced:
        if "\n" in reduced:
            new_name, new_description = _split_name_description(reduced)
        elif description:
            reduced = None
        else:
            new_name = reduced

    if reduced is None:
        new_name, new_description = _shrink_name_description(
            name, description, available
        )

    caption = render_summary(
        item, description_override=new_description, name_override=new_name
    )
    if len(caption) > caption_limit:
        caption = truncate_preserving_words(caption, caption_limit)

    was_shortened = len(caption) < len(full_summary)
    return caption, full_summary, was_shortened

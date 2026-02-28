from __future__ import annotations


def is_cancel_action(text: str | None) -> bool:
    if not text:
        return False

    normalized_text = text.strip().casefold()
    return normalized_text.endswith("cancel") or "скасувати" in normalized_text


def is_unavailable_chat_error(error: Exception) -> bool:
    error_text = str(error).casefold()
    return any(
        marker in error_text
        for marker in (
            "blocked",
            "chat not found",
            "user is deactivated",
            "forbidden",
            "bot was blocked by the user",
        )
    )


def format_joke_text(joke_text: str, tags: str | None) -> str:
    if not tags:
        return joke_text

    return f"{joke_text}\n\n#{tags.replace(', ', ' #')}"

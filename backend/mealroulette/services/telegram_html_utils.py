from __future__ import annotations

import html
import re

from mealroulette.services.telegram_format import TELEGRAM_MESSAGE_LIMIT


def esc(text: str, *, quote: bool = False) -> str:
    return html.escape(text, quote=quote)


def close_unclosed_html_tags(text: str) -> str:
    open_tags: list[str] = []
    for match in re.finditer(r"<(/?)(b|i|blockquote)\b[^>]*>", text, re.IGNORECASE):
        closing, tag = match.groups()
        tag = tag.lower()
        if closing:
            if open_tags and open_tags[-1] == tag:
                open_tags.pop()
        else:
            open_tags.append(tag)
    return text + "".join(f"</{tag}>" for tag in reversed(open_tags))


def truncate_message(message: str) -> str:
    suffix = "\n\n… (message truncated)"
    max_len = TELEGRAM_MESSAGE_LIMIT - len(suffix)
    if len(message) <= max_len:
        return message

    cut = message[:max_len]
    last_newline = cut.rfind("\n")
    if last_newline > max_len * 0.5:
        cut = cut[:last_newline]

    last_lt = cut.rfind("<")
    last_gt = cut.rfind(">")
    if last_lt > last_gt:
        cut = cut[:last_lt].rstrip()

    return close_unclosed_html_tags(cut.rstrip()) + suffix

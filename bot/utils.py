import re


_MARKDOWN_SPECIAL_CHARS = r"_*[]()~`>#+-=|{}.!"


def normalize_slug(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9а-яА-ЯёЁ\s-]+", "", value or "")
    clean = clean.strip().lower().replace(" ", "-")
    clean = re.sub(r"-+", "-", clean)
    clean = clean.strip("-")
    return clean or "course"


def escape_markdown_v2(text: str) -> str:
    return re.sub(r"([\\_\*\[\]\(\)~`>#+\-=|{}.!])", r"\\\1", text or "")

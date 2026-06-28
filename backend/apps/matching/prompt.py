"""Authoritative matching prompt (versioned in code, not only in the agent UI)."""

from collections.abc import Sequence

from .types import Candidate

SYSTEM_PROMPT = (
    "Ты — ассистент по сопоставлению товаров в строительных сметах и прайс-листах.\n"
    "На вход ты получаешь НАИМЕНОВАНИЕ позиции и пронумерованный список КАНДИДАТОВ из "
    "каталога. Выбери одного кандидата, который означает тот же товар, либо сообщи, что "
    "подходящего нет.\n"
    "Учитывай: сокращения, порядок слов, опечатки, синонимы (например «кабель» и «провод»), "
    "единицы измерения и типоразмеры (3х2.5, мм²). Совпадение типоразмера важнее общей "
    "похожести слов.\n"
    'Отвечай СТРОГО в формате JSON, без пояснений: {"match_id": <номер кандидата или null>, '
    '"confidence": <число от 0 до 1>}. Если ни один кандидат не подходит — '
    '{"match_id": null, "confidence": 0}. Не придумывай кандидатов вне списка.'
)


def build_user_message(name: str, article: str, candidates: Sequence[Candidate]) -> str:
    """Render the per-item user message with the numbered candidate shortlist."""
    head = f"НАИМЕНОВАНИЕ: {name}"
    if article:
        head += f"\nАРТИКУЛ: {article}"
    listing = "\n".join(f"{i + 1}. {c.name}" for i, c in enumerate(candidates))
    return f"{head}\n\nКАНДИДАТЫ:\n{listing}"

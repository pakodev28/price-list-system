"""Offline evaluation of the matching pipeline.

Builds a small labeled logistics dataset in memory, runs the production matcher
over it, and reports retrieval recall@k and end-to-end accuracy. This is what
lets us tune thresholds and embeddings against numbers instead of guessing.

Run it with ``manage.py eval_matching`` (uses the embedding model for the
semantic signal); the metric logic is unit-tested in lexical-only mode.

``CATALOG`` is the canonical ``(name, group)`` universe; ``CASES`` are noisy
supplier/estimate-style queries (abbreviations, reordered words, dropped codes)
plus one unrelated row that must resolve to "no match".
"""

from dataclasses import dataclass

from django.conf import settings

from apps.catalog.normalization import normalize_name

from .embeddings import embed_texts
from .semantic import retrieve
from .service import MatchingService
from .types import Candidate

CATALOG: list[tuple[str, str]] = [
    ("Морской фрахт Шанхай–Владивосток, 40HC", "Морской фрахт"),
    ("Морской фрахт Нинбо–Восточный, 20DC", "Морской фрахт"),
    ("Авиаперевозка Гуанчжоу–Москва, 100–300 кг", "Авиаперевозки"),
    ("Ж/д перевозка Чунцин–Москва, 40HC", "Ж/д перевозки"),
    ("Автодоставка Владивосток–Москва, тент 20т", "Автодоставка по РФ"),
    ("Таможенная пошлина: электроника", "Таможенные платежи"),
    ("НДС 20%", "Таможенные платежи"),
    ("Услуги таможенного брокера (1 ДТ)", "Таможенное оформление"),
    ("Подбор кода ТН ВЭД", "Таможенное оформление"),
    ("Сертификат соответствия ТР ТС (электроника)", "Сертификация"),
    ("Хранение на СВХ (1 сутки)", "Склад и СВХ"),
    ("Страхование груза (0.2% от стоимости)", "Страхование"),
    ("Смартфон (ТН ВЭД 8517130000)", "Товары (импорт)"),
]


@dataclass(frozen=True)
class EvalCase:
    """A noisy query paired with its expected catalog name (``None`` = no match)."""

    query: str
    gold: str | None
    article: str = ""


CASES: list[EvalCase] = [
    EvalCase("Мор. фрахт Шанхай-Владивосток 40HC", "Морской фрахт Шанхай–Владивосток, 40HC"),
    EvalCase("морской фрахт нинбо восточный 20DC", "Морской фрахт Нинбо–Восточный, 20DC"),
    EvalCase("Авиа Гуанчжоу Москва 100-300 кг", "Авиаперевозка Гуанчжоу–Москва, 100–300 кг"),
    EvalCase("ЖД Чунцин Москва 40HC", "Ж/д перевозка Чунцин–Москва, 40HC"),
    EvalCase("Авто Владивосток Москва тент 20т", "Автодоставка Владивосток–Москва, тент 20т"),
    EvalCase("Пошлина электроника", "Таможенная пошлина: электроника"),
    EvalCase("НДС 20", "НДС 20%"),
    EvalCase("брокер 1 ДТ", "Услуги таможенного брокера (1 ДТ)"),
    EvalCase("Подбор кода ТН ВЭД", "Подбор кода ТН ВЭД"),
    EvalCase("Сертификат ТР ТС электроника", "Сертификат соответствия ТР ТС (электроника)"),
    EvalCase("Хран. СВХ 1 сутки", "Хранение на СВХ (1 сутки)"),
    EvalCase("страхование груза 0.2%", "Страхование груза (0.2% от стоимости)"),
    EvalCase("Смартфон", "Смартфон (ТН ВЭД 8517130000)"),
    EvalCase("Представительские расходы", None),
]


@dataclass(frozen=True)
class CaseResult:
    case: EvalCase
    predicted: str | None
    in_shortlist: bool
    source: str
    score: float


@dataclass(frozen=True)
class EvalReport:
    results: list[CaseResult]
    k: int

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def recall_at_k(self) -> float:
        """Share of gold-bearing cases whose answer was in the retrieval shortlist."""
        golds = [r for r in self.results if r.case.gold is not None]
        return sum(r.in_shortlist for r in golds) / len(golds) if golds else 1.0

    @property
    def accuracy(self) -> float:
        """Share of cases whose final prediction equals the gold (``None`` included)."""
        if not self.results:
            return 1.0
        return sum(r.predicted == r.case.gold for r in self.results) / len(self.results)


def _candidates(embed: bool) -> list[Candidate]:
    group_ids = {name: i + 1 for i, name in enumerate(sorted({g for _n, g in CATALOG}))}
    vectors = (
        embed_texts([normalize_name(name) for name, _g in CATALOG])
        if embed
        else [None] * len(CATALOG)
    )
    return [
        Candidate(id=i, article="", name=name, group_id=group_ids[group], vector=vectors[i])
        for i, (name, group) in enumerate(CATALOG)
    ]


def run_eval(*, embed: bool = True, use_llm: bool = False, k: int | None = None) -> EvalReport:
    """Run the full matcher over the labeled set and collect per-case metrics."""
    k = k or settings.MATCH_SHORTLIST_SIZE
    candidates = _candidates(embed)
    name_by_id = {c.id: c.name for c in candidates}
    service = MatchingService(use_llm=use_llm)

    results: list[CaseResult] = []
    for case in CASES:
        shortlist = {name_by_id[c.id] for c, _score in retrieve(case.query, candidates, k)}
        outcome = service.match(case.query, case.article, candidates)
        predicted = name_by_id.get(outcome.product_id) if outcome.product_id is not None else None
        results.append(
            CaseResult(
                case=case,
                predicted=predicted,
                in_shortlist=case.gold in shortlist if case.gold is not None else True,
                source=outcome.source,
                score=round(outcome.confidence, 3),
            )
        )
    return EvalReport(results=results, k=k)

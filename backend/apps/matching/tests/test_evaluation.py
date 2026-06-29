"""Evaluation harness — exercised in lexical-only mode (no embedding model)."""

from apps.matching.evaluation import CASES, run_eval


def test_eval_runs_lexically_and_reports_sane_metrics() -> None:
    report = run_eval(embed=False, use_llm=False)

    assert report.total == len(CASES)
    assert 0.0 <= report.recall_at_k <= 1.0
    assert 0.0 <= report.accuracy <= 1.0


def test_lexical_recall_is_high_thanks_to_synonyms() -> None:
    """With abbreviation expansion, pure lexical retrieval surfaces most gold answers."""
    report = run_eval(embed=False, use_llm=False)

    assert report.recall_at_k >= 0.7

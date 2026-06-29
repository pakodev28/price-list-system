"""Report matching quality on the labeled evaluation set."""

from typing import Any

from django.core.management.base import BaseCommand

from apps.matching.evaluation import run_eval


class Command(BaseCommand):
    help = "Evaluate the matching pipeline on a labeled logistics set (recall@k, accuracy)."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--no-embed", action="store_true", help="Lexical only — skip the embedding model."
        )
        parser.add_argument("--llm", action="store_true", help="Enable the LLM rerank stage.")

    def handle(self, *args: Any, **options: Any) -> None:
        report = run_eval(embed=not options["no_embed"], use_llm=options["llm"])
        for result in report.results:
            ok = result.predicted == result.case.gold
            mark = self.style.SUCCESS("OK ") if ok else self.style.ERROR("MISS")
            self.stdout.write(
                f"{mark} [{result.source:>9} {result.score:.2f}] "
                f"{result.case.query}  ->  {result.predicted or 'нет соответствия'}"
            )
        self.stdout.write("")
        self.stdout.write(
            self.style.NOTICE(
                f"recall@{report.k}: {report.recall_at_k:.0%}   "
                f"accuracy: {report.accuracy:.0%}   ({report.total} кейсов)"
            )
        )

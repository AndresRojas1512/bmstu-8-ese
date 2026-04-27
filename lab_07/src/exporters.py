from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if __package__ in {None, ""}:
    from cocomo2 import ApplicationCompositionProject, ApplicationCompositionResult, FunctionPointProject, FunctionPointResult
else:
    from .cocomo2 import (
        ApplicationCompositionProject,
        ApplicationCompositionResult,
        FunctionPointProject,
        FunctionPointResult,
    )

if TYPE_CHECKING:
    if __package__ in {None, ""}:
        from main import EarlyDesignPayload
    else:
        from .main import EarlyDesignPayload


@dataclass(frozen=True, slots=True)
class ExportedFile:
    label: str
    path: Path


class CsvExportService:
    def export_function_points(
        self,
        directory: str,
        project: FunctionPointProject,
        result: FunctionPointResult,
        stem: str,
    ) -> tuple[ExportedFile, ...]:
        target_dir = Path(directory)
        target_dir.mkdir(parents=True, exist_ok=True)

        summary_path = target_dir / f"{stem}_summary.csv"
        components_path = target_dir / f"{stem}_components.csv"
        characteristics_path = target_dir / f"{stem}_characteristics.csv"

        self._write_csv(
            summary_path,
            ["Metric", "Value"],
            [
                ("Components", str(len(project.components))),
                ("UFP", f"{result.unadjusted_points:.2f}"),
                ("Characteristics sum", str(result.total_characteristics)),
                ("VAF", f"{result.value_adjustment_factor:.2f}"),
                ("Adjusted FP", f"{result.adjusted_points:.2f}"),
            ],
        )
        self._write_csv(
            components_path,
            ["Name", "Type", "DET", "References", "Complexity", "Weight", "Notes"],
            [
                (
                    item.component.name,
                    item.component.component_type.name,
                    str(item.component.det_count),
                    str(item.component.reference_count),
                    item.complexity.label,
                    str(item.weight),
                    item.component.notes,
                )
                for item in result.rated_components
            ],
        )
        self._write_csv(
            characteristics_path,
            ["Id", "Name", "Value"],
            [
                (
                    str(item.definition.identifier),
                    item.definition.name,
                    str(item.value),
                )
                for item in project.characteristics
            ],
        )
        return (
            ExportedFile("summary", summary_path),
            ExportedFile("components", components_path),
            ExportedFile("characteristics", characteristics_path),
        )

    def export_application_composition(
        self,
        directory: str,
        project: ApplicationCompositionProject,
        result: ApplicationCompositionResult,
        stem: str,
    ) -> tuple[ExportedFile, ...]:
        target_dir = Path(directory)
        target_dir.mkdir(parents=True, exist_ok=True)

        summary_path = target_dir / f"{stem}_summary.csv"
        items_path = target_dir / f"{stem}_items.csv"

        self._write_csv(
            summary_path,
            ["Metric", "Value"],
            [
                ("Items", str(len(project.items))),
                ("Reuse %", f"{project.reuse_percent:.2f}"),
                ("PROD", f"{project.productivity_level.productivity:.2f}"),
                ("Object Points", f"{result.object_points:.2f}"),
                ("NOP", f"{result.new_object_points:.2f}"),
                ("Exponent p", f"{result.exponent:.4f}"),
                ("Effort PM", f"{result.effort_person_months:.2f}"),
                ("TDEV", f"{result.time_months:.2f}"),
                ("Average team", f"{result.average_team_size:.2f}"),
                ("Budget", "" if result.budget is None else f"{result.budget:.2f}"),
            ],
        )
        self._write_csv(
            items_path,
            ["Name", "Kind", "Complexity", "Weight", "Count", "Points", "Notes"],
            [
                (
                    item.item.name,
                    item.item.kind.label,
                    "-" if item.item.complexity is None else item.item.complexity.label,
                    str(item.weight),
                    str(item.item.count),
                    str(item.points),
                    item.item.notes,
                )
                for item in result.rated_items
            ],
        )
        return (
            ExportedFile("summary", summary_path),
            ExportedFile("items", items_path),
        )

    def export_early_design(
        self,
        directory: str,
        payload: "EarlyDesignPayload",
        stem: str,
    ) -> tuple[ExportedFile, ...]:
        target_dir = Path(directory)
        target_dir.mkdir(parents=True, exist_ok=True)

        summary_path = target_dir / f"{stem}_summary.csv"
        languages_path = target_dir / f"{stem}_languages.csv"
        factors_path = target_dir / f"{stem}_factors.csv"

        summary_rows = [
            ("Function Points", f"{payload.function_point_result.adjusted_points:.2f}"),
            ("Known share %", f"{payload.backfiring_result.known_share_percent:.2f}"),
            ("Partial KLOC", f"{payload.backfiring_result.partial_kloc_from_known_share:.3f}"),
            (
                "Estimated KLOC",
                "" if payload.backfiring_result.estimated_kloc is None else f"{payload.backfiring_result.estimated_kloc:.3f}",
            ),
        ]
        if payload.early_design_result is not None:
            summary_rows.extend(
                [
                    ("Exponent p", f"{payload.early_design_result.exponent:.4f}"),
                    ("EArch", f"{payload.early_design_result.effort_adjustment_factor:.4f}"),
                    ("PM", f"{payload.early_design_result.effort_person_months:.2f}"),
                    ("TDEV", f"{payload.early_design_result.time_months:.2f}"),
                    ("Average team", f"{payload.early_design_result.average_team_size:.2f}"),
                    (
                        "Budget",
                        "" if payload.early_design_result.budget is None else f"{payload.early_design_result.budget:.2f}",
                    ),
                ]
            )
        self._write_csv(summary_path, ["Metric", "Value"], summary_rows)

        self._write_csv(
            languages_path,
            ["Language", "Share %", "LOC/FP"],
            [
                (
                    item.language,
                    f"{item.percentage:.2f}",
                    "" if item.loc_per_fp is None else f"{item.loc_per_fp:.2f}",
                )
                for item in payload.backfiring_project.language_mix
            ],
        )

        factor_rows = []
        if payload.early_design_project is not None:
            for identifier, rating in payload.early_design_project.scale_factor_ratings.items():
                factor_rows.append(("Scale", identifier, rating.label))
            for identifier, rating in payload.early_design_project.effort_multiplier_ratings.items():
                factor_rows.append(("Multiplier", identifier, rating.label))
        self._write_csv(factors_path, ["Group", "Id", "Rating"], factor_rows)

        return (
            ExportedFile("summary", summary_path),
            ExportedFile("languages", languages_path),
            ExportedFile("factors", factors_path),
        )

    @staticmethod
    def _write_csv(path: Path, header, rows) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(rows)

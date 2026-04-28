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
            ["Показатель", "Значение"],
            [
                ("Количество компонентов", str(len(project.components))),
                ("UFP", f"{result.unadjusted_points:.2f}"),
                ("Сумма системных характеристик", str(result.total_characteristics)),
                ("VAF", f"{result.value_adjustment_factor:.2f}"),
                ("Скорректированные функциональные точки", f"{result.adjusted_points:.2f}"),
            ],
        )
        self._write_csv(
            components_path,
            ["Название", "Тип", "DET", "Ссылки", "Сложность", "Вес", "Примечание"],
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
            ["Идентификатор", "Название", "Значение"],
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
            ["Показатель", "Значение"],
            [
                ("Количество элементов", str(len(project.items))),
                ("Повторное использование, %", f"{project.reuse_percent:.2f}"),
                ("Продуктивность (PROD)", f"{project.productivity_level.productivity:.2f}"),
                ("Объектные точки", f"{result.object_points:.2f}"),
                ("NOP", f"{result.new_object_points:.2f}"),
                ("Показатель степени p", f"{result.exponent:.4f}"),
                ("Трудоемкость, PM", f"{result.effort_person_months:.2f}"),
                ("TDEV", f"{result.time_months:.2f}"),
                ("Средний размер команды", f"{result.average_team_size:.2f}"),
                ("Бюджет", "" if result.budget is None else f"{result.budget:.2f}"),
            ],
        )
        self._write_csv(
            items_path,
            ["Название", "Вид", "Сложность", "Вес", "Количество", "Точки", "Примечание"],
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
            ("Функциональные точки", f"{payload.function_point_result.adjusted_points:.2f}"),
            ("Покрытая доля пересчета, %", f"{payload.size_conversion_result.known_share_percent:.2f}"),
            ("Частичный KLOC", f"{payload.size_conversion_result.partial_kloc_from_known_share:.3f}"),
            (
                "Оцененный KLOC",
                "" if payload.size_conversion_result.estimated_kloc is None else f"{payload.size_conversion_result.estimated_kloc:.3f}",
            ),
        ]
        if payload.early_design_result is not None:
            summary_rows.extend(
                [
                    ("Показатель степени p", f"{payload.early_design_result.exponent:.4f}"),
                    ("EArch", f"{payload.early_design_result.effort_coefficient_product:.4f}"),
                    ("PM", f"{payload.early_design_result.effort_person_months:.2f}"),
                    ("TDEV", f"{payload.early_design_result.time_months:.2f}"),
                    ("Средний размер команды", f"{payload.early_design_result.average_team_size:.2f}"),
                    (
                        "Бюджет",
                        "" if payload.early_design_result.budget is None else f"{payload.early_design_result.budget:.2f}",
                    ),
                ]
            )
        self._write_csv(summary_path, ["Показатель", "Значение"], summary_rows)

        self._write_csv(
            languages_path,
            ["Язык", "Доля, %", "LOC/FP"],
            [
                (
                    item.language,
                    f"{item.percentage:.2f}",
                    "" if item.loc_per_fp is None else f"{item.loc_per_fp:.2f}",
                )
                for item in payload.size_conversion_project.language_mix
            ],
        )

        factor_rows = []
        if payload.early_design_project is not None:
            for identifier, rating in payload.early_design_project.exponent_factor_ratings.items():
                factor_rows.append(("Показатель степени", identifier, rating.label))
            for identifier, rating in payload.early_design_project.effort_coefficient_ratings.items():
                factor_rows.append(("Коэффициент трудоемкости", identifier, rating.label))
        self._write_csv(factors_path, ["Группа", "Идентификатор", "Уровень"], factor_rows)

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

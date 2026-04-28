from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LanguageFootprint:
    language: str
    percentage: float
    loc_per_fp: float | None


@dataclass(frozen=True, slots=True)
class SizeConversionProject:
    language_mix: tuple[LanguageFootprint, ...]


@dataclass(frozen=True, slots=True)
class SizeConversionResult:
    function_points: float
    known_share_percent: float
    partial_kloc_from_known_share: float
    weighted_loc_per_fp: float | None
    estimated_kloc: float | None


class FunctionPointConversionService:
    def estimate(self, function_points: float, project: SizeConversionProject) -> SizeConversionResult:
        self._validate(function_points, project)

        known_share_percent = 0.0
        weighted_sum = 0.0
        for item in project.language_mix:
            if item.loc_per_fp is None:
                continue
            known_share_percent += item.percentage
            weighted_sum += item.percentage * item.loc_per_fp

        partial_kloc = function_points * weighted_sum / 100000.0
        weighted_loc_per_fp = weighted_sum / 100.0 if known_share_percent == 100.0 else None
        estimated_kloc = function_points * weighted_loc_per_fp / 1000.0 if weighted_loc_per_fp is not None else None

        return SizeConversionResult(
            function_points=function_points,
            known_share_percent=known_share_percent,
            partial_kloc_from_known_share=partial_kloc,
            weighted_loc_per_fp=weighted_loc_per_fp,
            estimated_kloc=estimated_kloc,
        )

    @staticmethod
    def _validate(function_points: float, project: SizeConversionProject) -> None:
        if function_points <= 0:
            raise ValueError("Количество функциональных точек должно быть положительным.")
        if not project.language_mix:
            raise ValueError("Нужно указать хотя бы один язык в языковой смеси.")

        total_share = 0.0
        for item in project.language_mix:
            if item.percentage <= 0:
                raise ValueError(f"Доля языка '{item.language}' должна быть положительной.")
            if item.loc_per_fp is not None and item.loc_per_fp <= 0:
                raise ValueError(f"Коэффициент LOC/FP для языка '{item.language}' должен быть положительным.")
            total_share += item.percentage

        if abs(total_share - 100.0) > 1e-9:
            raise ValueError("Сумма долей языковой смеси должна составлять 100 %.")

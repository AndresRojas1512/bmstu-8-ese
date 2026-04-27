from __future__ import annotations

import math
from dataclasses import dataclass

from .model import ProjectEstimate


@dataclass(frozen=True, slots=True)
class PhaseAllocation:
    name: str
    effort_percent: float
    duration_percent: float
    effort_pm: float
    duration_months: float
    average_staffing: float


@dataclass(frozen=True, slots=True)
class WBSAllocation:
    name: str
    effort_percent: float
    effort_pm: float


@dataclass(frozen=True, slots=True)
class StaffingSegment:
    phase_name: str
    start_month: float
    end_month: float
    duration_months: float
    effort_pm: float
    average_staffing: float
    recommended_headcount: int


@dataclass(frozen=True, slots=True)
class StaffingPoint:
    month: int
    headcount: int
    phase_name: str


@dataclass(frozen=True, slots=True)
class DistributionBundle:
    total_effort_pm: float
    total_time_months: float
    phases: tuple[PhaseAllocation, ...]
    wbs_items: tuple[WBSAllocation, ...]
    staffing_segments: tuple[StaffingSegment, ...]
    staffing_points: tuple[StaffingPoint, ...]
    staffing_strategy_note: str


class DistributionService:
    _PLANNING_EFFORT_PERCENT = 8.0
    _PLANNING_TIME_PERCENT = 36.0

    _DEVELOPMENT_PHASES: tuple[tuple[str, float, float], ...] = (
        ("Проектирование продукта", 18.0, 36.0),
        ("Детальное проектирование", 25.0, 18.0),
        ("Кодирование и модульное тестирование", 26.0, 18.0),
        ("Интеграция и тестирование", 31.0, 28.0),
    )

    _WBS_DISTRIBUTION: tuple[tuple[str, float], ...] = (
        ("Анализ требований", 4.0),
        ("Проектирование продукта", 12.0),
        ("Программирование", 44.0),
        ("Планирование тестирования", 6.0),
        ("Верификация и аттестация", 14.0),
        ("Канцелярия проекта", 7.0),
        ("Управление конфигурацией и обеспечение качества", 7.0),
        ("Создание документации", 6.0),
    )

    def build(self, estimate: ProjectEstimate) -> DistributionBundle:
        total_effort_pm = estimate.development_effort_pm * (1.0 + self._PLANNING_EFFORT_PERCENT / 100.0)
        total_time_months = estimate.development_time_months * (1.0 + self._PLANNING_TIME_PERCENT / 100.0)

        planning_effort_pm = estimate.development_effort_pm * self._PLANNING_EFFORT_PERCENT / 100.0
        planning_time_months = estimate.development_time_months * self._PLANNING_TIME_PERCENT / 100.0

        phases: list[PhaseAllocation] = [
            PhaseAllocation(
                name="Планирование и анализ требований",
                effort_percent=self._PLANNING_EFFORT_PERCENT,
                duration_percent=self._PLANNING_TIME_PERCENT,
                effort_pm=planning_effort_pm,
                duration_months=planning_time_months,
                average_staffing=self._safe_staffing(planning_effort_pm, planning_time_months),
            )
        ]

        for name, effort_percent, duration_percent in self._DEVELOPMENT_PHASES:
            phase_effort_pm = estimate.development_effort_pm * effort_percent / 100.0
            phase_time_months = estimate.development_time_months * duration_percent / 100.0
            phases.append(
                PhaseAllocation(
                    name=name,
                    effort_percent=effort_percent,
                    duration_percent=duration_percent,
                    effort_pm=phase_effort_pm,
                    duration_months=phase_time_months,
                    average_staffing=self._safe_staffing(phase_effort_pm, phase_time_months),
                )
            )

        wbs_items = tuple(
            WBSAllocation(
                name=name,
                effort_percent=effort_percent,
                effort_pm=total_effort_pm * effort_percent / 100.0,
            )
            for name, effort_percent in self._WBS_DISTRIBUTION
        )

        staffing_segments, staffing_points, staffing_strategy_note = self._build_staffing_plan(
            phases=tuple(phases),
            total_effort_pm=total_effort_pm,
            total_time_months=total_time_months,
        )

        return DistributionBundle(
            total_effort_pm=total_effort_pm,
            total_time_months=total_time_months,
            phases=tuple(phases),
            wbs_items=wbs_items,
            staffing_segments=staffing_segments,
            staffing_points=staffing_points,
            staffing_strategy_note=staffing_strategy_note,
        )

    @staticmethod
    def _safe_staffing(effort_pm: float, duration_months: float) -> float:
        if duration_months == 0:
            return 0.0
        return effort_pm / duration_months

    def _build_staffing_plan(
        self,
        phases: tuple[PhaseAllocation, ...],
        total_effort_pm: float,
        total_time_months: float,
    ) -> tuple[tuple[StaffingSegment, ...], tuple[StaffingPoint, ...], str]:
        average_team_size = self._safe_staffing(total_effort_pm, total_time_months)
        minimum_core_team = 1 if average_team_size < 2.0 else 2

        segments: list[StaffingSegment] = []
        current_month = 0.0
        previous_headcount: int | None = None

        for index, phase in enumerate(phases):
            if index == 0:
                target = max(
                    minimum_core_team,
                    round(max(phase.average_staffing, average_team_size * 0.35)),
                )
            else:
                target = max(minimum_core_team, round(phase.average_staffing))

            if previous_headcount is not None and index == len(phases) - 1:
                target = min(target, max(minimum_core_team, round(previous_headcount * 0.85)))

            if previous_headcount is None:
                recommended_headcount = target
            else:
                max_change = max(1, math.ceil(previous_headcount * 0.5))
                lower_bound = max(minimum_core_team, previous_headcount - max_change)
                upper_bound = previous_headcount + max_change
                recommended_headcount = max(lower_bound, min(target, upper_bound))

            start_month = current_month
            end_month = current_month + phase.duration_months
            segments.append(
                StaffingSegment(
                    phase_name=phase.name,
                    start_month=start_month,
                    end_month=end_month,
                    duration_months=phase.duration_months,
                    effort_pm=phase.effort_pm,
                    average_staffing=phase.average_staffing,
                    recommended_headcount=recommended_headcount,
                )
            )
            current_month = end_month
            previous_headcount = recommended_headcount

        staffing_points: list[StaffingPoint] = []
        for month in range(1, math.ceil(total_time_months) + 1):
            month_marker = month - 0.5
            active_segment = next(
                (
                    segment
                    for segment in segments
                    if segment.start_month <= month_marker < segment.end_month
                ),
                segments[-1],
            )
            staffing_points.append(
                StaffingPoint(
                    month=month,
                    headcount=active_segment.recommended_headcount,
                    phase_name=active_segment.phase_name,
                )
            )

        note = (
            "Рекомендуемый план комплектования использует целочисленную численность команды, "
            "опирается на среднюю нагрузку по фазам, сохраняет минимальное ядро команды, "
            "ограничивает резкие изменения численности и начинает снижение состава "
            "на финальной стадии интеграции."
        )
        return tuple(segments), tuple(staffing_points), note

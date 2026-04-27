from __future__ import annotations

from dataclasses import dataclass

from .drivers import COST_DRIVER_MAP, default_driver_ratings
from .enums import ProjectMode, Rating
from .model import COCOMOCalculator, ProjectEstimate, ProjectProfile


@dataclass(frozen=True, slots=True)
class SweepRow:
    driver_id: str
    driver_title: str
    rating: Rating
    eaf: float
    effort_pm: float
    time_months: float


@dataclass(frozen=True, slots=True)
class DriverSweep:
    driver_id: str
    driver_title: str
    rows: tuple[SweepRow, ...]
    effort_delta_pm: float
    effort_delta_percent: float
    time_delta_months: float
    time_delta_percent: float


@dataclass(frozen=True, slots=True)
class Variant3AnalysisResult:
    kloc: float
    nominal_sced: Rating
    comparison_sced: Rating
    nominal_sweeps: tuple[DriverSweep, ...]
    comparison_sweeps: tuple[DriverSweep, ...]
    top_effort_driver_nominal: str
    top_time_driver_nominal: str
    top_effort_driver_comparison: str
    top_time_driver_comparison: str


@dataclass(frozen=True, slots=True)
class Variant3CasePreset:
    profile: ProjectProfile
    note: str


class Variant3AnalysisService:
    _TARGET_DRIVERS: tuple[str, ...] = ("RELY", "DATA", "CPLX")

    def __init__(self, calculator: COCOMOCalculator) -> None:
        self._calculator = calculator

    def analyze(
        self,
        kloc: float,
        nominal_sced: Rating = Rating.NOMINAL,
        comparison_sced: Rating = Rating.VERY_LOW,
    ) -> Variant3AnalysisResult:
        nominal_sweeps = self._build_sweeps(kloc=kloc, sced=nominal_sced)
        comparison_sweeps = self._build_sweeps(kloc=kloc, sced=comparison_sced)
        return Variant3AnalysisResult(
            kloc=kloc,
            nominal_sced=nominal_sced,
            comparison_sced=comparison_sced,
            nominal_sweeps=nominal_sweeps,
            comparison_sweeps=comparison_sweeps,
            top_effort_driver_nominal=self._max_spread_driver(nominal_sweeps, key="effort"),
            top_time_driver_nominal=self._max_spread_driver(nominal_sweeps, key="time"),
            top_effort_driver_comparison=self._max_spread_driver(comparison_sweeps, key="effort"),
            top_time_driver_comparison=self._max_spread_driver(comparison_sweeps, key="time"),
        )

    def build_variant3_case_preset(
        self,
        cost_per_person_month: float | None = None,
    ) -> Variant3CasePreset:
        ratings = default_driver_ratings()
        ratings.update(
            {
                "ACAP": Rating.VERY_HIGH,
                "PCAP": Rating.VERY_HIGH,
                "AEXP": Rating.HIGH,
                "LEXP": Rating.HIGH,
                "RELY": Rating.HIGH,
                "TIME": Rating.VERY_HIGH,
                "SCED": Rating.VERY_LOW,
            }
        )
        profile = ProjectProfile(
            mode=ProjectMode.EMBEDDED,
            kloc=230.0,
            driver_ratings=ratings,
            cost_per_person_month=cost_per_person_month,
        )
        note = (
            "Базовый сценарий для программного компонента системы управления воздушным движением. "
            "Формулировка про жесткие ограничения времени выполнения интерпретируется как "
            "TIME = Очень высокий, а жесткие ограничения по срокам разработки как "
            "SCED = Очень низкий."
        )
        return Variant3CasePreset(profile=profile, note=note)

    def _build_sweeps(self, kloc: float, sced: Rating) -> tuple[DriverSweep, ...]:
        sweeps: list[DriverSweep] = []
        for driver_id in self._TARGET_DRIVERS:
            definition = COST_DRIVER_MAP[driver_id]
            rows: list[SweepRow] = []
            for rating in definition.ratings:
                ratings = default_driver_ratings()
                ratings["SCED"] = sced
                ratings[driver_id] = rating
                estimate = self._calculator.estimate(
                    ProjectProfile(
                        mode=ProjectMode.SEMIDETACHED,
                        kloc=kloc,
                        driver_ratings=ratings,
                    )
                )
                rows.append(
                    SweepRow(
                        driver_id=driver_id,
                        driver_title=definition.title,
                        rating=rating,
                        eaf=estimate.eaf,
                        effort_pm=estimate.development_effort_pm,
                        time_months=estimate.development_time_months,
                    )
                )

            effort_values = [row.effort_pm for row in rows]
            time_values = [row.time_months for row in rows]
            sweeps.append(
                DriverSweep(
                    driver_id=driver_id,
                    driver_title=definition.title,
                    rows=tuple(rows),
                    effort_delta_pm=max(effort_values) - min(effort_values),
                    effort_delta_percent=self._relative_delta(effort_values),
                    time_delta_months=max(time_values) - min(time_values),
                    time_delta_percent=self._relative_delta(time_values),
                )
            )
        return tuple(sweeps)

    @staticmethod
    def _relative_delta(values: list[float]) -> float:
        lower_bound = min(values)
        upper_bound = max(values)
        if lower_bound == 0:
            return 0.0
        return (upper_bound - lower_bound) / lower_bound * 100.0

    @staticmethod
    def _max_spread_driver(sweeps: tuple[DriverSweep, ...], key: str) -> str:
        if key == "effort":
            best = max(sweeps, key=lambda item: item.effort_delta_percent)
        else:
            best = max(sweeps, key=lambda item: item.time_delta_percent)
        return best.driver_id

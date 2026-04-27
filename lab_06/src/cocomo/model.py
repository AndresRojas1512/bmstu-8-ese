from __future__ import annotations

from dataclasses import dataclass

from .drivers import COST_DRIVERS, COST_DRIVER_MAP, default_driver_ratings
from .enums import ProjectMode, Rating


@dataclass(frozen=True, slots=True)
class ProjectProfile:
    mode: ProjectMode
    kloc: float
    driver_ratings: dict[str, Rating]
    cost_per_person_month: float | None = None


@dataclass(frozen=True, slots=True)
class ProjectEstimate:
    profile: ProjectProfile
    eaf: float
    driver_factors: dict[str, float]
    development_effort_pm: float
    development_time_months: float
    average_team_size: float


class COCOMOCalculator:
    _MODE_COEFFICIENTS: dict[ProjectMode, tuple[float, float, float, float]] = {
        ProjectMode.ORGANIC: (3.2, 1.05, 2.5, 0.38),
        ProjectMode.SEMIDETACHED: (3.0, 1.12, 2.5, 0.35),
        ProjectMode.EMBEDDED: (2.8, 1.20, 2.5, 0.32),
    }

    def estimate(self, profile: ProjectProfile) -> ProjectEstimate:
        self._validate(profile)
        eaf, factors = self._compute_eaf(profile.driver_ratings)
        effort_a, effort_b, schedule_c, schedule_d = self._MODE_COEFFICIENTS[profile.mode]

        development_effort_pm = effort_a * eaf * (profile.kloc ** effort_b)
        development_time_months = schedule_c * (development_effort_pm ** schedule_d)
        average_team_size = development_effort_pm / development_time_months

        return ProjectEstimate(
            profile=ProjectProfile(
                mode=profile.mode,
                kloc=profile.kloc,
                driver_ratings=dict(profile.driver_ratings),
                cost_per_person_month=profile.cost_per_person_month,
            ),
            eaf=eaf,
            driver_factors=factors,
            development_effort_pm=development_effort_pm,
            development_time_months=development_time_months,
            average_team_size=average_team_size,
        )

    def _compute_eaf(self, ratings: dict[str, Rating]) -> tuple[float, dict[str, float]]:
        effective_ratings = default_driver_ratings()
        effective_ratings.update(ratings)

        factors: dict[str, float] = {}
        eaf = 1.0
        for driver in COST_DRIVERS:
            rating = effective_ratings[driver.identifier]
            factor = driver.factor_for(rating)
            factors[driver.identifier] = factor
            eaf *= factor
        return eaf, factors

    def _validate(self, profile: ProjectProfile) -> None:
        if profile.kloc <= 0:
            raise ValueError("KLOC must be greater than zero.")
        for driver_id, rating in profile.driver_ratings.items():
            if driver_id not in COST_DRIVER_MAP:
                raise ValueError(f"Unknown cost driver: {driver_id}")
            definition = COST_DRIVER_MAP[driver_id]
            if rating not in definition.factors:
                raise ValueError(
                    f"Rating {rating.label} is not valid for driver {driver_id}."
                )
        if profile.cost_per_person_month is not None and profile.cost_per_person_month < 0:
            raise ValueError("Cost per person-month cannot be negative.")

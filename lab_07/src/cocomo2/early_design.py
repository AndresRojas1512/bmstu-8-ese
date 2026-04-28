from __future__ import annotations

from dataclasses import dataclass

from .enums import Rating


@dataclass(frozen=True, slots=True)
class ExponentFactorDefinition:
    identifier: str
    title: str
    values: dict[Rating, float]

    def value_for(self, rating: Rating) -> float:
        if rating not in self.values:
            raise ValueError(f"Уровень '{rating.label}' недопустим для показателя степени {self.identifier}.")
        return self.values[rating]


@dataclass(frozen=True, slots=True)
class EffortCoefficientDefinition:
    identifier: str
    title: str
    values: dict[Rating, float]

    def value_for(self, rating: Rating) -> float:
        if rating not in self.values:
            raise ValueError(f"Уровень '{rating.label}' недопустим для коэффициента трудоемкости {self.identifier}.")
        return self.values[rating]


@dataclass(frozen=True, slots=True)
class EarlyDesignProject:
    size: float
    exponent_factor_ratings: dict[str, Rating]
    effort_coefficient_ratings: dict[str, Rating]
    cost_per_person_month: float | None = None


@dataclass(frozen=True, slots=True)
class EarlyDesignResult:
    exponent: float
    exponent_factor_sum: float
    effort_coefficient_product: float
    effort_person_months: float
    time_months: float
    average_team_size: float
    budget: float | None


def _exponent_factor(identifier: str, title: str, values: dict[Rating, float]) -> ExponentFactorDefinition:
    return ExponentFactorDefinition(identifier=identifier, title=title, values=values)


def _effort_coefficient(
    identifier: str,
    title: str,
    values: dict[Rating, float],
) -> EffortCoefficientDefinition:
    return EffortCoefficientDefinition(identifier=identifier, title=title, values=values)


EXPONENT_FACTOR_DEFINITIONS: tuple[ExponentFactorDefinition, ...] = (
    _exponent_factor(
        "PREC",
        "Новизна проекта",
        {
            Rating.VERY_LOW: 6.20,
            Rating.LOW: 4.96,
            Rating.NOMINAL: 3.72,
            Rating.HIGH: 2.48,
            Rating.VERY_HIGH: 1.24,
            Rating.EXTRA_HIGH: 0.00,
        },
    ),
    _exponent_factor(
        "FLEX",
        "Гибкость процесса разработки",
        {
            Rating.VERY_LOW: 5.07,
            Rating.LOW: 4.05,
            Rating.NOMINAL: 3.04,
            Rating.HIGH: 2.03,
            Rating.VERY_HIGH: 1.01,
            Rating.EXTRA_HIGH: 0.00,
        },
    ),
    _exponent_factor(
        "RESL",
        "Разрешение рисков в архитектуре",
        {
            Rating.VERY_LOW: 7.00,
            Rating.LOW: 5.65,
            Rating.NOMINAL: 4.24,
            Rating.HIGH: 2.83,
            Rating.VERY_HIGH: 1.41,
            Rating.EXTRA_HIGH: 0.00,
        },
    ),
    _exponent_factor(
        "TEAM",
        "Сплоченность команды",
        {
            Rating.VERY_LOW: 5.48,
            Rating.LOW: 4.38,
            Rating.NOMINAL: 3.29,
            Rating.HIGH: 2.19,
            Rating.VERY_HIGH: 1.10,
            Rating.EXTRA_HIGH: 0.00,
        },
    ),
    _exponent_factor(
        "PMAT",
        "Зрелость процесса разработки",
        {
            Rating.VERY_LOW: 7.00,
            Rating.LOW: 6.24,
            Rating.NOMINAL: 4.68,
            # The lecture PDF OCR drops the leading "3" and misreads CMM level 4.
            Rating.HIGH: 3.12,
            Rating.VERY_HIGH: 1.56,
            Rating.EXTRA_HIGH: 0.00,
        },
    ),
)

EFFORT_COEFFICIENT_DEFINITIONS: tuple[EffortCoefficientDefinition, ...] = (
    _effort_coefficient(
        "PERS",
        "Квалификация персонала",
        {
            Rating.VERY_LOW: 1.62,
            Rating.LOW: 1.26,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 0.83,
            Rating.VERY_HIGH: 0.63,
            Rating.EXTRA_HIGH: 0.50,
        },
    ),
    _effort_coefficient(
        "RCPX",
        "Надежность и сложность продукта",
        {
            Rating.VERY_LOW: 0.60,
            Rating.LOW: 0.83,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 1.33,
            Rating.VERY_HIGH: 1.91,
            Rating.EXTRA_HIGH: 2.72,
        },
    ),
    _effort_coefficient(
        "RUSE",
        "Требуемый уровень повторного использования",
        {
            Rating.LOW: 0.95,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 1.07,
            Rating.VERY_HIGH: 1.15,
            Rating.EXTRA_HIGH: 1.24,
        },
    ),
    _effort_coefficient(
        "PDIF",
        "Сложность платформы",
        {
            Rating.LOW: 0.87,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 1.29,
            Rating.VERY_HIGH: 1.81,
            Rating.EXTRA_HIGH: 2.61,
        },
    ),
    _effort_coefficient(
        "PREX",
        "Опыт работы в предметной области и на платформе",
        {
            Rating.VERY_LOW: 1.33,
            Rating.LOW: 1.22,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 0.87,
            Rating.VERY_HIGH: 0.74,
            Rating.EXTRA_HIGH: 0.62,
        },
    ),
    _effort_coefficient(
        "FCIL",
        "Возможности инструментальных средств",
        {
            Rating.VERY_LOW: 1.30,
            Rating.LOW: 1.10,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 0.87,
            Rating.VERY_HIGH: 0.73,
            Rating.EXTRA_HIGH: 0.62,
        },
    ),
    _effort_coefficient(
        "SCED",
        "Требуемые сроки разработки",
        {
            Rating.VERY_LOW: 1.43,
            Rating.LOW: 1.14,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 1.00,
            Rating.VERY_HIGH: 1.00,
        },
    ),
)

_EXPONENT_FACTOR_MAP: dict[str, ExponentFactorDefinition] = {
    item.identifier: item for item in EXPONENT_FACTOR_DEFINITIONS
}

_EFFORT_COEFFICIENT_MAP: dict[str, EffortCoefficientDefinition] = {
    item.identifier: item for item in EFFORT_COEFFICIENT_DEFINITIONS
}


class EarlyDesignCalculator:
    def estimate(self, project: EarlyDesignProject) -> EarlyDesignResult:
        self._validate(project)

        exponent_factor_sum = 0.0
        for identifier, definition in _EXPONENT_FACTOR_MAP.items():
            exponent_factor_sum += definition.value_for(project.exponent_factor_ratings[identifier])

        exponent = 1.01 + 0.01 * exponent_factor_sum

        effort_coefficient_product = 1.0
        for identifier, definition in _EFFORT_COEFFICIENT_MAP.items():
            effort_coefficient_product *= definition.value_for(project.effort_coefficient_ratings[identifier])

        effort_person_months = 2.45 * effort_coefficient_product * (project.size ** exponent)
        schedule_exponent = 0.33 + 0.2 * (exponent - 1.01)
        time_months = 3.0 * (effort_person_months ** schedule_exponent)
        average_team_size = effort_person_months / time_months
        budget = None if project.cost_per_person_month is None else effort_person_months * project.cost_per_person_month

        return EarlyDesignResult(
            exponent=exponent,
            exponent_factor_sum=exponent_factor_sum,
            effort_coefficient_product=effort_coefficient_product,
            effort_person_months=effort_person_months,
            time_months=time_months,
            average_team_size=average_team_size,
            budget=budget,
        )

    @staticmethod
    def _validate(project: EarlyDesignProject) -> None:
        if project.size <= 0:
            raise ValueError("Размер проекта должен быть положительным.")
        if set(project.exponent_factor_ratings) != set(_EXPONENT_FACTOR_MAP):
            raise ValueError("Нужно указать все пять показателей степени.")
        if set(project.effort_coefficient_ratings) != set(_EFFORT_COEFFICIENT_MAP):
            raise ValueError("Нужно указать все семь коэффициентов трудоемкости.")
        if project.cost_per_person_month is not None and project.cost_per_person_month < 0:
            raise ValueError("Стоимость человеко-месяца не может быть отрицательной.")

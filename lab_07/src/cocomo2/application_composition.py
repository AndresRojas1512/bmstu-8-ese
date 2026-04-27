from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .enums import Rating
from .early_design import SCALE_FACTOR_DEFINITIONS


class ObjectPointKind(Enum):
    SCREEN = "Экран"
    REPORT = "Отчет"
    MODULE_3GL = "Модуль 3GL"

    @property
    def label(self) -> str:
        return self.value


class ObjectPointComplexity(Enum):
    SIMPLE = "Простой"
    MEDIUM = "Средний"
    COMPLEX = "Сложный"

    @property
    def label(self) -> str:
        return self.value


class ProductivityLevel(Enum):
    VERY_LOW = ("Очень низкая", 4.0)
    LOW = ("Низкая", 7.0)
    NOMINAL = ("Номинальная", 13.0)
    HIGH = ("Высокая", 25.0)
    VERY_HIGH = ("Очень высокая", 50.0)

    @property
    def label(self) -> str:
        return self.value[0]

    @property
    def productivity(self) -> float:
        return self.value[1]


@dataclass(frozen=True, slots=True)
class ObjectPointItem:
    name: str
    kind: ObjectPointKind
    complexity: ObjectPointComplexity | None
    count: int = 1
    notes: str = ""


@dataclass(frozen=True, slots=True)
class ApplicationCompositionProject:
    items: tuple[ObjectPointItem, ...]
    reuse_percent: float
    productivity_level: ProductivityLevel
    scale_factor_ratings: dict[str, Rating]
    cost_per_person_month: float | None = None


@dataclass(frozen=True, slots=True)
class RatedObjectPointItem:
    item: ObjectPointItem
    weight: int
    points: int


@dataclass(frozen=True, slots=True)
class ApplicationCompositionResult:
    rated_items: tuple[RatedObjectPointItem, ...]
    object_points: float
    new_object_points: float
    exponent: float
    effort_person_months: float
    time_months: float
    average_team_size: float
    budget: float | None


_SCREEN_WEIGHTS: dict[ObjectPointComplexity, int] = {
    ObjectPointComplexity.SIMPLE: 1,
    ObjectPointComplexity.MEDIUM: 2,
    ObjectPointComplexity.COMPLEX: 3,
}

_REPORT_WEIGHTS: dict[ObjectPointComplexity, int] = {
    ObjectPointComplexity.SIMPLE: 2,
    ObjectPointComplexity.MEDIUM: 5,
    ObjectPointComplexity.COMPLEX: 8,
}


class ApplicationCompositionCalculator:
    def calculate(self, project: ApplicationCompositionProject) -> ApplicationCompositionResult:
        self._validate(project)

        rated_items = tuple(self._rate_item(item) for item in project.items)
        object_points = float(sum(item.points for item in rated_items))
        new_object_points = object_points * (100.0 - project.reuse_percent) / 100.0
        scale_factor_sum = 0.0
        for definition in SCALE_FACTOR_DEFINITIONS:
            scale_factor_sum += definition.value_for(project.scale_factor_ratings[definition.identifier])
        exponent = 1.01 + 0.01 * scale_factor_sum
        effort_person_months = new_object_points / project.productivity_level.productivity
        schedule_exponent = 0.33 + 0.2 * (exponent - 1.01)
        time_months = 3.0 * (effort_person_months ** schedule_exponent)
        average_team_size = effort_person_months / time_months
        budget = None if project.cost_per_person_month is None else effort_person_months * project.cost_per_person_month

        return ApplicationCompositionResult(
            rated_items=rated_items,
            object_points=object_points,
            new_object_points=new_object_points,
            exponent=exponent,
            effort_person_months=effort_person_months,
            time_months=time_months,
            average_team_size=average_team_size,
            budget=budget,
        )

    def _rate_item(self, item: ObjectPointItem) -> RatedObjectPointItem:
        weight = self._weight_for(item)
        return RatedObjectPointItem(item=item, weight=weight, points=weight * item.count)

    @staticmethod
    def _weight_for(item: ObjectPointItem) -> int:
        if item.kind is ObjectPointKind.MODULE_3GL:
            return 10

        if item.complexity is None:
            raise ValueError(f"Complexity is required for '{item.name}'.")

        if item.kind is ObjectPointKind.SCREEN:
            return _SCREEN_WEIGHTS[item.complexity]
        return _REPORT_WEIGHTS[item.complexity]

    @staticmethod
    def _validate(project: ApplicationCompositionProject) -> None:
        if not project.items:
            raise ValueError("At least one object point item is required.")
        if project.reuse_percent < 0 or project.reuse_percent > 100:
            raise ValueError("Reuse percent must be between 0 and 100.")
        if set(project.scale_factor_ratings) != {definition.identifier for definition in SCALE_FACTOR_DEFINITIONS}:
            raise ValueError("All five scale factors must be provided.")
        if project.cost_per_person_month is not None and project.cost_per_person_month < 0:
            raise ValueError("Cost per person-month cannot be negative.")

        for item in project.items:
            if item.count <= 0:
                raise ValueError(f"Count must be positive for '{item.name}'.")

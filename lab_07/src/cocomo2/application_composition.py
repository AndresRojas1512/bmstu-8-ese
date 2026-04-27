from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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
    effort_person_months: float


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
        effort_person_months = new_object_points / project.productivity_level.productivity

        return ApplicationCompositionResult(
            rated_items=rated_items,
            object_points=object_points,
            new_object_points=new_object_points,
            effort_person_months=effort_person_months,
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

        for item in project.items:
            if item.count <= 0:
                raise ValueError(f"Count must be positive for '{item.name}'.")

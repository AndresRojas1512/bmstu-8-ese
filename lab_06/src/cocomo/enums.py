from __future__ import annotations

from enum import Enum


class Rating(Enum):
    VERY_LOW = "Очень низкий"
    LOW = "Низкий"
    NOMINAL = "Номинальный"
    HIGH = "Высокий"
    VERY_HIGH = "Очень высокий"
    EXTRA_HIGH = "Экстремально высокий"

    @property
    def label(self) -> str:
        return self.value


class ProjectMode(Enum):
    ORGANIC = "Обычный"
    SEMIDETACHED = "Промежуточный"
    EMBEDDED = "Встроенный"

    @property
    def label(self) -> str:
        return self.value

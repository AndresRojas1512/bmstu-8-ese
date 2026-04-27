from __future__ import annotations

from enum import Enum


class Rating(Enum):
    VERY_LOW = "Очень низкий"
    LOW = "Низкий"
    NOMINAL = "Номинальный"
    HIGH = "Высокий"
    VERY_HIGH = "Очень высокий"
    EXTRA_HIGH = "Сверхвысокий"

    @property
    def label(self) -> str:
        return self.value


class ComplexityLevel(Enum):
    LOW = "Низкий"
    AVERAGE = "Средний"
    HIGH = "Высокий"

    @property
    def label(self) -> str:
        return self.value


class FunctionPointComponentType(Enum):
    EI = "Внешний ввод"
    EO = "Внешний вывод"
    EQ = "Внешний запрос"
    ILF = "Внутренний логический файл"
    EIF = "Внешний интерфейсный файл"

    @property
    def label(self) -> str:
        return self.value

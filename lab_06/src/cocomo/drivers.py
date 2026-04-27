from __future__ import annotations

from dataclasses import dataclass

from .enums import Rating


@dataclass(frozen=True, slots=True)
class CostDriverDefinition:
    identifier: str
    title: str
    group: str
    factors: dict[Rating, float]
    default_rating: Rating = Rating.NOMINAL

    @property
    def ratings(self) -> tuple[Rating, ...]:
        return tuple(self.factors.keys())

    def factor_for(self, rating: Rating) -> float:
        if rating not in self.factors:
            raise ValueError(f"Rating {rating.label} is not allowed for driver {self.identifier}.")
        return self.factors[rating]


def _driver(
    identifier: str,
    title: str,
    group: str,
    factors: dict[Rating, float],
) -> CostDriverDefinition:
    return CostDriverDefinition(identifier=identifier, title=title, group=group, factors=factors)


COST_DRIVERS: tuple[CostDriverDefinition, ...] = (
    _driver(
        "RELY",
        "Требуемая надежность ПО",
        "Продукт",
        {
            Rating.VERY_LOW: 0.75,
            Rating.LOW: 0.88,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 1.15,
            Rating.VERY_HIGH: 1.40,
        },
    ),
    _driver(
        "DATA",
        "Размер базы данных",
        "Продукт",
        {
            Rating.LOW: 0.94,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 1.08,
            Rating.VERY_HIGH: 1.16,
        },
    ),
    _driver(
        "CPLX",
        "Сложность продукта",
        "Продукт",
        {
            Rating.VERY_LOW: 0.70,
            Rating.LOW: 0.85,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 1.15,
            Rating.VERY_HIGH: 1.30,
            Rating.EXTRA_HIGH: 1.65,
        },
    ),
    _driver(
        "TIME",
        "Ограничение времени выполнения",
        "Компьютер",
        {
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 1.11,
            Rating.VERY_HIGH: 1.30,
            Rating.EXTRA_HIGH: 1.66,
        },
    ),
    _driver(
        "STOR",
        "Ограничение основной памяти",
        "Компьютер",
        {
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 1.06,
            Rating.VERY_HIGH: 1.21,
            Rating.EXTRA_HIGH: 1.56,
        },
    ),
    _driver(
        "VIRT",
        "Изменчивость виртуальной машины",
        "Компьютер",
        {
            Rating.LOW: 0.87,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 1.15,
            Rating.VERY_HIGH: 1.30,
        },
    ),
    _driver(
        "TURN",
        "Время реакции компьютера",
        "Компьютер",
        {
            Rating.LOW: 0.87,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 1.07,
            Rating.VERY_HIGH: 1.15,
        },
    ),
    _driver(
        "ACAP",
        "Способности аналитика",
        "Персонал",
        {
            Rating.VERY_LOW: 1.46,
            Rating.LOW: 1.19,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 0.86,
            Rating.VERY_HIGH: 0.71,
        },
    ),
    _driver(
        "AEXP",
        "Знание приложений",
        "Персонал",
        {
            Rating.VERY_LOW: 1.29,
            Rating.LOW: 1.13,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 0.91,
            Rating.VERY_HIGH: 0.82,
        },
    ),
    _driver(
        "PCAP",
        "Способности программиста",
        "Персонал",
        {
            Rating.VERY_LOW: 1.42,
            Rating.LOW: 1.17,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 0.86,
            Rating.VERY_HIGH: 0.70,
        },
    ),
    _driver(
        "VEXP",
        "Знание виртуальной машины",
        "Персонал",
        {
            Rating.VERY_LOW: 1.21,
            Rating.LOW: 1.10,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 0.90,
        },
    ),
    _driver(
        "LEXP",
        "Знание языка программирования",
        "Персонал",
        {
            Rating.VERY_LOW: 1.14,
            Rating.LOW: 1.07,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 0.95,
        },
    ),
    _driver(
        "MODP",
        "Использование современных методов",
        "Проект",
        {
            Rating.VERY_LOW: 1.24,
            Rating.LOW: 1.10,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 0.91,
            Rating.VERY_HIGH: 0.82,
        },
    ),
    _driver(
        "TOOL",
        "Использование программных инструментов",
        "Проект",
        {
            Rating.VERY_LOW: 1.24,
            Rating.LOW: 1.10,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 0.91,
            Rating.VERY_HIGH: 0.83,
        },
    ),
    _driver(
        "SCED",
        "Требуемые сроки разработки",
        "Проект",
        {
            Rating.VERY_LOW: 1.23,
            Rating.LOW: 1.08,
            Rating.NOMINAL: 1.00,
            Rating.HIGH: 1.04,
            Rating.VERY_HIGH: 1.10,
        },
    ),
)

COST_DRIVER_MAP: dict[str, CostDriverDefinition] = {
    driver.identifier: driver for driver in COST_DRIVERS
}


def default_driver_ratings() -> dict[str, Rating]:
    return {driver.identifier: driver.default_rating for driver in COST_DRIVERS}

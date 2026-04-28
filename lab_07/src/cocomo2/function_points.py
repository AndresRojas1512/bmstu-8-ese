from __future__ import annotations

from dataclasses import dataclass

from .enums import ComplexityLevel, FunctionPointComponentType


@dataclass(frozen=True, slots=True)
class SystemCharacteristicDefinition:
    identifier: int
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class SystemCharacteristic:
    definition: SystemCharacteristicDefinition
    value: int


@dataclass(frozen=True, slots=True)
class FunctionPointComponent:
    name: str
    component_type: FunctionPointComponentType
    det_count: int
    reference_count: int
    notes: str = ""


@dataclass(frozen=True, slots=True)
class RatedFunctionPointComponent:
    component: FunctionPointComponent
    complexity: ComplexityLevel
    weight: int


@dataclass(frozen=True, slots=True)
class FunctionPointProject:
    components: tuple[FunctionPointComponent, ...]
    characteristics: tuple[SystemCharacteristic, ...]


@dataclass(frozen=True, slots=True)
class FunctionPointResult:
    rated_components: tuple[RatedFunctionPointComponent, ...]
    unadjusted_points: float
    total_characteristics: int
    value_adjustment_factor: float
    adjusted_points: float


FUNCTION_POINT_CHARACTERISTICS: tuple[SystemCharacteristicDefinition, ...] = (
    SystemCharacteristicDefinition(1, "Передачи данных", "Требования к обмену данными и коммуникациям."),
    SystemCharacteristicDefinition(2, "Распределенная обработка данных", "Степень распределенности обработки."),
    SystemCharacteristicDefinition(3, "Производительность", "Требования к времени отклика и производительности."),
    SystemCharacteristicDefinition(4, "Эксплуатационные ограничения", "Ограничения по аппаратным ресурсам."),
    SystemCharacteristicDefinition(5, "Частота транзакций", "Интенсивность транзакционной нагрузки."),
    SystemCharacteristicDefinition(6, "Оперативный ввод данных", "Интенсивность интерактивного ввода."),
    SystemCharacteristicDefinition(7, "Эффективность работы конечных пользователей", "Требования к эргономике."),
    SystemCharacteristicDefinition(8, "Оперативное обновление", "Степень онлайн-обновления внутренних файлов."),
    SystemCharacteristicDefinition(9, "Сложность обработки", "Интенсивность логической и математической обработки."),
    SystemCharacteristicDefinition(10, "Повторная используемость", "Требования к повторному использованию."),
    SystemCharacteristicDefinition(11, "Легкость инсталляции", "Сложность преобразования и установки."),
    SystemCharacteristicDefinition(12, "Легкость эксплуатации", "Автоматизация администрирования и восстановления."),
    SystemCharacteristicDefinition(13, "Количество возможных установок на различных платформах", "Требования к переносимости."),
    SystemCharacteristicDefinition(14, "Простота изменений", "Требования к гибкости и управляемости изменений."),
)

_CHARACTERISTIC_MAP: dict[int, SystemCharacteristicDefinition] = {
    item.identifier: item for item in FUNCTION_POINT_CHARACTERISTICS
}

_WEIGHTS: dict[FunctionPointComponentType, dict[ComplexityLevel, int]] = {
    FunctionPointComponentType.EI: {
        ComplexityLevel.LOW: 3,
        ComplexityLevel.AVERAGE: 4,
        ComplexityLevel.HIGH: 6,
    },
    FunctionPointComponentType.EO: {
        ComplexityLevel.LOW: 4,
        ComplexityLevel.AVERAGE: 5,
        ComplexityLevel.HIGH: 7,
    },
    FunctionPointComponentType.EQ: {
        ComplexityLevel.LOW: 3,
        ComplexityLevel.AVERAGE: 4,
        ComplexityLevel.HIGH: 6,
    },
    FunctionPointComponentType.ILF: {
        ComplexityLevel.LOW: 7,
        ComplexityLevel.AVERAGE: 10,
        ComplexityLevel.HIGH: 15,
    },
    FunctionPointComponentType.EIF: {
        ComplexityLevel.LOW: 5,
        ComplexityLevel.AVERAGE: 7,
        ComplexityLevel.HIGH: 10,
    },
}

_TRANSACTION_MATRIX: tuple[tuple[ComplexityLevel, ...], ...] = (
    (ComplexityLevel.LOW, ComplexityLevel.LOW, ComplexityLevel.AVERAGE),
    (ComplexityLevel.LOW, ComplexityLevel.AVERAGE, ComplexityLevel.HIGH),
    (ComplexityLevel.AVERAGE, ComplexityLevel.HIGH, ComplexityLevel.HIGH),
)

_DATA_MATRIX: tuple[tuple[ComplexityLevel, ...], ...] = (
    (ComplexityLevel.LOW, ComplexityLevel.LOW, ComplexityLevel.AVERAGE),
    (ComplexityLevel.LOW, ComplexityLevel.AVERAGE, ComplexityLevel.HIGH),
    (ComplexityLevel.AVERAGE, ComplexityLevel.HIGH, ComplexityLevel.HIGH),
)


def build_characteristics(values: dict[int, int]) -> tuple[SystemCharacteristic, ...]:
    ordered: list[SystemCharacteristic] = []
    for identifier in range(1, len(FUNCTION_POINT_CHARACTERISTICS) + 1):
        if identifier not in values:
            raise ValueError(f"Отсутствует системная характеристика {identifier}.")
        ordered.append(SystemCharacteristic(definition=_CHARACTERISTIC_MAP[identifier], value=values[identifier]))
    return tuple(ordered)


class FunctionPointCalculator:
    def calculate(self, project: FunctionPointProject) -> FunctionPointResult:
        self._validate_project(project)

        rated_components = tuple(self._rate_component(item) for item in project.components)
        unadjusted_points = float(sum(item.weight for item in rated_components))
        total_characteristics = sum(item.value for item in project.characteristics)
        value_adjustment_factor = 0.65 + 0.01 * total_characteristics
        adjusted_points = unadjusted_points * value_adjustment_factor

        return FunctionPointResult(
            rated_components=rated_components,
            unadjusted_points=unadjusted_points,
            total_characteristics=total_characteristics,
            value_adjustment_factor=value_adjustment_factor,
            adjusted_points=adjusted_points,
        )

    def _rate_component(self, component: FunctionPointComponent) -> RatedFunctionPointComponent:
        if component.component_type in {FunctionPointComponentType.ILF, FunctionPointComponentType.EIF}:
            complexity = self._classify_data_function(component.reference_count, component.det_count)
        else:
            complexity = self._classify_transaction(component.component_type, component.reference_count, component.det_count)

        return RatedFunctionPointComponent(
            component=component,
            complexity=complexity,
            weight=_WEIGHTS[component.component_type][complexity],
        )

    @staticmethod
    def _classify_data_function(ret_count: int, det_count: int) -> ComplexityLevel:
        row = _band_index(ret_count, (1, 5))
        column = _band_index(det_count, (19, 50))
        return _DATA_MATRIX[row][column]

    @staticmethod
    def _classify_transaction(
        component_type: FunctionPointComponentType,
        ftr_count: int,
        det_count: int,
    ) -> ComplexityLevel:
        if component_type is FunctionPointComponentType.EI:
            row = _band_index(ftr_count, (1, 2))
            column = _band_index(det_count, (4, 15))
            return _TRANSACTION_MATRIX[row][column]

        row = _band_index(ftr_count, (1, 3))
        column = _band_index(det_count, (4, 19))
        return _TRANSACTION_MATRIX[row][column]

    @staticmethod
    def _validate_project(project: FunctionPointProject) -> None:
        if not project.components:
            raise ValueError("Нужно указать хотя бы одну функциональную компоненту.")
        if len(project.characteristics) != len(FUNCTION_POINT_CHARACTERISTICS):
            raise ValueError("Нужно указать ровно 14 системных характеристик.")

        seen_ids: set[int] = set()
        for characteristic in project.characteristics:
            identifier = characteristic.definition.identifier
            if identifier in seen_ids:
                raise ValueError(f"Системная характеристика {identifier} указана дважды.")
            seen_ids.add(identifier)
            if characteristic.value < 0 or characteristic.value > 5:
                raise ValueError(f"Значение характеристики {identifier} должно быть в диапазоне от 0 до 5.")

        for component in project.components:
            if component.det_count <= 0:
                raise ValueError(f"Количество DET для '{component.name}' должно быть положительным.")
            if component.reference_count < 0:
                raise ValueError(f"Количество ссылок для '{component.name}' не может быть отрицательным.")


def _band_index(value: int, thresholds: tuple[int, int]) -> int:
    if value <= thresholds[0]:
        return 0
    if value <= thresholds[1]:
        return 1
    return 2

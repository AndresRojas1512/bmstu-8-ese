from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in {None, ""}:
    from cocomo2 import (
        ApplicationCompositionCalculator,
        ApplicationCompositionProject,
        ApplicationCompositionResult,
        BackfiringProject,
        BackfiringResult,
        EFFORT_MULTIPLIER_DEFINITIONS,
        EarlyDesignCalculator,
        EarlyDesignProject,
        EarlyDesignResult,
        FUNCTION_POINT_CHARACTERISTICS,
        FunctionPointCalculator,
        FunctionPointComponent,
        FunctionPointComponentType,
        FunctionPointProject,
        FunctionPointResult,
        Lab7VariantPreset,
        LanguageFootprint,
        ObjectPointComplexity,
        ObjectPointItem,
        ObjectPointKind,
        ProductivityLevel,
        Rating,
        SCALE_FACTOR_DEFINITIONS,
        SizeBackfiringService,
        build_characteristics,
        build_variant_2_preset,
    )
    from exporters import CsvExportService
    from qt_compat import (
        QApplication,
        QComboBox,
        QDoubleSpinBox,
        QFileDialog,
        QFormLayout,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QPlainTextEdit,
        QScrollArea,
        QSpinBox,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
        QT_BINDING,
    )
else:
    from .cocomo2 import (
        ApplicationCompositionCalculator,
        ApplicationCompositionProject,
        ApplicationCompositionResult,
        BackfiringProject,
        BackfiringResult,
        EFFORT_MULTIPLIER_DEFINITIONS,
        EarlyDesignCalculator,
        EarlyDesignProject,
        EarlyDesignResult,
        FUNCTION_POINT_CHARACTERISTICS,
        FunctionPointCalculator,
        FunctionPointComponent,
        FunctionPointComponentType,
        FunctionPointProject,
        FunctionPointResult,
        Lab7VariantPreset,
        LanguageFootprint,
        ObjectPointComplexity,
        ObjectPointItem,
        ObjectPointKind,
        ProductivityLevel,
        Rating,
        SCALE_FACTOR_DEFINITIONS,
        SizeBackfiringService,
        build_characteristics,
        build_variant_2_preset,
    )
    from .exporters import CsvExportService
    from .qt_compat import (
        QApplication,
        QComboBox,
        QDoubleSpinBox,
        QFileDialog,
        QFormLayout,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QPlainTextEdit,
        QScrollArea,
        QSpinBox,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
        QT_BINDING,
    )


def _format_float(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def _item_text(item: QTableWidgetItem | None) -> str:
    return "" if item is None else item.text().strip()


def _parse_int(value: str, *, row: int, field: str, minimum: int = 0, allow_zero: bool = True) -> int:
    try:
        parsed = int(value.strip())
    except ValueError as error:
        raise ValueError(f"Строка {row}: поле '{field}' должно быть целым числом.") from error

    if allow_zero:
        if parsed < minimum:
            raise ValueError(f"Строка {row}: поле '{field}' должно быть не меньше {minimum}.")
    else:
        if parsed <= minimum:
            raise ValueError(f"Строка {row}: поле '{field}' должно быть больше {minimum}.")
    return parsed


def _parse_float(value: str, *, row: int, field: str, minimum: float = 0.0, strict_min: bool = False) -> float:
    normalized = value.strip().replace(",", ".")
    try:
        parsed = float(normalized)
    except ValueError as error:
        raise ValueError(f"Строка {row}: поле '{field}' должно быть числом.") from error

    if strict_min:
        if parsed <= minimum:
            raise ValueError(f"Строка {row}: поле '{field}' должно быть больше {minimum}.")
    elif parsed < minimum:
        raise ValueError(f"Строка {row}: поле '{field}' должно быть не меньше {minimum}.")
    return parsed


def _selected_row(table: QTableWidget) -> int | None:
    indexes = table.selectionModel().selectedRows()
    if not indexes:
        return None
    return indexes[0].row()


@dataclass(frozen=True, slots=True)
class FunctionPointPayload:
    project: FunctionPointProject
    result: FunctionPointResult


@dataclass(frozen=True, slots=True)
class ApplicationCompositionPayload:
    project: ApplicationCompositionProject
    result: ApplicationCompositionResult


@dataclass(frozen=True, slots=True)
class EarlyDesignPayload:
    function_point_result: FunctionPointResult
    backfiring_project: BackfiringProject
    backfiring_result: BackfiringResult
    early_design_project: EarlyDesignProject | None
    early_design_result: EarlyDesignResult | None


class FunctionPointTab(QWidget):
    def __init__(
        self,
        calculator: FunctionPointCalculator,
        preset: Lab7VariantPreset,
        export_service: CsvExportService,
    ) -> None:
        super().__init__()
        self._calculator = calculator
        self._preset = preset
        self._export_service = export_service
        self._payload: FunctionPointPayload | None = None

        self._components = QTableWidget()
        self._characteristics = QTableWidget()
        self._summary = QPlainTextEdit()
        self._results = QTableWidget()
        self._build_ui()
        self.load_preset(preset)

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)

        controls = QWidget()
        controls_layout = QVBoxLayout(controls)

        components_box = QGroupBox("Функции приложения")
        components_layout = QVBoxLayout(components_box)
        self._components.setColumnCount(5)
        self._components.setHorizontalHeaderLabels(["Функция", "Тип", "DET", "FTR/RET", "Примечание"])
        self._components.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._components.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        components_layout.addWidget(self._components)
        component_buttons = QWidget()
        component_buttons_layout = QHBoxLayout(component_buttons)
        add_component_button = QPushButton("Добавить функцию")
        add_component_button.clicked.connect(self._add_component_row)
        remove_component_button = QPushButton("Удалить выбранную")
        remove_component_button.clicked.connect(self._remove_selected_component_row)
        component_buttons_layout.addWidget(add_component_button)
        component_buttons_layout.addWidget(remove_component_button)
        components_layout.addWidget(component_buttons)

        characteristics_box = QGroupBox("14 факторов регулировки")
        characteristics_layout = QVBoxLayout(characteristics_box)
        self._characteristics.setColumnCount(3)
        self._characteristics.setHorizontalHeaderLabels(["#", "Параметр", "Значение 0..5"])
        self._characteristics.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        characteristics_layout.addWidget(self._characteristics)

        buttons = QWidget()
        buttons_layout = QHBoxLayout(buttons)
        calculate_button = QPushButton("Рассчитать FP")
        calculate_button.clicked.connect(self.calculate)
        preset_button = QPushButton("Восстановить исходный сценарий")
        preset_button.clicked.connect(lambda: self.load_preset(self._preset))
        export_button = QPushButton("Экспорт CSV")
        export_button.clicked.connect(self._export_csv)
        buttons_layout.addWidget(calculate_button)
        buttons_layout.addWidget(preset_button)
        buttons_layout.addWidget(export_button)

        controls_layout.addWidget(components_box, stretch=3)
        controls_layout.addWidget(characteristics_box, stretch=2)
        controls_layout.addWidget(buttons)

        results = QWidget()
        results_layout = QVBoxLayout(results)
        self._summary.setReadOnly(True)
        self._summary.setPlaceholderText("Здесь появится сводка по расчету функциональных точек.")
        self._results.setColumnCount(7)
        self._results.setHorizontalHeaderLabels(
            ["Функция", "Тип", "DET", "FTR/RET", "Сложность", "Вес", "Примечание"]
        )
        self._results.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._results.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        results_layout.addWidget(QLabel("Сводка"))
        results_layout.addWidget(self._summary)
        results_layout.addWidget(QLabel("Детализация функций"))
        results_layout.addWidget(self._results)

        root.addWidget(controls, stretch=3)
        root.addWidget(results, stretch=2)

    def load_preset(self, preset: Lab7VariantPreset) -> None:
        self._populate_components(preset.function_point_project.components)
        self._populate_characteristics(preset.function_point_project.characteristics)
        self.calculate()

    def calculate(self) -> FunctionPointPayload | None:
        try:
            project = self._build_project()
            result = self._calculator.calculate(project)
            payload = FunctionPointPayload(project=project, result=result)
            self._payload = payload
            self._render(payload)
            return payload
        except ValueError as error:
            QMessageBox.critical(self, "Ошибка расчета FP", str(error))
            return None

    def current_payload(self) -> FunctionPointPayload | None:
        return self._payload

    def _build_project(self) -> FunctionPointProject:
        components: list[FunctionPointComponent] = []
        for row in range(self._components.rowCount()):
            name_item = self._components.item(row, 0)
            det_item = self._components.item(row, 2)
            ref_item = self._components.item(row, 3)
            note_item = self._components.item(row, 4)
            combo = self._components.cellWidget(row, 1)
            if not isinstance(combo, QComboBox):
                raise ValueError("В таблице функций отсутствует тип функции.")
            component_type = combo.currentData()
            if not isinstance(component_type, FunctionPointComponentType):
                raise ValueError("Нужно выбрать корректный тип функции.")
            if name_item is None or not name_item.text().strip():
                raise ValueError(f"Строка {row + 1}: имя функции не должно быть пустым.")
            if det_item is None or ref_item is None:
                raise ValueError(f"Строка {row + 1}: отсутствуют числовые параметры функции.")
            components.append(
                FunctionPointComponent(
                    name=name_item.text().strip(),
                    component_type=component_type,
                    det_count=_parse_int(_item_text(det_item), row=row + 1, field="DET", minimum=0, allow_zero=False),
                    reference_count=_parse_int(_item_text(ref_item), row=row + 1, field="FTR/RET", minimum=0),
                    notes="" if note_item is None else note_item.text().strip(),
                )
            )

        values: dict[int, int] = {}
        for row in range(self._characteristics.rowCount()):
            identifier_item = self._characteristics.item(row, 0)
            spin = self._characteristics.cellWidget(row, 2)
            if identifier_item is None or not isinstance(spin, QSpinBox):
                raise ValueError("Не удалось прочитать системные параметры FP.")
            values[int(identifier_item.text())] = spin.value()

        return FunctionPointProject(components=tuple(components), characteristics=build_characteristics(values))

    def _render(self, payload: FunctionPointPayload) -> None:
        result = payload.result
        self._summary.setPlainText(
            "\n".join(
                [
                    f"Количество функций: {len(payload.project.components)}",
                    f"Нерегулируемые функциональные точки (UFP): {_format_float(result.unadjusted_points)}",
                    f"Сумма факторов регулировки: {result.total_characteristics}",
                    f"Коэффициент VAF: {_format_float(result.value_adjustment_factor)}",
                    f"Скорректированные функциональные точки (FP): {_format_float(result.adjusted_points)}",
                ]
            )
        )

        self._results.setRowCount(len(result.rated_components))
        for row, item in enumerate(result.rated_components):
            values = [
                item.component.name,
                item.component.component_type.label,
                str(item.component.det_count),
                str(item.component.reference_count),
                item.complexity.label,
                str(item.weight),
                item.component.notes,
            ]
            for column, value in enumerate(values):
                self._results.setItem(row, column, QTableWidgetItem(value))
        self._results.resizeColumnsToContents()

    def _populate_components(self, components: tuple[FunctionPointComponent, ...]) -> None:
        self._components.setRowCount(len(components))
        for row, component in enumerate(components):
            self._set_component_row(row, component)

    def _populate_characteristics(self, characteristics) -> None:
        self._characteristics.setRowCount(len(characteristics))
        for row, characteristic in enumerate(characteristics):
            self._characteristics.setItem(row, 0, QTableWidgetItem(str(characteristic.definition.identifier)))
            self._characteristics.setItem(row, 1, QTableWidgetItem(characteristic.definition.name))
            spin = QSpinBox()
            spin.setRange(0, 5)
            spin.setValue(characteristic.value)
            self._characteristics.setCellWidget(row, 2, spin)

    def _set_component_row(self, row: int, component: FunctionPointComponent) -> None:
        self._components.setItem(row, 0, QTableWidgetItem(component.name))
        combo = QComboBox()
        for item_type in FunctionPointComponentType:
            combo.addItem(item_type.label, item_type)
        combo.setCurrentText(component.component_type.label)
        self._components.setCellWidget(row, 1, combo)
        self._components.setItem(row, 2, QTableWidgetItem(str(component.det_count)))
        self._components.setItem(row, 3, QTableWidgetItem(str(component.reference_count)))
        self._components.setItem(row, 4, QTableWidgetItem(component.notes))

    def _add_component_row(self) -> None:
        row = self._components.rowCount()
        self._components.insertRow(row)
        self._set_component_row(
            row,
            FunctionPointComponent(
                name="Новая функция",
                component_type=FunctionPointComponentType.EI,
                det_count=1,
                reference_count=1,
                notes="",
            ),
        )

    def _remove_selected_component_row(self) -> None:
        row = _selected_row(self._components)
        if row is None:
            QMessageBox.information(self, "Удаление", "Сначала выберите строку функции.")
            return
        self._components.removeRow(row)

    def _export_csv(self) -> None:
        payload = self.calculate()
        if payload is None:
            return
        directory = QFileDialog.getExistingDirectory(self, "Выберите каталог для экспорта FP")
        if not directory:
            return
        exported = self._export_service.export_function_points(directory, payload.project, payload.result, "function_points")
        names = ", ".join(Path(item.path).name for item in exported)
        QMessageBox.information(self, "Экспорт завершен", f"Созданы файлы: {names}")


class ApplicationCompositionTab(QWidget):
    def __init__(
        self,
        calculator: ApplicationCompositionCalculator,
        preset: Lab7VariantPreset,
        export_service: CsvExportService,
    ) -> None:
        super().__init__()
        self._calculator = calculator
        self._preset = preset
        self._export_service = export_service
        self._payload: ApplicationCompositionPayload | None = None

        self._items = QTableWidget()
        self._reuse_spin = QDoubleSpinBox()
        self._cost_spin = QDoubleSpinBox()
        self._productivity_combo = QComboBox()
        self._scale_widget = RatingSelectorWidget(SCALE_FACTOR_DEFINITIONS)
        self._summary = QPlainTextEdit()
        self._results = QTableWidget()
        self._build_ui()
        self.load_preset(preset)

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)

        controls = QWidget()
        controls_layout = QVBoxLayout(controls)

        items_box = QGroupBox("Объектные точки")
        items_layout = QVBoxLayout(items_box)
        self._items.setColumnCount(5)
        self._items.setHorizontalHeaderLabels(["Элемент", "Вид", "Сложность", "Количество", "Примечание"])
        self._items.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._items.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        items_layout.addWidget(self._items)
        item_buttons = QWidget()
        item_buttons_layout = QHBoxLayout(item_buttons)
        add_item_button = QPushButton("Добавить элемент")
        add_item_button.clicked.connect(self._add_item_row)
        remove_item_button = QPushButton("Удалить выбранный")
        remove_item_button.clicked.connect(self._remove_selected_item_row)
        item_buttons_layout.addWidget(add_item_button)
        item_buttons_layout.addWidget(remove_item_button)
        items_layout.addWidget(item_buttons)

        options_box = QGroupBox("Параметры модели композиции")
        options_form = QFormLayout(options_box)
        self._reuse_spin.setRange(0.0, 100.0)
        self._reuse_spin.setDecimals(2)
        self._reuse_spin.setSuffix(" %")
        self._cost_spin.setRange(0.0, 1_000_000_000.0)
        self._cost_spin.setDecimals(2)
        self._cost_spin.setSuffix(" за чел.-мес.")
        for level in ProductivityLevel:
            self._productivity_combo.addItem(f"{level.label} ({_format_float(level.productivity, 0)})", level)
        options_form.addRow("Повторное использование", self._reuse_spin)
        options_form.addRow("Продуктивность PROD", self._productivity_combo)
        options_form.addRow("Стоимость человеко-месяца", self._cost_spin)

        scale_box = QGroupBox("Показатели степени")
        scale_layout = QVBoxLayout(scale_box)
        scale_layout.addWidget(self._scale_widget)

        buttons = QWidget()
        buttons_layout = QHBoxLayout(buttons)
        calculate_button = QPushButton("Рассчитать модель композиции приложения")
        calculate_button.clicked.connect(self.calculate)
        preset_button = QPushButton("Восстановить исходный сценарий")
        preset_button.clicked.connect(lambda: self.load_preset(self._preset))
        export_button = QPushButton("Экспорт CSV")
        export_button.clicked.connect(self._export_csv)
        buttons_layout.addWidget(calculate_button)
        buttons_layout.addWidget(preset_button)
        buttons_layout.addWidget(export_button)

        controls_layout.addWidget(items_box, stretch=3)
        controls_layout.addWidget(options_box)
        controls_layout.addWidget(scale_box, stretch=2)
        controls_layout.addWidget(buttons)

        results = QWidget()
        results_layout = QVBoxLayout(results)
        self._summary.setReadOnly(True)
        self._summary.setPlaceholderText("Здесь появится сводка по расчету объектных точек.")
        self._results.setColumnCount(6)
        self._results.setHorizontalHeaderLabels(["Элемент", "Вид", "Сложность", "Вес", "Количество", "Итого OP"])
        self._results.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(QLabel("Сводка"))
        results_layout.addWidget(self._summary)
        results_layout.addWidget(QLabel("Детализация объектных точек"))
        results_layout.addWidget(self._results)

        root.addWidget(controls, stretch=3)
        root.addWidget(results, stretch=2)

    def load_preset(self, preset: Lab7VariantPreset) -> None:
        self._populate_items(preset.application_composition_project.items)
        self._reuse_spin.setValue(preset.application_composition_project.reuse_percent)
        self._cost_spin.setValue(
            0.0
            if preset.application_composition_project.cost_per_person_month is None
            else preset.application_composition_project.cost_per_person_month
        )
        self._scale_widget.set_ratings(preset.application_composition_project.scale_factor_ratings)
        index = self._productivity_combo.findText(
            f"{preset.application_composition_project.productivity_level.label} "
            f"({_format_float(preset.application_composition_project.productivity_level.productivity, 0)})"
        )
        if index >= 0:
            self._productivity_combo.setCurrentIndex(index)
        self.calculate()

    def calculate(self) -> ApplicationCompositionPayload | None:
        try:
            project = self._build_project()
            result = self._calculator.calculate(project)
            payload = ApplicationCompositionPayload(project=project, result=result)
            self._payload = payload
            self._render(payload)
            return payload
        except ValueError as error:
            QMessageBox.critical(self, "Ошибка расчета объектных точек", str(error))
            return None

    def current_payload(self) -> ApplicationCompositionPayload | None:
        return self._payload

    def _build_project(self) -> ApplicationCompositionProject:
        items: list[ObjectPointItem] = []
        for row in range(self._items.rowCount()):
            name_item = self._items.item(row, 0)
            count_item = self._items.item(row, 3)
            note_item = self._items.item(row, 4)
            kind_combo = self._items.cellWidget(row, 1)
            complexity_combo = self._items.cellWidget(row, 2)
            if not isinstance(kind_combo, QComboBox) or not isinstance(complexity_combo, QComboBox):
                raise ValueError("Не удалось прочитать строку объектных точек.")
            kind = kind_combo.currentData()
            complexity = complexity_combo.currentData()
            if not isinstance(kind, ObjectPointKind):
                raise ValueError("Нужно выбрать корректный вид объектной точки.")
            if name_item is None or not name_item.text().strip():
                raise ValueError(f"Строка {row + 1}: имя элемента не должно быть пустым.")
            if count_item is None:
                raise ValueError(f"Строка {row + 1}: отсутствует количество элементов.")
            items.append(
                ObjectPointItem(
                    name=name_item.text().strip(),
                    kind=kind,
                    complexity=complexity if isinstance(complexity, ObjectPointComplexity) else None,
                    count=_parse_int(_item_text(count_item), row=row + 1, field="Количество", minimum=0, allow_zero=False),
                    notes="" if note_item is None else note_item.text().strip(),
                )
            )

        productivity = self._productivity_combo.currentData()
        if not isinstance(productivity, ProductivityLevel):
            raise ValueError("Нужно выбрать корректный уровень продуктивности.")

        return ApplicationCompositionProject(
            items=tuple(items),
            reuse_percent=self._reuse_spin.value(),
            productivity_level=productivity,
            scale_factor_ratings=self._scale_widget.ratings(),
            cost_per_person_month=self._cost_spin.value() or None,
        )

    def _render(self, payload: ApplicationCompositionPayload) -> None:
        result = payload.result
        self._summary.setPlainText(
            "\n".join(
                [
                    f"Количество элементов: {len(payload.project.items)}",
                    f"Объектные точки: {_format_float(result.object_points)}",
                    f"Новые объектные точки (NOP): {_format_float(result.new_object_points)}",
                    f"Показатель степени p: {_format_float(result.exponent, 4)}",
                    f"PROD: {_format_float(payload.project.productivity_level.productivity, 0)}",
                    f"Трудоемкость модели композиции (PM): {_format_float(result.effort_person_months)}",
                    f"Срок модели композиции (мес.): {_format_float(result.time_months)}",
                    f"Средний размер команды: {_format_float(result.average_team_size)}",
                    "Предварительный бюджет: "
                    + ("не задан" if result.budget is None else _format_float(result.budget)),
                ]
            )
        )

        self._results.setRowCount(len(result.rated_items))
        for row, item in enumerate(result.rated_items):
            values = [
                item.item.name,
                item.item.kind.label,
                "-" if item.item.complexity is None else item.item.complexity.label,
                str(item.weight),
                str(item.item.count),
                str(item.points),
            ]
            for column, value in enumerate(values):
                self._results.setItem(row, column, QTableWidgetItem(value))
        self._results.resizeColumnsToContents()

    def _populate_items(self, items: tuple[ObjectPointItem, ...]) -> None:
        self._items.setRowCount(len(items))
        for row, item in enumerate(items):
            self._set_item_row(row, item)

    def _set_item_row(self, row: int, item: ObjectPointItem) -> None:
        self._items.setItem(row, 0, QTableWidgetItem(item.name))
        kind_combo = QComboBox()
        for kind in ObjectPointKind:
            kind_combo.addItem(kind.label, kind)
        kind_combo.setCurrentText(item.kind.label)
        self._items.setCellWidget(row, 1, kind_combo)

        complexity_combo = QComboBox()
        complexity_combo.addItem("-", None)
        for complexity in ObjectPointComplexity:
            complexity_combo.addItem(complexity.label, complexity)
        if item.complexity is None:
            complexity_combo.setCurrentIndex(0)
        else:
            complexity_combo.setCurrentText(item.complexity.label)
        self._items.setCellWidget(row, 2, complexity_combo)

        self._items.setItem(row, 3, QTableWidgetItem(str(item.count)))
        self._items.setItem(row, 4, QTableWidgetItem(item.notes))

    def _add_item_row(self) -> None:
        row = self._items.rowCount()
        self._items.insertRow(row)
        self._set_item_row(
            row,
            ObjectPointItem(
                name="Новый элемент",
                kind=ObjectPointKind.SCREEN,
                complexity=ObjectPointComplexity.SIMPLE,
                count=1,
                notes="",
            ),
        )

    def _remove_selected_item_row(self) -> None:
        row = _selected_row(self._items)
        if row is None:
            QMessageBox.information(self, "Удаление", "Сначала выберите строку объектной точки.")
            return
        self._items.removeRow(row)

    def _export_csv(self) -> None:
        payload = self.calculate()
        if payload is None:
            return
        directory = QFileDialog.getExistingDirectory(
            self,
            "Выберите каталог для экспорта модели композиции приложения",
        )
        if not directory:
            return
        exported = self._export_service.export_application_composition(
            directory,
            payload.project,
            payload.result,
            "application_composition",
        )
        names = ", ".join(Path(item.path).name for item in exported)
        QMessageBox.information(self, "Экспорт завершен", f"Созданы файлы: {names}")


class RatingSelectorWidget(QWidget):
    def __init__(self, definitions) -> None:
        super().__init__()
        self._combos: dict[str, QComboBox] = {}
        self._definitions = tuple(definitions)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        grid = QGridLayout(content)
        grid.setColumnStretch(1, 1)

        for row, definition in enumerate(self._definitions):
            label = QLabel(f"{definition.identifier} - {definition.title}")
            combo = QComboBox()
            for rating in definition.values:
                combo.addItem(rating.label, rating)
            self._combos[definition.identifier] = combo
            grid.addWidget(label, row, 0)
            grid.addWidget(combo, row, 1)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def ratings(self) -> dict[str, Rating]:
        values: dict[str, Rating] = {}
        for identifier, combo in self._combos.items():
            rating = combo.currentData()
            if isinstance(rating, Rating):
                values[identifier] = rating
        return values

    def set_ratings(self, values: dict[str, Rating]) -> None:
        for identifier, rating in values.items():
            combo = self._combos.get(identifier)
            if combo is None:
                continue
            index = combo.findText(rating.label)
            if index >= 0:
                combo.setCurrentIndex(index)


class EarlyDesignTab(QWidget):
    def __init__(
        self,
        fp_tab: FunctionPointTab,
        calculator: EarlyDesignCalculator,
        backfiring_service: SizeBackfiringService,
        preset: Lab7VariantPreset,
        export_service: CsvExportService,
    ) -> None:
        super().__init__()
        self._fp_tab = fp_tab
        self._calculator = calculator
        self._backfiring_service = backfiring_service
        self._preset = preset
        self._export_service = export_service
        self._payload: EarlyDesignPayload | None = None

        self._cost_spin = QDoubleSpinBox()
        self._languages = QTableWidget()
        self._scale_widget = RatingSelectorWidget(SCALE_FACTOR_DEFINITIONS)
        self._multiplier_widget = RatingSelectorWidget(EFFORT_MULTIPLIER_DEFINITIONS)
        self._summary = QPlainTextEdit()
        self._backfiring_table = QTableWidget()
        self._factors_table = QTableWidget()
        self._build_ui()
        self.load_preset(preset)

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)

        controls = QWidget()
        controls_layout = QVBoxLayout(controls)

        sizing_box = QGroupBox("Размер проекта и бюджет")
        sizing_form = QFormLayout(sizing_box)
        self._cost_spin.setRange(0.0, 1_000_000_000.0)
        self._cost_spin.setDecimals(2)
        self._cost_spin.setSuffix(" за чел.-мес.")
        self._languages.setColumnCount(3)
        self._languages.setHorizontalHeaderLabels(["Язык", "Доля, %", "LOC / FP"])
        self._languages.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        sizing_form.addRow("Стоимость человеко-месяца", self._cost_spin)
        sizing_form.addRow(self._languages)

        language_buttons = QWidget()
        language_buttons_layout = QHBoxLayout(language_buttons)
        add_language_button = QPushButton("Добавить язык")
        add_language_button.clicked.connect(self._add_language_row)
        remove_language_button = QPushButton("Удалить выбранный")
        remove_language_button.clicked.connect(self._remove_selected_language_row)
        language_buttons_layout.addWidget(add_language_button)
        language_buttons_layout.addWidget(remove_language_button)
        sizing_form.addRow(language_buttons)

        scale_box = QGroupBox("Показатели степени")
        scale_layout = QVBoxLayout(scale_box)
        scale_layout.addWidget(self._scale_widget)

        multiplier_box = QGroupBox("Множители трудоемкости")
        multiplier_layout = QVBoxLayout(multiplier_box)
        multiplier_layout.addWidget(self._multiplier_widget)

        buttons = QWidget()
        buttons_layout = QHBoxLayout(buttons)
        calculate_button = QPushButton("Рассчитать модель ранней разработки архитектуры")
        calculate_button.clicked.connect(self.calculate)
        preset_button = QPushButton("Восстановить исходный сценарий")
        preset_button.clicked.connect(lambda: self.load_preset(self._preset))
        export_button = QPushButton("Экспорт CSV")
        export_button.clicked.connect(self._export_csv)
        buttons_layout.addWidget(calculate_button)
        buttons_layout.addWidget(preset_button)
        buttons_layout.addWidget(export_button)

        controls_layout.addWidget(sizing_box)
        controls_layout.addWidget(scale_box, stretch=1)
        controls_layout.addWidget(multiplier_box, stretch=1)
        controls_layout.addWidget(buttons)

        results = QWidget()
        results_layout = QVBoxLayout(results)
        self._summary.setReadOnly(True)
        self._summary.setPlaceholderText("Здесь появится сводка по модели ранней разработки архитектуры.")
        self._backfiring_table.setColumnCount(4)
        self._backfiring_table.setHorizontalHeaderLabels(["Язык", "Доля, %", "LOC / FP", "Вклад, KLOC"])
        self._backfiring_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._factors_table.setColumnCount(4)
        self._factors_table.setHorizontalHeaderLabels(["Группа", "ID", "Уровень", "Значение"])
        self._factors_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        results_layout.addWidget(QLabel("Сводка"))
        results_layout.addWidget(self._summary)
        results_layout.addWidget(QLabel("Backfiring FP -> KLOC"))
        results_layout.addWidget(self._backfiring_table)
        results_layout.addWidget(QLabel("Использованные факторы"))
        results_layout.addWidget(self._factors_table)

        root.addWidget(controls, stretch=3)
        root.addWidget(results, stretch=2)

    def load_preset(self, preset: Lab7VariantPreset) -> None:
        self._cost_spin.setValue(0.0 if preset.early_design_project is None or preset.early_design_project.cost_per_person_month is None else preset.early_design_project.cost_per_person_month)
        self._populate_languages(preset.backfiring_project.language_mix)
        reference_project = preset.early_design_project
        if reference_project is None:
            # Use explicit ratings from the documented variant even if size is unresolved.
            reference_project = EarlyDesignProject(
                size=1.0,
                scale_factor_ratings={
                    "PREC": Rating.NOMINAL,
                    "FLEX": Rating.HIGH,
                    "RESL": Rating.LOW,
                    "TEAM": Rating.HIGH,
                    "PMAT": Rating.LOW,
                },
                effort_multiplier_ratings={
                    "PERS": Rating.NOMINAL,
                    "RCPX": Rating.VERY_HIGH,
                    "RUSE": Rating.LOW,
                    "PDIF": Rating.HIGH,
                    "PREX": Rating.LOW,
                    "FCIL": Rating.VERY_HIGH,
                    "SCED": Rating.VERY_LOW,
                },
            )
        self._scale_widget.set_ratings(reference_project.scale_factor_ratings)
        self._multiplier_widget.set_ratings(reference_project.effort_multiplier_ratings)
        self.calculate()

    def calculate(self) -> EarlyDesignPayload | None:
        try:
            fp_payload = self._fp_tab.calculate()
            if fp_payload is None:
                raise ValueError("Сначала нужен корректный расчет функциональных точек.")
            backfiring_project = self._build_backfiring_project()
            backfiring_result = self._backfiring_service.estimate(fp_payload.result.adjusted_points, backfiring_project)

            early_project: EarlyDesignProject | None = None
            early_result: EarlyDesignResult | None = None
            if backfiring_result.estimated_kloc is not None:
                early_project = EarlyDesignProject(
                    size=backfiring_result.estimated_kloc,
                    scale_factor_ratings=self._scale_widget.ratings(),
                    effort_multiplier_ratings=self._multiplier_widget.ratings(),
                    cost_per_person_month=self._cost_spin.value() or None,
                )
                early_result = self._calculator.estimate(early_project)

            payload = EarlyDesignPayload(
                function_point_result=fp_payload.result,
                backfiring_project=backfiring_project,
                backfiring_result=backfiring_result,
                early_design_project=early_project,
                early_design_result=early_result,
            )
            self._payload = payload
            self._render(payload)
            return payload
        except ValueError as error:
            QMessageBox.critical(self, "Ошибка расчета модели ранней разработки архитектуры", str(error))
            return None

    def current_payload(self) -> EarlyDesignPayload | None:
        return self._payload

    def _build_backfiring_project(self) -> BackfiringProject:
        items: list[LanguageFootprint] = []
        for row in range(self._languages.rowCount()):
            language_item = self._languages.item(row, 0)
            share_item = self._languages.item(row, 1)
            loc_item = self._languages.item(row, 2)
            if language_item is None or share_item is None:
                raise ValueError("Таблица языков заполнена некорректно.")
            language_name = language_item.text().strip()
            if not language_name:
                raise ValueError(f"Строка {row + 1}: имя языка не должно быть пустым.")
            loc_text = "" if loc_item is None else loc_item.text().strip()
            if not loc_text:
                loc_per_fp = None
            else:
                loc_per_fp = _parse_float(loc_text, row=row + 1, field="LOC / FP", minimum=0.0, strict_min=True)
            items.append(
                LanguageFootprint(
                    language=language_name,
                    percentage=_parse_float(_item_text(share_item), row=row + 1, field="Доля, %", minimum=0.0, strict_min=True),
                    loc_per_fp=loc_per_fp,
                )
            )
        return BackfiringProject(language_mix=tuple(items))

    def _render(self, payload: EarlyDesignPayload) -> None:
        backfiring = payload.backfiring_result
        lines = [
            f"FP из вкладки Function Point: {_format_float(payload.function_point_result.adjusted_points)}",
            f"Покрытая доля backfiring: {_format_float(backfiring.known_share_percent, 0)} %",
            f"Частичный размер по известной доле: {_format_float(backfiring.partial_kloc_from_known_share, 3)} KLOC",
        ]
        sql_item = next((item for item in payload.backfiring_project.language_mix if item.language.upper() == "SQL"), None)
        if sql_item is not None and sql_item.loc_per_fp is not None:
            lines.append(f"Принятое значение SQL LOC/FP: {_format_float(sql_item.loc_per_fp, 0)}")
        if backfiring.estimated_kloc is None or payload.early_design_result is None or payload.early_design_project is None:
            lines.extend(
                [
                    "Полный расчет модели ранней разработки архитектуры пока не завершен.",
                    "Нужно задать LOC/FP для всех языков смеси, включая SQL.",
                ]
            )
        else:
            result = payload.early_design_result
            lines.extend(
                [
                    f"Полный размер: {_format_float(payload.early_design_project.size, 3)} KLOC",
                    f"Показатель степени p: {_format_float(result.exponent, 4)}",
                    f"EArch: {_format_float(result.effort_adjustment_factor, 4)}",
                    f"Трудоемкость (PM): {_format_float(result.effort_person_months)}",
                    f"Срок разработки (мес.): {_format_float(result.time_months)}",
                    f"Средняя численность команды: {_format_float(result.average_team_size)}",
                    "Предварительный бюджет: "
                    + ("не задан" if result.budget is None else _format_float(result.budget)),
                ]
            )
        self._summary.setPlainText("\n".join(lines))

        self._backfiring_table.setRowCount(len(payload.backfiring_project.language_mix))
        for row, item in enumerate(payload.backfiring_project.language_mix):
            contribution = 0.0 if item.loc_per_fp is None else payload.function_point_result.adjusted_points * item.percentage * item.loc_per_fp / 100000.0
            values = [
                item.language,
                _format_float(item.percentage, 0),
                "-" if item.loc_per_fp is None else _format_float(item.loc_per_fp, 0),
                _format_float(contribution, 3),
            ]
            for column, value in enumerate(values):
                self._backfiring_table.setItem(row, column, QTableWidgetItem(value))
        self._backfiring_table.resizeColumnsToContents()

        factor_rows = []
        for definition in SCALE_FACTOR_DEFINITIONS:
            rating = self._scale_widget.ratings()[definition.identifier]
            factor_rows.append(("Scale", definition.identifier, rating.label, _format_float(definition.value_for(rating), 2)))
        for definition in EFFORT_MULTIPLIER_DEFINITIONS:
            rating = self._multiplier_widget.ratings()[definition.identifier]
            factor_rows.append(
                ("Multiplier", definition.identifier, rating.label, _format_float(definition.value_for(rating), 2))
            )

        self._factors_table.setRowCount(len(factor_rows))
        for row, values in enumerate(factor_rows):
            for column, value in enumerate(values):
                self._factors_table.setItem(row, column, QTableWidgetItem(value))
        self._factors_table.resizeColumnsToContents()

    def _populate_languages(self, items: tuple[LanguageFootprint, ...]) -> None:
        self._languages.setRowCount(len(items))
        for row, item in enumerate(items):
            self._set_language_row(row, item)

    def _set_language_row(self, row: int, item: LanguageFootprint) -> None:
        self._languages.setItem(row, 0, QTableWidgetItem(item.language))
        self._languages.setItem(row, 1, QTableWidgetItem(_format_float(item.percentage, 0)))
        self._languages.setItem(row, 2, QTableWidgetItem("" if item.loc_per_fp is None else _format_float(item.loc_per_fp, 0)))

    def _add_language_row(self) -> None:
        row = self._languages.rowCount()
        self._languages.insertRow(row)
        self._set_language_row(row, LanguageFootprint(language="Новый язык", percentage=1.0, loc_per_fp=53.0))

    def _remove_selected_language_row(self) -> None:
        row = _selected_row(self._languages)
        if row is None:
            QMessageBox.information(self, "Удаление", "Сначала выберите строку языка.")
            return
        self._languages.removeRow(row)

    def _export_csv(self) -> None:
        payload = self.calculate()
        if payload is None:
            return
        directory = QFileDialog.getExistingDirectory(
            self,
            "Выберите каталог для экспорта модели ранней разработки архитектуры",
        )
        if not directory:
            return
        exported = self._export_service.export_early_design(directory, payload, "early_design")
        names = ", ".join(Path(item.path).name for item in exported)
        QMessageBox.information(self, "Экспорт завершен", f"Созданы файлы: {names}")


class SummaryTab(QWidget):
    def __init__(
        self,
        fp_tab: FunctionPointTab,
        application_tab: ApplicationCompositionTab,
        early_tab: EarlyDesignTab,
        export_service: CsvExportService,
    ) -> None:
        super().__init__()
        self._fp_tab = fp_tab
        self._application_tab = application_tab
        self._early_tab = early_tab
        self._export_service = export_service

        self._summary = QPlainTextEdit()
        self._assumptions = QPlainTextEdit()
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        buttons = QWidget()
        buttons_layout = QHBoxLayout(buttons)
        refresh_button = QPushButton("Обновить сводку")
        refresh_button.clicked.connect(self.refresh)
        export_button = QPushButton("Экспорт всего набора")
        export_button.clicked.connect(self._export_all)
        buttons_layout.addWidget(refresh_button)
        buttons_layout.addWidget(export_button)

        self._summary.setReadOnly(True)
        self._assumptions.setReadOnly(True)

        layout.addWidget(buttons)
        layout.addWidget(QLabel("Интегрированная сводка"))
        layout.addWidget(self._summary)
        layout.addWidget(QLabel("Рабочие допущения"))
        layout.addWidget(self._assumptions)

    def refresh(self) -> None:
        fp_payload = self._fp_tab.calculate()
        app_payload = self._application_tab.calculate()
        early_payload = self._early_tab.calculate()

        lines = ["Мобильное приложение брокерской системы", ""]
        if fp_payload is not None:
            lines.append(f"FP: {_format_float(fp_payload.result.adjusted_points)}")
        if app_payload is not None:
            lines.append(f"Объектные точки: {_format_float(app_payload.result.object_points)}")
            lines.append(
                f"Трудоемкость по модели композиции приложения: {_format_float(app_payload.result.effort_person_months)}"
            )
            lines.append(f"Срок по модели композиции приложения: {_format_float(app_payload.result.time_months)}")
            lines.append(
                f"Средний размер команды по модели композиции приложения: {_format_float(app_payload.result.average_team_size)}"
            )
            if app_payload.result.budget is not None:
                lines.append(f"Бюджет по модели композиции приложения: {_format_float(app_payload.result.budget)}")
        if early_payload is not None:
            lines.append(
                f"Backfiring covered share: {_format_float(early_payload.backfiring_result.known_share_percent, 0)} %"
            )
            if early_payload.early_design_result is None:
                lines.append("Модель ранней разработки архитектуры: ожидает полного набора LOC/FP по языкам.")
            else:
                sql_item = next(
                    (item for item in early_payload.backfiring_project.language_mix if item.language.upper() == "SQL"),
                    None,
                )
                if sql_item is not None and sql_item.loc_per_fp is not None:
                    lines.append(f"SQL LOC/FP: {_format_float(sql_item.loc_per_fp, 0)}")
                lines.append(
                    f"KLOC для модели ранней разработки архитектуры: {_format_float(early_payload.early_design_project.size, 3)}"
                )
                lines.append(
                    f"Трудоемкость по модели ранней разработки архитектуры: {_format_float(early_payload.early_design_result.effort_person_months)}"
                )
                lines.append(
                    f"Срок по модели ранней разработки архитектуры: {_format_float(early_payload.early_design_result.time_months)}"
                )
                lines.append(f"Средний размер команды: {_format_float(early_payload.early_design_result.average_team_size)}")
        self._summary.setPlainText("\n".join(lines))

        assumptions = [
            "1. FP и объектные точки предзаполнены для исходного сценария брокерского мобильного приложения, но остаются редактируемыми.",
            "2. Модель ранней разработки архитектуры использует размер, рассчитанный через backfiring FP -> KLOC.",
            "3. Для SQL по умолчанию используется LOC/FP = 53 как явное и редактируемое экспертное допущение.",
            "4. Если пользователь очищает LOC/FP хотя бы для одного языка смеси, модель ранней разработки архитектуры не закрывается автоматически.",
            "5. Значения scale factors и effort multipliers взяты из текстового описания исходного сценария.",
        ]
        self._assumptions.setPlainText("\n".join(assumptions))

    def _export_all(self) -> None:
        fp_payload = self._fp_tab.calculate()
        app_payload = self._application_tab.calculate()
        early_payload = self._early_tab.calculate()
        if fp_payload is None or app_payload is None or early_payload is None:
            return
        directory = QFileDialog.getExistingDirectory(self, "Выберите каталог для полного экспорта")
        if not directory:
            return
        exported = []
        exported.extend(self._export_service.export_function_points(directory, fp_payload.project, fp_payload.result, "function_points"))
        exported.extend(
            self._export_service.export_application_composition(
                directory,
                app_payload.project,
                app_payload.result,
                "application_composition",
            )
        )
        exported.extend(self._export_service.export_early_design(directory, early_payload, "early_design"))
        names = ", ".join(Path(item.path).name for item in exported)
        QMessageBox.information(self, "Экспорт завершен", f"Созданы файлы: {names}")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"Калькулятор COCOMO II ЛР №7 [{QT_BINDING}]")
        self.resize(1520, 920)

        preset = build_variant_2_preset()
        fp_calculator = FunctionPointCalculator()
        application_calculator = ApplicationCompositionCalculator()
        early_calculator = EarlyDesignCalculator()
        backfiring_service = SizeBackfiringService()
        exporter = CsvExportService()

        tabs = QTabWidget()
        self._fp_tab = FunctionPointTab(fp_calculator, preset, exporter)
        self._application_tab = ApplicationCompositionTab(application_calculator, preset, exporter)
        self._early_tab = EarlyDesignTab(self._fp_tab, early_calculator, backfiring_service, preset, exporter)
        self._summary_tab = SummaryTab(self._fp_tab, self._application_tab, self._early_tab, exporter)

        tabs.addTab(self._fp_tab, "Функциональные точки")
        tabs.addTab(self._application_tab, "Модель композиции приложения")
        tabs.addTab(self._early_tab, "Модель ранней разработки архитектуры")
        tabs.addTab(self._summary_tab, "Сводка")
        self.setCentralWidget(tabs)


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(
        """
        QWidget { font-size: 13px; }
        QGroupBox { font-weight: 600; margin-top: 12px; }
        QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
        QPlainTextEdit { background: #fafaf7; }
        QTableWidget { background: white; gridline-color: #d0d0d0; }
        QPushButton {
            background: #1b4d3e;
            color: white;
            border: none;
            padding: 8px 14px;
            border-radius: 6px;
        }
        QPushButton:hover { background: #255f4d; }
        """
    )
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

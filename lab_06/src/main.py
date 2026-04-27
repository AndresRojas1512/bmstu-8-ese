from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in {None, ""}:
    from charts import StaffingChartCanvas, Variant3ChartsCanvas
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
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QPlainTextEdit,
        QScrollArea,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
        QT_BINDING,
    )

    from cocomo import (
        COCOMOCalculator,
        COST_DRIVERS,
        COST_DRIVER_MAP,
        DistributionBundle,
        DistributionService,
        ProjectEstimate,
        ProjectMode,
        ProjectProfile,
        Rating,
        Variant3AnalysisResult,
        Variant3AnalysisService,
    )
else:
    from .charts import StaffingChartCanvas, Variant3ChartsCanvas
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
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QPlainTextEdit,
        QScrollArea,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
        QT_BINDING,
    )

    from .cocomo import (
        COCOMOCalculator,
        COST_DRIVERS,
        COST_DRIVER_MAP,
        DistributionBundle,
        DistributionService,
        ProjectEstimate,
        ProjectMode,
        ProjectProfile,
        Rating,
        Variant3AnalysisResult,
        Variant3AnalysisService,
    )


def _format_float(value: float) -> str:
    return f"{value:.2f}"


@dataclass(slots=True)
class ReportPayload:
    estimate: ProjectEstimate
    distributions: DistributionBundle

    @property
    def total_budget(self) -> float | None:
        cost = self.estimate.profile.cost_per_person_month
        if cost is None or cost == 0:
            return None
        return self.distributions.total_effort_pm * cost


class DriverSelectorWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._combos: dict[str, QComboBox] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        grid = QGridLayout(content)
        grid.setColumnStretch(1, 1)

        row = 0
        for driver in COST_DRIVERS:
            label = QLabel(f"{driver.identifier} - {driver.title}")
            combo = QComboBox()
            for rating in driver.ratings:
                combo.addItem(rating.label, rating)
            combo.setCurrentText(driver.default_rating.label)
            self._combos[driver.identifier] = combo
            grid.addWidget(label, row, 0)
            grid.addWidget(combo, row, 1)
            row += 1

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

    def ratings(self) -> dict[str, Rating]:
        ratings: dict[str, Rating] = {}
        for driver_id, combo in self._combos.items():
            rating = combo.currentData()
            if isinstance(rating, Rating):
                ratings[driver_id] = rating
        return ratings

    def set_ratings(self, ratings: dict[str, Rating]) -> None:
        for driver_id, rating in ratings.items():
            combo = self._combos.get(driver_id)
            if combo is None:
                continue
            index = combo.findText(rating.label)
            if index >= 0:
                combo.setCurrentIndex(index)


class EstimateResultsWidget(QWidget):
    def __init__(
        self,
        export_service: CsvExportService,
        export_stem: str,
    ) -> None:
        super().__init__()
        self._export_service = export_service
        self._export_stem = export_stem
        self._current_payload: ReportPayload | None = None
        self._summary = QPlainTextEdit()
        self._staffing_note = QPlainTextEdit()
        self._staffing_plan = QTableWidget()
        self._phases = QTableWidget()
        self._wbs = QTableWidget()
        self._staffing_chart = StaffingChartCanvas()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._summary.setReadOnly(True)
        self._summary.setPlaceholderText("Здесь появится сводка по расчету.")

        self._staffing_note.setReadOnly(True)
        self._staffing_note.setPlaceholderText("Здесь появится рекомендация по комплектованию команды.")

        self._staffing_plan.setColumnCount(5)
        self._staffing_plan.setHorizontalHeaderLabels(
            ["Этап", "Начало, мес.", "Конец, мес.", "Средняя загрузка", "Рекомендуемая команда"]
        )

        self._phases.setColumnCount(5)
        self._phases.setHorizontalHeaderLabels(
            ["Этап", "Трудоемкость, %", "Время, %", "Трудоемкость, чел.-мес.", "Средняя загрузка"]
        )

        self._wbs.setColumnCount(3)
        self._wbs.setHorizontalHeaderLabels(["Вид работ WBS", "Трудоемкость, %", "Трудоемкость, чел.-мес."])

        export_button = QPushButton("Экспорт CSV")
        export_button.clicked.connect(self._export_csv)

        layout.addWidget(QLabel("Сводка"))
        layout.addWidget(self._summary)
        layout.addWidget(QLabel("Профиль привлечения сотрудников"))
        layout.addWidget(self._staffing_note)
        layout.addWidget(self._staffing_chart)
        layout.addWidget(QLabel("План комплектования команды"))
        layout.addWidget(self._staffing_plan)
        layout.addWidget(export_button)
        layout.addWidget(QLabel("Распределение по стадиям жизненного цикла"))
        layout.addWidget(self._phases)
        layout.addWidget(QLabel("Распределение по видам деятельности WBS"))
        layout.addWidget(self._wbs)

    def set_payload(self, payload: ReportPayload) -> None:
        self._current_payload = payload
        estimate = payload.estimate
        distributions = payload.distributions
        budget_line = (
            f"Предварительный бюджет: {_format_float(payload.total_budget)}"
            if payload.total_budget is not None
            else "Предварительный бюджет: не задан"
        )

        summary_lines = [
            f"Режим проекта: {estimate.profile.mode.label}",
            f"KLOC: {_format_float(estimate.profile.kloc)}",
            f"EAF: {_format_float(estimate.eaf)}",
            f"Трудоемкость разработки (чел.-мес.): {_format_float(estimate.development_effort_pm)}",
            f"Срок разработки (мес.): {_format_float(estimate.development_time_months)}",
            f"Средний размер команды: {_format_float(estimate.average_team_size)}",
            f"Полная трудоемкость с учетом планирования: {_format_float(distributions.total_effort_pm)}",
            f"Полная длительность с учетом планирования: {_format_float(distributions.total_time_months)}",
            budget_line,
        ]
        self._summary.setPlainText("\n".join(summary_lines))
        self._staffing_note.setPlainText(distributions.staffing_strategy_note)
        self._staffing_chart.plot_distribution(distributions)

        self._staffing_plan.setRowCount(len(distributions.staffing_segments))
        for row_index, segment in enumerate(distributions.staffing_segments):
            values = [
                segment.phase_name,
                _format_float(segment.start_month),
                _format_float(segment.end_month),
                _format_float(segment.average_staffing),
                str(segment.recommended_headcount),
            ]
            for column_index, value in enumerate(values):
                self._staffing_plan.setItem(row_index, column_index, QTableWidgetItem(value))
        self._staffing_plan.resizeColumnsToContents()

        self._phases.setRowCount(len(distributions.phases))
        for row_index, phase in enumerate(distributions.phases):
            values = [
                phase.name,
                _format_float(phase.effort_percent),
                _format_float(phase.duration_percent),
                _format_float(phase.effort_pm),
                _format_float(phase.average_staffing),
            ]
            for column_index, value in enumerate(values):
                self._phases.setItem(row_index, column_index, QTableWidgetItem(value))
        self._phases.resizeColumnsToContents()

        self._wbs.setRowCount(len(distributions.wbs_items))
        for row_index, item in enumerate(distributions.wbs_items):
            values = [item.name, _format_float(item.effort_percent), _format_float(item.effort_pm)]
            for column_index, value in enumerate(values):
                self._wbs.setItem(row_index, column_index, QTableWidgetItem(value))
        self._wbs.resizeColumnsToContents()

    def _export_csv(self) -> None:
        if self._current_payload is None:
            QMessageBox.information(self, "Экспорт", "Пока нет результатов для экспорта.")
            return

        directory = QFileDialog.getExistingDirectory(self, "Выберите каталог для экспорта")
        if not directory:
            return

        exported = self._export_service.export_estimate(
            directory=directory,
            estimate=self._current_payload.estimate,
            distributions=self._current_payload.distributions,
            stem=self._export_stem,
            total_budget=self._current_payload.total_budget,
        )
        exported_names = ", ".join(Path(item.path).name for item in exported)
        QMessageBox.information(self, "Экспорт завершен", f"Созданы файлы: {exported_names}")


class CalculatorTab(QWidget):
    def __init__(
        self,
        calculator: COCOMOCalculator,
        distribution_service: DistributionService,
        export_service: CsvExportService,
    ) -> None:
        super().__init__()
        self._calculator = calculator
        self._distribution_service = distribution_service

        self._mode_combo = QComboBox()
        self._kloc_spin = QDoubleSpinBox()
        self._cost_spin = QDoubleSpinBox()
        self._drivers = DriverSelectorWidget()
        self._results = EstimateResultsWidget(export_service=export_service, export_stem="calculator")

        self._build_ui()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)

        controls = QWidget()
        controls_layout = QVBoxLayout(controls)

        form_box = QGroupBox("Параметры проекта")
        form = QFormLayout(form_box)

        for mode in ProjectMode:
            self._mode_combo.addItem(mode.label, mode)

        self._kloc_spin.setRange(0.1, 100000.0)
        self._kloc_spin.setDecimals(2)
        self._kloc_spin.setValue(100.0)

        self._cost_spin.setRange(0.0, 1_000_000_000.0)
        self._cost_spin.setDecimals(2)
        self._cost_spin.setValue(0.0)
        self._cost_spin.setSuffix(" за чел.-мес.")

        form.addRow("Режим", self._mode_combo)
        form.addRow("KLOC", self._kloc_spin)
        form.addRow("Стоимость человеко-месяца", self._cost_spin)

        button = QPushButton("Рассчитать проект")
        button.clicked.connect(self._calculate)

        controls_layout.addWidget(form_box)
        controls_layout.addWidget(QLabel("Драйверы затрат"))
        controls_layout.addWidget(self._drivers, stretch=1)
        controls_layout.addWidget(button)

        root.addWidget(controls, stretch=2)
        root.addWidget(self._results, stretch=3)

    def load_profile(self, profile: ProjectProfile) -> None:
        index = self._mode_combo.findText(profile.mode.label)
        if index >= 0:
            self._mode_combo.setCurrentIndex(index)
        self._kloc_spin.setValue(profile.kloc)
        self._cost_spin.setValue(profile.cost_per_person_month or 0.0)
        self._drivers.set_ratings(profile.driver_ratings)
        self._calculate()

    def _calculate(self) -> None:
        try:
            mode = self._mode_combo.currentData()
            if not isinstance(mode, ProjectMode):
                raise ValueError("Нужно выбрать корректный режим проекта.")
            cost = self._cost_spin.value()
            profile = ProjectProfile(
                mode=mode,
                kloc=self._kloc_spin.value(),
                driver_ratings=self._drivers.ratings(),
                cost_per_person_month=cost if cost > 0 else None,
            )
            estimate = self._calculator.estimate(profile)
            distributions = self._distribution_service.build(estimate)
            self._results.set_payload(ReportPayload(estimate=estimate, distributions=distributions))
        except ValueError as error:
            QMessageBox.critical(self, "Ошибка расчета", str(error))


class Variant3AnalysisTab(QWidget):
    def __init__(
        self,
        analysis_service: Variant3AnalysisService,
        export_service: CsvExportService,
    ) -> None:
        super().__init__()
        self._analysis_service = analysis_service
        self._export_service = export_service
        self._current_result: Variant3AnalysisResult | None = None

        self._kloc_spin = QDoubleSpinBox()
        self._comparison_combo = QComboBox()
        self._summary = QPlainTextEdit()
        self._charts = Variant3ChartsCanvas()
        self._nominal_table = QTableWidget()
        self._comparison_table = QTableWidget()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        controls_box = QGroupBox("Параметры анализа чувствительности")
        controls = QFormLayout(controls_box)

        self._kloc_spin.setRange(0.1, 100000.0)
        self._kloc_spin.setDecimals(2)
        self._kloc_spin.setValue(100.0)

        sced_driver = COST_DRIVER_MAP["SCED"]
        for rating in sced_driver.ratings:
            self._comparison_combo.addItem(rating.label, rating)
        self._comparison_combo.setCurrentText(Rating.VERY_LOW.label)

        controls.addRow("Фиксированный KLOC", self._kloc_spin)
        controls.addRow("Сжатый график", self._comparison_combo)

        analyze_button = QPushButton("Запустить анализ драйверов")
        analyze_button.clicked.connect(self._analyze)

        export_button = QPushButton("Экспорт CSV")
        export_button.clicked.connect(self._export_csv)

        self._summary.setReadOnly(True)

        for table in (self._nominal_table, self._comparison_table):
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels(
                ["Драйвер", "Уровень", "EAF", "PM", "TM", "Отклонение от min PM, %"]
            )

        layout.addWidget(controls_box)
        layout.addWidget(analyze_button)
        layout.addWidget(export_button)
        layout.addWidget(QLabel("Сводка"))
        layout.addWidget(self._summary)
        layout.addWidget(QLabel("Графики"))
        layout.addWidget(self._charts)
        layout.addWidget(QLabel("Базовый график"))
        layout.addWidget(self._nominal_table)
        layout.addWidget(QLabel("Сжатый график"))
        layout.addWidget(self._comparison_table)

    def _analyze(self) -> None:
        try:
            comparison = self._comparison_combo.currentData()
            if not isinstance(comparison, Rating):
                raise ValueError("Нужно выбрать корректный уровень параметра SCED.")

            result = self._analysis_service.analyze(
                kloc=self._kloc_spin.value(),
                nominal_sced=Rating.NOMINAL,
                comparison_sced=comparison,
            )
            self._populate(result)
        except ValueError as error:
            QMessageBox.critical(self, "Ошибка анализа", str(error))

    def _populate(self, result: Variant3AnalysisResult) -> None:
        self._current_result = result
        summary_lines = [
            f"Базовый график: {result.nominal_sced.label}",
            f"Сжатый график: {result.comparison_sced.label}",
            f"Наибольшее влияние на PM при базовом графике: {result.top_effort_driver_nominal}",
            f"Наибольшее влияние на TM при базовом графике: {result.top_time_driver_nominal}",
            f"Наибольшее влияние на PM при сжатом графике: {result.top_effort_driver_comparison}",
            f"Наибольшее влияние на TM при сжатом графике: {result.top_time_driver_comparison}",
        ]
        self._summary.setPlainText("\n".join(summary_lines))
        self._charts.plot_analysis(result)
        self._fill_sweep_table(self._nominal_table, result.nominal_sweeps)
        self._fill_sweep_table(self._comparison_table, result.comparison_sweeps)

    def _export_csv(self) -> None:
        if self._current_result is None:
            QMessageBox.information(self, "Экспорт", "Сначала выполните анализ.")
            return

        directory = QFileDialog.getExistingDirectory(self, "Выберите каталог для экспорта")
        if not directory:
            return

        exported = self._export_service.export_variant3_analysis(
            directory=directory,
            analysis=self._current_result,
            stem="variant3_analysis",
        )
        exported_names = ", ".join(Path(item.path).name for item in exported)
        QMessageBox.information(self, "Экспорт завершен", f"Созданы файлы: {exported_names}")

    @staticmethod
    def _fill_sweep_table(table: QTableWidget, sweeps) -> None:
        rows_count = sum(len(sweep.rows) for sweep in sweeps)
        table.setRowCount(rows_count)

        row_index = 0
        for sweep in sweeps:
            min_pm = min(item.effort_pm for item in sweep.rows)
            for item in sweep.rows:
                delta_percent = 0.0 if min_pm == 0 else (item.effort_pm - min_pm) / min_pm * 100.0
                values = [
                    item.driver_id,
                    item.rating.label,
                    _format_float(item.eaf),
                    _format_float(item.effort_pm),
                    _format_float(item.time_months),
                    _format_float(delta_percent),
                ]
                for column_index, value in enumerate(values):
                    table.setItem(row_index, column_index, QTableWidgetItem(value))
                row_index += 1
        table.resizeColumnsToContents()


class Variant3CaseTab(QWidget):
    def __init__(
        self,
        analysis_service: Variant3AnalysisService,
        calculator: COCOMOCalculator,
        distribution_service: DistributionService,
        export_service: CsvExportService,
    ) -> None:
        super().__init__()
        self._analysis_service = analysis_service
        self._calculator = calculator
        self._distribution_service = distribution_service

        self._cost_spin = QDoubleSpinBox()
        self._note = QPlainTextEdit()
        self._results = EstimateResultsWidget(export_service=export_service, export_stem="variant3_case")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        controls_box = QGroupBox("Справочный сценарий")
        controls = QFormLayout(controls_box)

        self._cost_spin.setRange(0.0, 1_000_000_000.0)
        self._cost_spin.setDecimals(2)
        self._cost_spin.setValue(0.0)
        self._cost_spin.setSuffix(" за чел.-мес.")
        controls.addRow("Стоимость человеко-месяца", self._cost_spin)

        button = QPushButton("Рассчитать сценарий")
        button.clicked.connect(self._calculate)

        self._note.setReadOnly(True)
        self._note.setPlaceholderText("Здесь появятся допущения по сценарию.")

        layout.addWidget(controls_box)
        layout.addWidget(button)
        layout.addWidget(QLabel("Допущения"))
        layout.addWidget(self._note)
        layout.addWidget(self._results)

        self._calculate()

    def _calculate(self) -> None:
        preset = self._analysis_service.build_variant3_case_preset(
            cost_per_person_month=self._cost_spin.value() or None
        )
        estimate = self._calculator.estimate(preset.profile)
        distributions = self._distribution_service.build(estimate)
        self._note.setPlainText(preset.note)
        self._results.set_payload(ReportPayload(estimate=estimate, distributions=distributions))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"Калькулятор COCOMO ЛР №6 [{QT_BINDING}]")
        self.resize(1500, 900)

        calculator = COCOMOCalculator()
        distributions = DistributionService()
        analysis = Variant3AnalysisService(calculator)
        exporter = CsvExportService()

        tabs = QTabWidget()

        self._calculator_tab = CalculatorTab(calculator, distributions, exporter)
        self._analysis_tab = Variant3AnalysisTab(analysis, exporter)
        self._case_tab = Variant3CaseTab(analysis, calculator, distributions, exporter)

        tabs.addTab(self._calculator_tab, "Калькулятор")
        tabs.addTab(self._analysis_tab, "Анализ чувствительности")
        tabs.addTab(self._case_tab, "Справочный сценарий")

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

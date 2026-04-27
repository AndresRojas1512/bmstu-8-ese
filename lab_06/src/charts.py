from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path("/tmp") / "matplotlib-cocomo"))

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

if __package__ in {None, ""}:
    from cocomo import DistributionBundle, Variant3AnalysisResult
else:
    from .cocomo import DistributionBundle, Variant3AnalysisResult


class StaffingChartCanvas(FigureCanvasQTAgg):
    def __init__(self) -> None:
        self._figure = Figure(figsize=(7, 3.5), tight_layout=True)
        super().__init__(self._figure)

    def plot_distribution(self, distribution: DistributionBundle) -> None:
        self._figure.clear()
        axis = self._figure.add_subplot(111)

        segments = distribution.staffing_segments
        x_values = [segment.start_month for segment in segments]
        y_values = [segment.recommended_headcount for segment in segments]
        x_values.append(segments[-1].end_month)
        y_values.append(segments[-1].recommended_headcount)

        axis.step(x_values, y_values, where="post", color="#1b4d3e", linewidth=2.4)
        axis.fill_between(x_values, y_values, step="post", alpha=0.18, color="#1b4d3e")
        axis.set_title("Предлагаемый план привлечения сотрудников")
        axis.set_ylabel("Количество сотрудников")
        axis.set_xlabel("Месяц")
        axis.grid(True, alpha=0.25)

        for segment in segments:
            midpoint = (segment.start_month + segment.end_month) / 2
            axis.text(
                midpoint,
                segment.recommended_headcount + 0.1,
                segment.phase_name,
                ha="center",
                va="bottom",
                fontsize=8,
                rotation=10,
            )

        self.draw_idle()


class Variant3ChartsCanvas(FigureCanvasQTAgg):
    def __init__(self) -> None:
        self._figure = Figure(figsize=(9, 5.5), tight_layout=True)
        super().__init__(self._figure)

    def plot_analysis(self, analysis: Variant3AnalysisResult) -> None:
        self._figure.clear()
        axes = self._figure.subplots(2, 2)

        self._plot_metric(
            axes[0][0],
            analysis.nominal_sweeps,
            metric="effort",
            title=f"PM, SCED={analysis.nominal_sced.label}",
        )
        self._plot_metric(
            axes[0][1],
            analysis.nominal_sweeps,
            metric="time",
            title=f"TM, SCED={analysis.nominal_sced.label}",
        )
        self._plot_metric(
            axes[1][0],
            analysis.comparison_sweeps,
            metric="effort",
            title=f"PM, SCED={analysis.comparison_sced.label}",
        )
        self._plot_metric(
            axes[1][1],
            analysis.comparison_sweeps,
            metric="time",
            title=f"TM, SCED={analysis.comparison_sced.label}",
        )
        self.draw_idle()

    @staticmethod
    def _plot_metric(axis, sweeps, metric: str, title: str) -> None:
        palette = ["#1b4d3e", "#c84c09", "#3562a6"]

        for color, sweep in zip(palette, sweeps, strict=True):
            x_labels = [row.rating.label for row in sweep.rows]
            y_values = [row.effort_pm if metric == "effort" else row.time_months for row in sweep.rows]
            x_positions = list(range(len(x_labels)))
            axis.plot(
                x_positions,
                y_values,
                marker="o",
                linewidth=2.0,
                color=color,
                label=sweep.driver_id,
            )
            axis.set_xticks(x_positions)
            axis.set_xticklabels(x_labels, rotation=20)

        axis.set_title(title)
        axis.set_ylabel("Чел.-мес." if metric == "effort" else "Месяцы")
        axis.grid(True, alpha=0.25)
        axis.legend()

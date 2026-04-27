from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

if __package__ in {None, ""}:
    from cocomo import DistributionBundle, ProjectEstimate, Variant3AnalysisResult
else:
    from .cocomo import DistributionBundle, ProjectEstimate, Variant3AnalysisResult


@dataclass(frozen=True, slots=True)
class ExportedFile:
    label: str
    path: Path


class CsvExportService:
    def export_estimate(
        self,
        directory: str,
        estimate: ProjectEstimate,
        distributions: DistributionBundle,
        stem: str,
        total_budget: float | None,
    ) -> tuple[ExportedFile, ...]:
        target_dir = Path(directory)
        target_dir.mkdir(parents=True, exist_ok=True)

        summary_path = target_dir / f"{stem}_summary.csv"
        phases_path = target_dir / f"{stem}_phases.csv"
        wbs_path = target_dir / f"{stem}_wbs.csv"
        staffing_path = target_dir / f"{stem}_staffing.csv"

        self._write_csv(
            summary_path,
            ["Metric", "Value"],
            [
                ("Project mode", estimate.profile.mode.label),
                ("KLOC", f"{estimate.profile.kloc:.2f}"),
                ("EAF", f"{estimate.eaf:.4f}"),
                ("Development effort PM", f"{estimate.development_effort_pm:.2f}"),
                ("Development time months", f"{estimate.development_time_months:.2f}"),
                ("Average team size", f"{estimate.average_team_size:.2f}"),
                ("Total effort PM", f"{distributions.total_effort_pm:.2f}"),
                ("Total time months", f"{distributions.total_time_months:.2f}"),
                ("Budget", "" if total_budget is None else f"{total_budget:.2f}"),
            ],
        )

        self._write_csv(
            phases_path,
            ["Phase", "Effort %", "Time %", "Effort PM", "Time months", "Average staff"],
            [
                (
                    phase.name,
                    f"{phase.effort_percent:.2f}",
                    f"{phase.duration_percent:.2f}",
                    f"{phase.effort_pm:.2f}",
                    f"{phase.duration_months:.2f}",
                    f"{phase.average_staffing:.2f}",
                )
                for phase in distributions.phases
            ],
        )

        self._write_csv(
            wbs_path,
            ["WBS item", "Effort %", "Effort PM"],
            [
                (item.name, f"{item.effort_percent:.2f}", f"{item.effort_pm:.2f}")
                for item in distributions.wbs_items
            ],
        )

        self._write_csv(
            staffing_path,
            [
                "Phase",
                "Start month",
                "End month",
                "Duration months",
                "Effort PM",
                "Average staffing",
                "Recommended headcount",
            ],
            [
                (
                    segment.phase_name,
                    f"{segment.start_month:.2f}",
                    f"{segment.end_month:.2f}",
                    f"{segment.duration_months:.2f}",
                    f"{segment.effort_pm:.2f}",
                    f"{segment.average_staffing:.2f}",
                    str(segment.recommended_headcount),
                )
                for segment in distributions.staffing_segments
            ],
        )

        return (
            ExportedFile(label="summary", path=summary_path),
            ExportedFile(label="phases", path=phases_path),
            ExportedFile(label="staffing", path=staffing_path),
            ExportedFile(label="wbs", path=wbs_path),
        )

    def export_variant3_analysis(
        self,
        directory: str,
        analysis: Variant3AnalysisResult,
        stem: str,
    ) -> tuple[ExportedFile, ...]:
        target_dir = Path(directory)
        target_dir.mkdir(parents=True, exist_ok=True)

        summary_path = target_dir / f"{stem}_summary.csv"
        nominal_path = target_dir / f"{stem}_nominal_sced.csv"
        comparison_path = target_dir / f"{stem}_comparison_sced.csv"

        self._write_csv(
            summary_path,
            ["Metric", "Value"],
            [
                ("KLOC", f"{analysis.kloc:.2f}"),
                ("Nominal SCED", analysis.nominal_sced.label),
                ("Comparison SCED", analysis.comparison_sced.label),
                ("Top PM driver nominal", analysis.top_effort_driver_nominal),
                ("Top TM driver nominal", analysis.top_time_driver_nominal),
                ("Top PM driver comparison", analysis.top_effort_driver_comparison),
                ("Top TM driver comparison", analysis.top_time_driver_comparison),
            ],
        )
        self._write_sweeps(nominal_path, analysis.nominal_sweeps)
        self._write_sweeps(comparison_path, analysis.comparison_sweeps)

        return (
            ExportedFile(label="summary", path=summary_path),
            ExportedFile(label="nominal", path=nominal_path),
            ExportedFile(label="comparison", path=comparison_path),
        )

    @staticmethod
    def _write_sweeps(path: Path, sweeps) -> None:
        rows = []
        for sweep in sweeps:
            min_pm = min(item.effort_pm for item in sweep.rows)
            for item in sweep.rows:
                delta_percent = 0.0 if min_pm == 0 else (item.effort_pm - min_pm) / min_pm * 100.0
                rows.append(
                    (
                        sweep.driver_id,
                        sweep.driver_title,
                        item.rating.label,
                        f"{item.eaf:.4f}",
                        f"{item.effort_pm:.2f}",
                        f"{item.time_months:.2f}",
                        f"{delta_percent:.2f}",
                    )
                )

        CsvExportService._write_csv(
            path,
            ["Driver", "Title", "Rating", "EAF", "PM", "TM", "Delta vs min PM %"],
            rows,
        )

    @staticmethod
    def _write_csv(path: Path, header, rows) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(rows)

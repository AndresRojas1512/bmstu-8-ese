from __future__ import annotations

from dataclasses import dataclass

from .application_composition import (
    ApplicationCompositionProject,
    ObjectPointComplexity,
    ObjectPointItem,
    ObjectPointKind,
    ProductivityLevel,
)
from .early_design import EarlyDesignProject
from .enums import FunctionPointComponentType, Rating
from .function_points import (
    FunctionPointCalculator,
    FunctionPointComponent,
    FunctionPointProject,
    build_characteristics,
)
from .size_conversion import FunctionPointConversionService, LanguageFootprint, SizeConversionProject

DEFAULT_SQL_LOC_PER_FP = 53.0


@dataclass(frozen=True, slots=True)
class Lab7VariantPreset:
    project_name: str
    function_point_project: FunctionPointProject
    application_composition_project: ApplicationCompositionProject
    size_conversion_project: SizeConversionProject
    early_design_project: EarlyDesignProject | None
    language_mix_percent: dict[str, int]
    assumptions: tuple[str, ...]


def build_variant_2_preset(
    cost_per_person_month: float | None = None,
    sql_loc_per_fp: float | None = None,
) -> Lab7VariantPreset:
    effective_sql_loc_per_fp = DEFAULT_SQL_LOC_PER_FP if sql_loc_per_fp is None else sql_loc_per_fp

    function_components = (
        FunctionPointComponent(
            name="Авторизация пользователя",
            component_type=FunctionPointComponentType.EI,
            det_count=3,
            reference_count=1,
            notes="Логин, пароль и флаг запоминания авторизации.",
        ),
        FunctionPointComponent(
            name="Добавление бумаги в биржевые сводки",
            component_type=FunctionPointComponentType.EI,
            det_count=2,
            reference_count=1,
            notes="Имя бумаги и подтверждение команды.",
        ),
        FunctionPointComponent(
            name="Создание новой заявки",
            component_type=FunctionPointComponentType.EI,
            det_count=4,
            reference_count=2,
            notes="Имя бумаги, цена, количество, признак покупки/продажи.",
        ),
        FunctionPointComponent(
            name="Изменение существующей заявки",
            component_type=FunctionPointComponentType.EI,
            det_count=4,
            reference_count=2,
        ),
        FunctionPointComponent(
            name="Удаление заявки",
            component_type=FunctionPointComponentType.EI,
            det_count=2,
            reference_count=1,
        ),
        FunctionPointComponent(
            name="Показ биржевых сводок",
            component_type=FunctionPointComponentType.EO,
            det_count=4,
            reference_count=2,
            notes="Табличный вывод с вычислимым изменением цены.",
        ),
        FunctionPointComponent(
            name="Показ текущих заявок",
            component_type=FunctionPointComponentType.EQ,
            det_count=4,
            reference_count=1,
        ),
        FunctionPointComponent(
            name="История/статус исполнения заявки",
            component_type=FunctionPointComponentType.EO,
            det_count=3,
            reference_count=1,
        ),
        FunctionPointComponent(
            name="Заявки пользователя",
            component_type=FunctionPointComponentType.ILF,
            det_count=8,
            reference_count=1,
        ),
        FunctionPointComponent(
            name="Список отслеживаемых бумаг",
            component_type=FunctionPointComponentType.ILF,
            det_count=5,
            reference_count=1,
        ),
        FunctionPointComponent(
            name="Рыночные данные брокерской системы",
            component_type=FunctionPointComponentType.EIF,
            det_count=6,
            reference_count=1,
        ),
    )

    fp_characteristics = build_characteristics(
        {
            1: 5,
            2: 5,
            3: 3,
            4: 2,
            5: 3,
            6: 4,
            7: 1,
            8: 4,
            9: 4,
            10: 0,
            11: 1,
            12: 2,
            13: 2,
            14: 2,
        }
    )

    application_items = (
        ObjectPointItem(
            name="Экран авторизации",
            kind=ObjectPointKind.SCREEN,
            complexity=ObjectPointComplexity.SIMPLE,
        ),
        ObjectPointItem(
            name="Экран биржевых сводок",
            kind=ObjectPointKind.SCREEN,
            complexity=ObjectPointComplexity.COMPLEX,
        ),
        ObjectPointItem(
            name="Экран текущих заявок",
            kind=ObjectPointKind.SCREEN,
            complexity=ObjectPointComplexity.MEDIUM,
        ),
        ObjectPointItem(
            name="Экран создания заявки",
            kind=ObjectPointKind.SCREEN,
            complexity=ObjectPointComplexity.SIMPLE,
        ),
        ObjectPointItem(
            name="Отчет по биржевым сводкам",
            kind=ObjectPointKind.REPORT,
            complexity=ObjectPointComplexity.MEDIUM,
        ),
        ObjectPointItem(
            name="Отчет по текущим заявкам",
            kind=ObjectPointKind.REPORT,
            complexity=ObjectPointComplexity.MEDIUM,
        ),
    )

    exponent_factor_ratings = {
        "PREC": Rating.NOMINAL,
        "FLEX": Rating.HIGH,
        "RESL": Rating.LOW,
        "TEAM": Rating.HIGH,
        "PMAT": Rating.LOW,
    }

    effort_coefficient_ratings = {
        "PERS": Rating.NOMINAL,
        "RCPX": Rating.VERY_HIGH,
        "RUSE": Rating.LOW,
        "PDIF": Rating.HIGH,
        "PREX": Rating.LOW,
        "FCIL": Rating.VERY_HIGH,
        "SCED": Rating.VERY_LOW,
    }

    assumptions = (
        "Исходный сценарий редактируем и представляет собой трассируемую интерпретацию условия лабораторной работы.",
        "Для модели ранней разработки архитектуры размер проходит через явный пересчет функциональных точек в KLOC.",
        "В локальных материалах нет коэффициента LOC/FP для SQL, поэтому в версии для сдачи по умолчанию используется редактируемое экспертное допущение 53.",
        "Классификации функциональных и объектных точек можно уточнять через интерфейс при финальной проверке лабораторной работы.",
    )

    function_point_project = FunctionPointProject(
        components=function_components,
        characteristics=fp_characteristics,
    )
    adjusted_function_points = FunctionPointCalculator().calculate(function_point_project).adjusted_points
    size_conversion_project = SizeConversionProject(
        language_mix=(
            LanguageFootprint(language="SQL", percentage=15.0, loc_per_fp=effective_sql_loc_per_fp),
            LanguageFootprint(language="C#", percentage=60.0, loc_per_fp=53.0),
            LanguageFootprint(language="Java", percentage=25.0, loc_per_fp=53.0),
        )
    )
    size_conversion_result = FunctionPointConversionService().estimate(adjusted_function_points, size_conversion_project)
    early_design_project = None
    if size_conversion_result.estimated_kloc is not None:
        early_design_project = EarlyDesignProject(
            size=size_conversion_result.estimated_kloc,
            exponent_factor_ratings=exponent_factor_ratings,
            effort_coefficient_ratings=effort_coefficient_ratings,
            cost_per_person_month=cost_per_person_month,
        )

    return Lab7VariantPreset(
        project_name="Мобильное приложение брокерской системы",
        function_point_project=function_point_project,
        application_composition_project=ApplicationCompositionProject(
            items=application_items,
            reuse_percent=0.0,
            productivity_level=ProductivityLevel.NOMINAL,
            exponent_factor_ratings=exponent_factor_ratings,
            cost_per_person_month=cost_per_person_month,
        ),
        size_conversion_project=size_conversion_project,
        early_design_project=early_design_project,
        language_mix_percent={"SQL": 15, "C#": 60, "Java": 25},
        assumptions=assumptions,
    )

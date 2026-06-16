"""
Validations for question types.
"""

from collections.abc import Collection, Iterable
from decimal import Decimal, InvalidOperation
from math import isinf
from typing import Any

from pyxform import aliases
from pyxform import constants as co
from pyxform.errors import ErrorCode, PyXFormError
from pyxform.question_type_dictionary import QUESTION_TYPE_DICT
from pyxform.validators.pyxform import parameters as pv
from pyxform.validators.pyxform.choices import add_choices_info_to_question
from pyxform.validators.pyxform.parameters import (
    PARAMETERS_TYPE,
)
from pyxform.validators.pyxform.pyxform_reference import (
    is_pyxform_reference_candidate,
    parse_pyxform_references,
)

BACKGROUND_GEOPOINT_CALCULATION = (
    "[row : {r}] For 'background-geopoint' questions, "
    "the 'calculation' column must be empty."
)
BACKGROUND_GEOPOINT_TRIGGER = (
    "[row : {r}] For 'background-geopoint' questions, "
    "the 'trigger' column must not be empty."
)


def validate_background_geopoint_calculation(row: dict, row_num: int) -> bool:
    """A background-geopoint must not have a calculation."""
    try:
        row["bind"]["calculate"]
    except KeyError:
        return True
    else:
        raise PyXFormError(BACKGROUND_GEOPOINT_CALCULATION.format(r=row_num))


def validate_background_geopoint_trigger(trigger: str | None, row_num: int) -> bool:
    """A background-geopoint must have a trigger."""
    if not trigger:
        raise PyXFormError(BACKGROUND_GEOPOINT_TRIGGER.format(r=row_num))
    return True


def validate_references(
    referrers: Iterable[Iterable[str | None, int]], questions: Collection[str]
) -> bool:
    """Pyxform references must refer to a question that exists."""
    for target, row_num in referrers:
        if target not in questions:
            raise PyXFormError(
                code=ErrorCode.PYREF_003, context={"q": target, "row": row_num}
            )
    return True


def process_trigger(
    trigger: str | None, row_num: int, trigger_references: list[tuple[str, int]]
) -> tuple[str, ...] | None:
    """
    Try to parse the content of the "trigger" column into a list of question names.

    A trigger may contain one pyxform reference, or multiple comma-separated references.
    If a trigger is found, it will be added to trigger_references.

    :param trigger: The trigger data.
    :param row_num: The current row number.
    :param trigger_references: Which questions are being referred to by which row.
    """
    if not trigger:
        return None
    elif not is_pyxform_reference_candidate(trigger):
        raise PyXFormError(
            code=ErrorCode.PYREF_001,
            context={
                "sheet": "survey",
                "column": "trigger",
                "row": row_num,
                "q": trigger,
            },
        )

    try:
        trigger = tuple(
            r.name
            for t in trigger.split(",")
            for r in parse_pyxform_references(value=t, match_limit=1)
        )
    except PyXFormError as e:
        e.context.update(sheet="survey", column="trigger", row=row_num)
        raise

    if trigger:
        trigger_references.extend((t, row_num) for t in trigger)
        return trigger
    else:
        return None


def validate_geo_parameter_incremental(value: str) -> None:
    """For geoshape and geotrace, the 'incremental' parameter can only resolve to 'true'."""
    incremental = aliases.yes_no.get(value, None)
    if incremental is None or not incremental:
        raise PyXFormError(
            code=ErrorCode.SURVEY_003,
        )


def process_range_question_type(
    row_number: int,
    row: dict[str, Any],
    parameters: PARAMETERS_TYPE,
    appearance: str,
    choices: dict[str, Any],
) -> dict[str, Any]:
    """
    Returns a new row that includes the Range parameters start, end and step.

    Raises PyXFormError when invalid range parameters are used.
    """
    parameters = pv.validate(
        parameters=parameters,
        accepted=co.ParametersRange,
        row_number=row_number,
    )
    if (
        appearance
        and appearance not in {"vertical", "no-ticks"}
        and any(
            k in parameters
            for k in (
                co.ParametersRange.TICK_INTERVAL,
                co.ParametersRange.PLACEHOLDER,
                co.ParametersRange.TICK_LABELSET,
            )
        )
    ):
        raise PyXFormError(ErrorCode.RANGE_008.value.format(row=row_number))
    no_ticks_appearance = appearance and appearance == "no-ticks"

    defaults = QUESTION_TYPE_DICT["range"][co.PARAMETERS]
    # set defaults
    for key in defaults:
        if key not in parameters:
            parameters[key] = defaults[key]

    def process_parameter(name: str) -> Decimal | None:
        value = parameters.get(name)
        if value is None:
            return value
        err = False
        try:
            value = Decimal(value)
        except InvalidOperation:
            err = True

        if err or isinf(value):
            raise PyXFormError(
                ErrorCode.RANGE_001.value.format(row=row_number, name=name)
            )
        return value

    start = process_parameter(name=co.ParametersRange.START.value)
    end = process_parameter(name=co.ParametersRange.END.value)
    step = process_parameter(name=co.ParametersRange.STEP.value)
    tick_interval = process_parameter(name=co.ParametersRange.TICK_INTERVAL.value)
    placeholder = process_parameter(name=co.ParametersRange.PLACEHOLDER.value)
    tick_labelset = parameters.get(co.ParametersRange.TICK_LABELSET)
    range_width = abs(end - start)

    if step == 0:
        raise PyXFormError(
            ErrorCode.RANGE_002.value.format(
                row=row_number, name=co.ParametersRange.STEP.value
            )
        )
    if step > range_width:
        raise PyXFormError(
            ErrorCode.RANGE_003.value.format(
                row=row_number, name=co.ParametersRange.STEP.value
            )
        )

    if tick_interval is not None:
        if tick_interval == 0:
            raise PyXFormError(
                ErrorCode.RANGE_002.value.format(
                    row=row_number, name=co.ParametersRange.TICK_INTERVAL.value
                )
            )
        if tick_interval > range_width:
            raise PyXFormError(
                ErrorCode.RANGE_003.value.format(
                    row=row_number, name=co.ParametersRange.TICK_INTERVAL.value
                )
            )
        if (tick_interval % step) != 0:
            raise PyXFormError(
                ErrorCode.RANGE_004.value.format(
                    row=row_number, name=co.ParametersRange.TICK_INTERVAL.value
                )
            )
        # Input parameter uses underscore, output attribute name uses hyphen.
        parameters["odk:tick-interval"] = parameters.pop(
            co.ParametersRange.TICK_INTERVAL.value
        )

    if placeholder is not None:
        if (placeholder - start) % step != 0:
            raise PyXFormError(
                ErrorCode.RANGE_004.value.format(
                    row=row_number, name=co.ParametersRange.PLACEHOLDER.value
                )
            )
        if placeholder < min(start, end) or placeholder > max(start, end):
            raise PyXFormError(
                ErrorCode.RANGE_005.value.format(
                    row=row_number, name=co.ParametersRange.PLACEHOLDER.value
                )
            )
        parameters[f"odk:{co.ParametersRange.PLACEHOLDER.value}"] = parameters.pop(
            co.ParametersRange.PLACEHOLDER.value
        )

    if tick_labelset:
        tick_list = choices.get(tick_labelset)
        if tick_list is None:
            raise PyXFormError(ErrorCode.RANGE_006.value.format(row=row_number))

        no_ticks_labels = set()
        for item in tick_list:
            errored = False
            try:
                value = Decimal(item.get("name"))
            except InvalidOperation:
                errored = True

            if errored or isinf(value):
                raise PyXFormError(ErrorCode.RANGE_009.value.format(row=row_number))

            if value < min(start, end) or value > max(start, end):
                raise PyXFormError(ErrorCode.RANGE_010.value.format(row=row_number))
            if tick_interval is not None and (value - start) % tick_interval != 0:
                raise PyXFormError(
                    ErrorCode.RANGE_011.value.format(
                        row=row_number, name=co.ParametersRange.TICK_INTERVAL.value
                    )
                )
            elif (value - start) % step != 0:
                raise PyXFormError(
                    ErrorCode.RANGE_011.value.format(
                        row=row_number, name=co.ParametersRange.STEP.value
                    )
                )
            if no_ticks_appearance:
                no_ticks_labels.add(value)

        if no_ticks_appearance:
            if len(no_ticks_labels) > 2:
                raise PyXFormError(ErrorCode.RANGE_007.value.format(row=row_number))
            if no_ticks_labels != {start, end}:
                raise PyXFormError(ErrorCode.RANGE_012.value.format(row=row_number))

        parameters.pop(co.ParametersRange.TICK_LABELSET.value)

    # Default is integer, but if the values have decimals then change the bind type.
    if any(
        i is not None and not i == i.to_integral_value()
        for i in (start, end, step, tick_interval, placeholder)
    ):
        row["bind"] = row.get("bind", {})
        row["bind"].update({"type": "decimal"})

    row[co.PARAMETERS] = parameters

    # To trigger addition of itemset child nodes.
    if tick_labelset is not None:
        add_choices_info_to_question(
            question=row,
            list_name=tick_labelset,
            choices=choices,
            choice_filter=None,
            file_extension=None,
        )

    return row

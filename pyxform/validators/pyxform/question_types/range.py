from decimal import Decimal, InvalidOperation
from math import isinf
from typing import Any

from pyxform import constants as co
from pyxform.errors import ErrorCode, PyXFormError
from pyxform.question_type_dictionary import QUESTION_TYPE_DICT
from pyxform.validators.pyxform import parameters as pv
from pyxform.validators.pyxform.choices import add_choices_info_to_question
from pyxform.validators.pyxform.parameters import PARAMETERS_TYPE


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

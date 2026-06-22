from collections.abc import Iterable
from typing import Any

from pyxform import aliases
from pyxform import constants as co
from pyxform.errors import ErrorCode, PyXFormError
from pyxform.validators.pyxform import parameters as pv
from pyxform.validators.pyxform.parameters import PARAMETERS_TYPE
from pyxform.validators.pyxform.pyxform_reference import (
    is_pyxform_reference_candidate,
    parse_pyxform_references,
)


def validate_parameter_incremental(value: str) -> None:
    """For geoshape and geotrace, the 'incremental' parameter can only resolve to 'true'."""
    incremental = aliases.yes_no.get(value, None)
    if incremental is None or not incremental:
        raise PyXFormError(code=ErrorCode.SURVEY_003)


def validate_parameter_reference_geometry(
    geo_references: Iterable[Iterable[str, int]],
    secondary_instances: set[str],
    repeat_names: set[str],
    choices: dict[str, list[dict]],
    entity_declarations: dict[str, dict[str, Any]] | None = None,
) -> None:
    """
    Check that the reference-geometry name can be resolved to valid nodeset target.

    Does not support secondary instances that would be generated solely by:
    - pulldata() calls
    - search() calls
    - last-saved usages in variables

    :param geo_references: Pairs of (target, source row_num) for reference_geometry usage.
    :param secondary_instances: The names of valid secondary instances in the form.
    :param repeat_names: Names of repeat groups in the form.
    :param choices: The choices data as `{list_name: [choice_items[options], ...]}`.
    :param entity_declarations: The entities data `{list_name: declaration]}`.
    """
    for target, row_num in geo_references:
        if (
            target in secondary_instances
            or target in choices
            or (entity_declarations and target in entity_declarations)
        ):
            continue
        # Separated this part of the check since it requires slower parsing.
        elif is_pyxform_reference_candidate(target):
            try:
                refs = parse_pyxform_references(target, match_limit=1, match_full=True)
                if refs and refs[0].name in repeat_names:
                    continue
            except PyXFormError as err:
                raise PyXFormError(
                    code=ErrorCode.SURVEY_006, context={"row": row_num}
                ) from err

        raise PyXFormError(code=ErrorCode.SURVEY_006, context={"row": row_num})


def process_geo_question_type(
    row_number: int,
    row: dict[str, Any],
    parameters: PARAMETERS_TYPE,
    geo_references: list[tuple[str, int]],
) -> dict[str, Any]:
    """
    Amend the row data with processed parameters or other logic specific to the question type.

    :param row_number: The row position in the 'survey' sheet.
    :param row: The 'survey' sheet row data.
    :param parameters: The parsed parameters from the row data.
    :param geo_references: Pairs of (target, source row_num) for reference_geometry usage.
    :return: The updated row. Also appends to geo_references.
    """
    row[co.CONTROL] = row.get(co.CONTROL, {})
    question_type = row.get(co.TYPE)

    if question_type == "geopoint":
        qt_params = co.ParametersGeoPoint
        pv.validate(
            parameters=parameters,
            accepted=qt_params,
            row_number=row_number,
        )

        if qt_params.CAPTURE_ACCURACY in parameters:
            try:
                float(parameters[qt_params.CAPTURE_ACCURACY])
                row[co.CONTROL]["accuracyThreshold"] = parameters[
                    qt_params.CAPTURE_ACCURACY
                ]
            except ValueError as err:
                raise PyXFormError(
                    code=ErrorCode.SURVEY_007, context={"row": row_number}
                ) from err

        if qt_params.WARNING_ACCURACY in parameters:
            try:
                float(parameters[qt_params.WARNING_ACCURACY])
                row[co.CONTROL]["unacceptableAccuracyThreshold"] = parameters[
                    qt_params.WARNING_ACCURACY
                ]
            except ValueError as err:
                raise PyXFormError(
                    code=ErrorCode.SURVEY_008, context={"row": row_number}
                ) from err

    else:
        qt_params = co.ParametersGeo
        pv.validate(
            parameters=parameters,
            accepted=qt_params,
            row_number=row_number,
        )
        if qt_params.INCREMENTAL in parameters:
            try:
                validate_parameter_incremental(value=parameters[qt_params.INCREMENTAL])
            except PyXFormError as e:
                e.context.update(
                    sheet=co.SURVEY,
                    column=co.PARAMETERS,
                    row=row_number,
                )
                raise
            else:
                row[co.CONTROL][qt_params.INCREMENTAL.value] = "true"

    if qt_params.ALLOW_MOCK_ACCURACY in parameters:
        if parameters[qt_params.ALLOW_MOCK_ACCURACY] not in {"true", "false"}:
            raise PyXFormError(code=ErrorCode.SURVEY_009, context={"row": row_number})

        row[co.BIND] = row.get(co.BIND, {})
        row[co.BIND][f"odk:{qt_params.ALLOW_MOCK_ACCURACY.value}"] = parameters[
            qt_params.ALLOW_MOCK_ACCURACY
        ]

    if qt_params.REFERENCE_GEOMETRY in parameters:
        value = parameters[qt_params.REFERENCE_GEOMETRY]
        geo_references.append((value, row_number))
        row[co.ITEMSET] = value

    return row

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
        raise PyXFormError(
            code=ErrorCode.SURVEY_003,
        )


def validate_parameter_reference_geo(
    referrers: Iterable[Iterable[str | None, int]],
    csv_sources: set[str],
    repeats: set[str],
    choices: dict[str, list[dict]],
    entities: dict[str, dict[str, Any]] | None = None,
    external_choices: dict[Any, list] | None = None,
) -> None:
    """Check that the reference-geo name can be resolved to valid nodeset target."""
    for target, row_num in referrers:
        if (
            target in csv_sources
            or target in choices
            or (entities and target in entities)
            or (external_choices and target == "itemsets.csv")
        ):
            continue
        # Separated this part of the check since it requires slower parsing.
        elif is_pyxform_reference_candidate(target):
            try:
                refs = parse_pyxform_references(target, match_limit=1, match_full=True)
                if refs and refs[0].name in repeats:
                    continue
            except PyXFormError as e:
                raise PyXFormError(
                    code=ErrorCode.SURVEY_006, context={"row": row_num}
                ) from e

        raise PyXFormError(code=ErrorCode.SURVEY_006, context={"row": row_num})


def process_geo_question_type(
    row_number: int,
    row: dict[str, Any],
    parameters: PARAMETERS_TYPE,
    geo_references: list[tuple[str, int]],
) -> dict[str, Any]:
    new_dict = row.copy()
    new_dict["control"] = new_dict.get("control", {})
    question_type = row.get(co.TYPE)
    new_dict[co.PARAMETERS] = parameters

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
                new_dict["control"].update(
                    {"accuracyThreshold": parameters[qt_params.CAPTURE_ACCURACY]}
                )
            except ValueError as ca_err:
                raise PyXFormError(
                    f"Parameter {qt_params.CAPTURE_ACCURACY.value} must have a numeric value"
                ) from ca_err

        if qt_params.WARNING_ACCURACY in parameters:
            try:
                float(parameters[qt_params.WARNING_ACCURACY])
                new_dict["control"].update(
                    {
                        "unacceptableAccuracyThreshold": parameters[
                            qt_params.WARNING_ACCURACY
                        ]
                    }
                )
            except ValueError as wa_err:
                raise PyXFormError(
                    f"Parameter {qt_params.WARNING_ACCURACY.value} must have a numeric value"
                ) from wa_err

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
                new_dict["control"][qt_params.INCREMENTAL.value] = "true"

    if qt_params.ALLOW_MOCK_ACCURACY in parameters:
        if parameters[qt_params.ALLOW_MOCK_ACCURACY] not in {"true", "false"}:
            raise PyXFormError(
                f"Invalid value for {qt_params.ALLOW_MOCK_ACCURACY.value}."
            )

        new_dict["bind"] = new_dict.get("bind", {})
        new_dict["bind"].update(
            {
                f"odk:{qt_params.ALLOW_MOCK_ACCURACY.value}": parameters[
                    qt_params.ALLOW_MOCK_ACCURACY
                ]
            }
        )

    if qt_params.REFERENCE_GEO in parameters:
        value = parameters[qt_params.REFERENCE_GEO]
        geo_references.append((value, row_number))
        new_dict[co.ITEMSET] = value

    return new_dict

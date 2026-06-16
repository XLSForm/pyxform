from typing import Any

from pyxform import aliases
from pyxform import constants as co
from pyxform.errors import ErrorCode, PyXFormError
from pyxform.validators.pyxform import parameters as pv
from pyxform.validators.pyxform.parameters import PARAMETERS_TYPE


def validate_geo_parameter_incremental(value: str) -> None:
    """For geoshape and geotrace, the 'incremental' parameter can only resolve to 'true'."""
    incremental = aliases.yes_no.get(value, None)
    if incremental is None or not incremental:
        raise PyXFormError(
            code=ErrorCode.SURVEY_003,
        )


def process_geo_question_type(
    row_number: int,
    row: dict[str, Any],
    parameters: PARAMETERS_TYPE,
) -> dict[str, Any]:
    new_dict = row.copy()
    new_dict["control"] = new_dict.get("control", {})
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
                validate_geo_parameter_incremental(
                    value=parameters[qt_params.INCREMENTAL]
                )
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

    return new_dict

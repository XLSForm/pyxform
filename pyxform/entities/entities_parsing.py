from typing import Dict, List

from pyxform import constants
from pyxform.errors import PyXFormError
from pyxform.xlsparseutils import find_sheet_misspellings, is_valid_xml_tag


def get_entity_declaration(
    entities_sheet: Dict, workbook_dict: Dict, warnings: List
) -> Dict:
    if len(entities_sheet) == 0:
        similar = find_sheet_misspellings(
            key=constants.ENTITIES, keys=workbook_dict.keys()
        )
        if similar is not None:
            warnings.append(similar + constants._MSG_SUPPRESS_SPELLING)
        return {}
    elif len(entities_sheet) > 1:
        raise PyXFormError(
            "Currently, you can only declare a single entity per form. Please make sure your entities sheet only declares one entity."
        )

    entity = entities_sheet[0]
    dataset = entity["dataset"]

    if dataset.startswith(constants.ENTITIES_RESERVED_PREFIX):
        raise PyXFormError(
            f"Invalid entity list name: '{dataset}' starts with reserved prefix {constants.ENTITIES_RESERVED_PREFIX}."
        )

    if "." in dataset:
        raise PyXFormError(
            f"Invalid entity list name: '{dataset}'. Names may not include periods."
        )

    if not is_valid_xml_tag(dataset):
        if isinstance(dataset, bytes):
            dataset = dataset.encode("utf-8")

        raise PyXFormError(
            f"Invalid entity list name: '{dataset}'. Names must begin with a letter, colon, or underscore. Other characters can include numbers or dashes."
        )

    if not ("label" in entity):
        raise PyXFormError("The entities sheet is missing the required label column.")

    creation_condition = entity["create_if"] if "create_if" in entity else "1"

    return {
        "name": "entity",
        "type": "entity",
        "parameters": {
            "dataset": dataset,
            "create": creation_condition,
            "label": entity["label"],
        },
    }


def validate_entity_saveto(
    row: Dict, row_number: int, entity_declaration: Dict, in_repeat: bool
):
    save_to = row.get("bind", {}).get("entities:saveto", "")
    if not save_to:
        return

    if len(entity_declaration) == 0:
        raise PyXFormError(
            "To save entity properties using the save_to column, you must add an entities sheet and declare an entity."
        )

    if constants.GROUP in row.get(constants.TYPE) or constants.REPEAT in row.get(
        constants.TYPE
    ):
        raise PyXFormError(
            f"{constants.ROW_FORMAT_STRING % row_number} Groups and repeats can't be saved as entity properties."
        )

    if in_repeat:
        raise PyXFormError(
            f"{constants.ROW_FORMAT_STRING % row_number} Currently, you can't create entities from repeats. You may only specify save_to values for form fields outside of repeats."
        )

    error_start = f"{constants.ROW_FORMAT_STRING % row_number} Invalid save_to name:"

    if save_to.lower() == "name" or save_to.lower() == "label":
        raise PyXFormError(
            f"{error_start} the entity property name '{save_to}' is reserved."
        )

    if save_to.startswith(constants.ENTITIES_RESERVED_PREFIX):
        raise PyXFormError(
            f"{error_start} the entity property name '{save_to}' starts with reserved prefix {constants.ENTITIES_RESERVED_PREFIX}."
        )

    if not is_valid_xml_tag(save_to):
        if isinstance(save_to, bytes):
            save_to = save_to.encode("utf-8")

        raise PyXFormError(
            f"{error_start} '{save_to}'. Entity property names {constants.XML_IDENTIFIER_ERROR_MESSAGE}"
        )

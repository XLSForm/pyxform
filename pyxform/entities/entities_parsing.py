from typing import Any

from pyxform import constants as const
from pyxform.aliases import yes_no
from pyxform.errors import PyXFormError
from pyxform.xlsparseutils import find_sheet_misspellings, is_valid_xml_tag

EC = const.EntityColumns


def get_entity_declaration(
    entities_sheet: list[dict], workbook_dict: dict[str, list[dict]], warnings: list[str]
) -> dict[str, Any]:
    if len(entities_sheet) == 0:
        similar = find_sheet_misspellings(key=const.ENTITIES, keys=workbook_dict.keys())
        if similar is not None:
            warnings.append(similar + const._MSG_SUPPRESS_SPELLING)
        return {}
    elif len(entities_sheet) > 1:
        raise PyXFormError(
            "Currently, you can only declare a single entity per form. Please make sure your entities sheet only declares one entity."
        )

    entity_row = entities_sheet[0]

    validate_entities_columns(row=entity_row)
    dataset_name = get_validated_dataset_name(entity_row)
    entity_id = entity_row.get(EC.ENTITY_ID, None)
    create_condition = entity_row.get(EC.CREATE_IF, None)
    update_condition = entity_row.get(EC.UPDATE_IF, None)
    entity_label = entity_row.get(EC.LABEL, None)
    offline = yes_no.get(entity_row.get(EC.OFFLINE, None), None)

    if update_condition and not entity_id:
        raise PyXFormError(
            "The entities sheet is missing the entity_id column which is required when updating entities."
        )

    if entity_id and create_condition and not update_condition:
        raise PyXFormError(
            "The entities sheet can't specify an entity creation condition and an entity_id without also including an update condition."
        )

    if not entity_id and not entity_label:
        raise PyXFormError(
            "The entities sheet is missing the label column which is required when creating entities."
        )

    return {
        const.NAME: const.ENTITY,
        const.TYPE: const.ENTITY,
        const.PARAMETERS: {
            EC.DATASET: dataset_name,
            EC.ENTITY_ID: entity_id,
            EC.CREATE_IF: create_condition,
            EC.UPDATE_IF: update_condition,
            EC.LABEL: entity_label,
            EC.OFFLINE: offline,
        },
    }


def get_validated_dataset_name(entity):
    dataset = entity[EC.DATASET]

    if dataset.startswith(const.ENTITIES_RESERVED_PREFIX):
        raise PyXFormError(
            f"Invalid entity list name: '{dataset}' starts with reserved prefix {const.ENTITIES_RESERVED_PREFIX}."
        )

    if "." in dataset:
        raise PyXFormError(
            f"Invalid entity list name: '{dataset}'. Names may not include periods."
        )

    if not is_valid_xml_tag(dataset):
        if isinstance(dataset, bytes):
            dataset = dataset.decode("utf-8")

        raise PyXFormError(
            f"Invalid entity list name: '{dataset}'. Names must begin with a letter, colon, or underscore. Other characters can include numbers or dashes."
        )

    return dataset


def validate_entity_saveto(
    row: dict, row_number: int, entity_declaration: dict[str, Any], in_repeat: bool
):
    save_to = row.get(const.BIND, {}).get("entities:saveto", "")
    if not save_to:
        return

    if len(entity_declaration) == 0:
        raise PyXFormError(
            "To save entity properties using the save_to column, you must add an entities sheet and declare an entity."
        )

    if const.GROUP in row.get(const.TYPE) or const.REPEAT in row.get(const.TYPE):
        raise PyXFormError(
            f"{const.ROW_FORMAT_STRING % row_number} Groups and repeats can't be saved as entity properties."
        )

    if in_repeat:
        raise PyXFormError(
            f"{const.ROW_FORMAT_STRING % row_number} Currently, you can't create entities from repeats. You may only specify save_to values for form fields outside of repeats."
        )

    error_start = f"{const.ROW_FORMAT_STRING % row_number} Invalid save_to name:"

    if save_to.lower() == const.NAME or save_to.lower() == const.LABEL:
        raise PyXFormError(
            f"{error_start} the entity property name '{save_to}' is reserved."
        )

    if save_to.startswith(const.ENTITIES_RESERVED_PREFIX):
        raise PyXFormError(
            f"{error_start} the entity property name '{save_to}' starts with reserved prefix {const.ENTITIES_RESERVED_PREFIX}."
        )

    if not is_valid_xml_tag(save_to):
        if isinstance(save_to, bytes):
            save_to = save_to.decode("utf-8")

        raise PyXFormError(
            f"{error_start} '{save_to}'. Entity property names {const.XML_IDENTIFIER_ERROR_MESSAGE}"
        )


def validate_entities_columns(row: dict):
    extra = {k: None for k in row.keys() if k not in EC.value_list()}
    if 0 < len(extra):
        fmt_extra = ", ".join(f"'{k}'" for k in extra.keys())
        msg = (
            f"The entities sheet included the following unexpected column(s): {fmt_extra}. "
            f"These columns are not supported by this version of pyxform. Please either: "
            f"check the spelling of the column names, remove the columns, or update "
            f"pyxform."
        )
        raise PyXFormError(msg)

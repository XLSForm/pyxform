from collections.abc import Sequence
from typing import Any

from pyxform import constants as const
from pyxform.elements import action
from pyxform.errors import Detail, PyXFormError
from pyxform.parsing.expression import is_xml_tag
from pyxform.validators.pyxform.pyxform_reference import parse_pyxform_references

EC = const.EntityColumns
ENTITY001 = Detail(
    name="Invalid entity repeat reference",
    msg=(
        "[row : 2] On the 'entities' sheet, the 'repeat' value '{value}' is invalid. "
        "The 'repeat' column, if specified, must contain only a single reference variable "
        "(like '${{q1}}'), and the reference variable must contain a valid name."
    ),
)
ENTITY002 = Detail(
    name="Invalid entity repeat: target not found",
    msg=(
        "[row : 2] On the 'entities' sheet, the 'repeat' value '{value}' is invalid. "
        "The entity repeat target was not found in the 'survey' sheet."
    ),
)
ENTITY003 = Detail(
    name="Invalid entity repeat: target is not a repeat",
    msg=(
        "[row : 2] On the 'entities' sheet, the 'repeat' value '{value}' is invalid. "
        "The entity repeat target is not a repeat."
    ),
)
ENTITY004 = Detail(
    name="Invalid entity repeat: target is in a repeat",
    msg=(
        "[row : 2] On the 'entities' sheet, the 'repeat' value '{value}' is invalid. "
        "The entity repeat target is inside a repeat."
    ),
)
ENTITY005 = Detail(
    name="Invalid entity repeat save_to: question in nested repeat",
    msg=(
        "[row : {row}] On the 'survey' sheet, the 'save_to' value '{value}' is invalid. "
        "The entity property populated with 'save_to' must not be inside of a nested "
        "repeat within the entity repeat."
    ),
)
ENTITY006 = Detail(
    name="Invalid entity repeat save_to: question not in entity repeat",
    msg=(
        "[row : {row}] On the 'survey' sheet, the 'save_to' value '{value}' is invalid. "
        "The entity property populated with 'save_to' must be inside of the entity "
        "repeat."
    ),
)
ENTITY007 = Detail(
    name="Invalid entity repeat save_to: question in repeat but no entity repeat defined",
    msg=(
        "[row : {row}] On the 'survey' sheet, the 'save_to' value '{value}' is invalid. "
        "The entity property populated with 'save_to' must be inside a repeat that is "
        "declared in the 'repeat' column of the 'entities' sheet."
    ),
)


def get_entity_declaration(
    entities_sheet: Sequence[dict],
) -> dict[str, Any]:
    """
    Transform the entities sheet data into a spec for creating an EntityDeclaration.

    The combination of entity_id, create_if and update_if columns determines what entity
    behaviour is intended:

    entity_id  create_if  update_if  result
    0          0          0          always create
    0          0          1          error, need id to update
    0          1          0          create based on condition
    0          1          1          error, need id to update
    1          0          0          always update
    1          0          1          update based on condition
    1          1          0          error, id only acceptable when updating
    1          1          1          include conditions for create and update
                                       (user's responsibility to ensure they're exclusive)

    :param entities_sheet: XLSForm entities sheet data.
    """
    if len(entities_sheet) > 1:
        raise PyXFormError(
            "Currently, you can only declare a single entity per form. "
            "Please make sure your entities sheet only declares one entity."
        )

    entity_row = entities_sheet[0]

    validate_entities_columns(row=entity_row)
    dataset_name = get_validated_dataset_name(entity_row)
    entity_id = entity_row.get(EC.ENTITY_ID, None)
    create_if = entity_row.get(EC.CREATE_IF, None)
    update_if = entity_row.get(EC.UPDATE_IF, None)
    label = entity_row.get(EC.LABEL, None)
    repeat = get_validated_repeat_name(entity_row)

    if not entity_id and update_if:
        raise PyXFormError(
            "The entities sheet is missing the entity_id column which is required when "
            "updating entities."
        )

    if entity_id and create_if and not update_if:
        raise PyXFormError(
            "The entities sheet can't specify an entity creation condition and an "
            "entity_id without also including an update condition."
        )

    if not entity_id and not label:
        raise PyXFormError(
            "The entities sheet is missing the label column which is required when "
            "creating entities."
        )

    entity = {
        const.NAME: const.ENTITY,
        const.TYPE: const.ENTITY,
        EC.REPEAT.value: repeat,
        const.CHILDREN: [
            {
                const.NAME: "dataset",
                const.TYPE: "attribute",
                "value": dataset_name,
            },
        ],
    }

    id_attr = {
        const.NAME: "id",
        const.TYPE: "attribute",
        const.BIND: {
            "readonly": "true()",
            "type": "string",
        },
        "actions": [],
    }

    # Create mode
    if not entity_id or create_if:
        create_attr = {const.NAME: "create", const.TYPE: "attribute", "value": "1"}
        if create_if:
            create_attr[const.BIND] = {
                "calculate": create_if,
                "readonly": "true()",
                "type": "string",
            }
        entity[const.CHILDREN].append(create_attr)

        first_load = action.ActionLibrary.setvalue_first_load.value.to_dict()
        first_load["value"] = "uuid()"
        id_attr["actions"].append(first_load)

        if repeat:
            new_repeat = action.ActionLibrary.setvalue_new_repeat.value.to_dict()
            new_repeat["value"] = "uuid()"
            id_attr["actions"].append(new_repeat)

    # Update mode
    if entity_id:
        update_attr = {const.NAME: "update", const.TYPE: "attribute", "value": "1"}
        if update_if:
            update_attr[const.BIND] = {
                "calculate": update_if,
                "readonly": "true()",
                "type": "string",
            }

        entity[const.CHILDREN].append(update_attr)

        id_attr[const.BIND]["calculate"] = entity_id

        entity_id_expression = f"instance('{dataset_name}')/root/item[name={entity_id}]"
        entity[const.CHILDREN].extend(
            [
                {
                    const.NAME: "baseVersion",
                    const.TYPE: "attribute",
                    const.BIND: {
                        "calculate": f"{entity_id_expression}/__version",
                        "readonly": "true()",
                        "type": "string",
                    },
                },
                {
                    const.NAME: "trunkVersion",
                    const.TYPE: "attribute",
                    const.BIND: {
                        "calculate": f"{entity_id_expression}/__trunkVersion",
                        "readonly": "true()",
                        "type": "string",
                    },
                },
                {
                    const.NAME: "branchId",
                    const.TYPE: "attribute",
                    const.BIND: {
                        "calculate": f"{entity_id_expression}/__branchId",
                        "readonly": "true()",
                        "type": "string",
                    },
                },
            ]
        )

    entity[const.CHILDREN].append(id_attr)

    if label:
        entity[const.CHILDREN].append(
            {
                const.TYPE: "label",
                const.NAME: "label",
                const.BIND: {
                    "calculate": label,
                    "readonly": "true()",
                    "type": "string",
                },
            },
        )

    return entity


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

    if not is_xml_tag(dataset):
        if isinstance(dataset, bytes):
            dataset = dataset.decode("utf-8")

        raise PyXFormError(
            f"Invalid entity list name: '{dataset}'. Names must begin with a letter, colon, or underscore. Other characters can include numbers or dashes."
        )

    return dataset


def get_validated_repeat_name(entity) -> str | None:
    if EC.REPEAT.value not in entity:
        return None

    value = entity[EC.REPEAT]
    try:
        match = parse_pyxform_references(value=value, match_limit=1, match_full=True)
    except PyXFormError as e:
        e.context.update(sheet="entities", column="repeat", row=2)
        raise
    else:
        if not match or match[0].last_saved:
            raise PyXFormError(ENTITY001.format(value=value))
        else:
            return match[0].name


def validate_entity_saveto(
    row: dict,
    row_number: int,
    stack: Sequence[dict[str, Any]],
    entity_declaration: dict[str, Any] | None = None,
):
    save_to = row.get(const.BIND, {}).get("entities:saveto", "")
    if not save_to:
        return

    if not entity_declaration:
        raise PyXFormError(
            "To save entity properties using the save_to column, you must add an entities sheet and declare an entity."
        )

    if const.GROUP in row.get(const.TYPE) or const.REPEAT in row.get(const.TYPE):
        raise PyXFormError(
            f"{const.ROW_FORMAT_STRING % row_number} Groups and repeats can't be saved as entity properties."
        )

    entity_repeat = entity_declaration.get(EC.REPEAT, None)
    in_repeat = False
    located = False
    for i in reversed(stack):
        if not i["control_name"] or not i["control_type"]:
            break
        elif i["control_type"] == const.REPEAT:
            # Error: saveto in nested repeat inside entity repeat.
            if in_repeat:
                raise PyXFormError(ENTITY005.format(row=row_number, value=save_to))
            elif i["control_name"] == entity_repeat:
                located = True
            in_repeat = True

    # Error: saveto not in entity repeat
    if entity_repeat and not located:
        raise PyXFormError(ENTITY006.format(row=row_number, value=save_to))

    # Error: saveto in repeat but no entity repeat declared
    if in_repeat and not entity_repeat:
        raise PyXFormError(ENTITY007.format(row=row_number, value=save_to))

    error_start = f"{const.ROW_FORMAT_STRING % row_number} Invalid save_to name:"

    if save_to.lower() == const.NAME or save_to.lower() == const.LABEL:
        raise PyXFormError(
            f"{error_start} the entity property name '{save_to}' is reserved."
        )

    if save_to.startswith(const.ENTITIES_RESERVED_PREFIX):
        raise PyXFormError(
            f"{error_start} the entity property name '{save_to}' starts with reserved prefix {const.ENTITIES_RESERVED_PREFIX}."
        )

    if not is_xml_tag(save_to):
        if isinstance(save_to, bytes):
            save_to = save_to.decode("utf-8")

        raise PyXFormError(
            f"{error_start} '{save_to}'. Entity property names {const.XML_IDENTIFIER_ERROR_MESSAGE}"
        )


def validate_entities_columns(row: dict):
    extra = {k: None for k in row if k not in EC.value_list()}
    if 0 < len(extra):
        fmt_extra = ", ".join(f"'{k}'" for k in extra)
        msg = (
            f"The entities sheet included the following unexpected column(s): {fmt_extra}. "
            f"These columns are not supported by this version of pyxform. Please either: "
            f"check the spelling of the column names, remove the columns, or update "
            f"pyxform."
        )
        raise PyXFormError(msg)


def validate_entity_repeat_target(
    entity_declaration: dict[str, Any] | None,
    stack: Sequence[dict[str, Any]] | None = None,
) -> bool:
    """
    Check if the entity repeat target exists, is a repeat, and is a name match.

    Raises an error if the control type or name is None (such as for the Survey), or if
    the control type is not a repeat.

    :param entity_declaration:
    :param stack: The control stack from workbook_to_json.
    :return:
    """
    # Ignore: entity already processed.
    if not entity_declaration:
        return False

    entity_repeat = entity_declaration.get(EC.REPEAT, None)

    # Ignore: no repeat declared for the entity.
    if not entity_repeat:
        return False

    # Error: repeat not found while processing survey sheet.
    if not stack:
        raise PyXFormError(ENTITY002.format(value=entity_repeat))

    control_name = stack[-1]["control_name"]
    control_type = stack[-1]["control_type"]

    # Ignore: current control is not the target.
    if control_name and control_name != entity_repeat:
        return False

    # Error: target is not a repeat.
    if control_type and control_type != const.REPEAT:
        raise PyXFormError(ENTITY003.format(value=entity_repeat))

    # Error: repeat is in nested repeat.
    located = False
    for i in reversed(stack):
        if not i["control_name"] or not i["control_type"]:
            break
        elif i["control_type"] == const.REPEAT:
            if located:
                raise PyXFormError(ENTITY004.format(value=entity_repeat))
            elif i["control_name"] == entity_repeat:
                located = True

    return entity_repeat == control_name

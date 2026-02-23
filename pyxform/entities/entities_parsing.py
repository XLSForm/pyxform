from collections import defaultdict
from collections.abc import Iterable
from typing import Any, NamedTuple

from pyxform import constants as const
from pyxform.elements import action
from pyxform.errors import ErrorCode, PyXFormError
from pyxform.parsing.expression import is_xml_tag
from pyxform.question_type_dictionary import get_meta_group
from pyxform.validators.pyxform.pyxform_reference import parse_pyxform_references

EC = const.EntityColumns


class ContainerNode(NamedTuple):
    name: str
    type: str


class ReferenceSource(NamedTuple):
    path: tuple[ContainerNode, ...]
    row: int
    property_name: str | None = None
    question_name: str | None = None

    def get_scope_boundary(self) -> tuple[ContainerNode, ...]:
        for i in range(len(self.path) - 1, -1, -1):
            if self.path[i].type in {const.REPEAT, const.SURVEY}:
                return self.path[: i + 1]
        return ()


def get_entity_declaration(row: dict) -> dict[str, Any]:
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

    :param row: A row from the XLSForm entities sheet data.
    """
    extra = {k: None for k in row if k not in EC.value_list()}
    if 0 < len(extra):
        msg = ErrorCode.HEADER_005.value.format(
            columns=", ".join(f"'{k}'" for k in extra)
        )
        raise PyXFormError(msg)

    dataset_name = get_validated_dataset_name(row)
    entity_id = row.get(EC.ENTITY_ID, None)
    create_if = row.get(EC.CREATE_IF, None)
    update_if = row.get(EC.UPDATE_IF, None)
    label = row.get(EC.LABEL, None)

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
            ErrorCode.NAMES_010.value.format(
                sheet=const.ENTITIES, row=2, column=EC.DATASET.value
            )
        )
    elif "." in dataset:
        raise PyXFormError(
            ErrorCode.NAMES_011.value.format(
                sheet=const.ENTITIES, row=2, column=EC.DATASET.value
            )
        )
    elif not is_xml_tag(dataset):
        raise PyXFormError(
            ErrorCode.NAMES_008.value.format(
                sheet=const.ENTITIES, row=2, column=EC.DATASET.value
            )
        )

    return dataset


def validate_entity_saveto(
    saveto: str,
    row_number: int,
    is_container_begin: bool,
    is_container_end: bool,
    entity_references: list[ReferenceSource],
) -> None:
    if not saveto:
        raise PyXFormError(
            ErrorCode.NAMES_008.value.format(
                sheet=const.SURVEY, row=row_number, column=const.ENTITIES_SAVETO
            )
        )
    elif is_container_begin or is_container_end:
        raise PyXFormError(ErrorCode.ENTITY_003.value.format(row=row_number))
    # Error: naming rules
    elif saveto.lower() in {const.NAME, const.LABEL}:
        raise PyXFormError(
            ErrorCode.NAMES_012.value.format(
                sheet=const.SURVEY, row=row_number, column=const.ENTITIES_SAVETO
            )
        )
    elif saveto.startswith(const.ENTITIES_RESERVED_PREFIX):
        raise PyXFormError(
            ErrorCode.NAMES_010.value.format(
                sheet=const.SURVEY, row=row_number, column=const.ENTITIES_SAVETO
            )
        )
    elif not is_xml_tag(saveto):
        raise PyXFormError(
            ErrorCode.NAMES_008.value.format(
                sheet=const.SURVEY, row=row_number, column=const.ENTITIES_SAVETO
            )
        )
    elif entity_references:
        for ref_source in entity_references:
            if ref_source.property_name == saveto:
                raise PyXFormError(
                    ErrorCode.ENTITY_002.value.format(
                        row=row_number, saveto=saveto, other_row=ref_source.row
                    )
                )


def get_entity_declarations(
    entities_sheet: Iterable[dict],
) -> dict[str, dict[str, Any]]:
    """
    Collect all entity declarations from the entities sheet.
    """
    entities = {}
    for row_number, row in enumerate(entities_sheet, start=2):
        entity = get_entity_declaration(row=row)
        dataset_name = next(
            c["value"] for c in entity["children"] if c.get("name", "") == "dataset"
        )
        if dataset_name in entities:
            raise PyXFormError(ErrorCode.NAMES_014.value.format(row=row_number))
        entities[dataset_name] = entity

    return entities


def get_entity_variable_references(
    entities_sheet: Iterable[dict],
) -> dict[str, dict[str, list[str]]]:
    """
    Parse variable references in the entities sheet columns.
    """
    entity_references = defaultdict(lambda: defaultdict(list))
    for row in entities_sheet:
        for column_name, value in row.items():
            if column_name == EC.DATASET:
                continue
            references = parse_pyxform_references(value=value)
            if references:
                for ref in references:
                    entity_references[ref.name][row[EC.DATASET]].append(column_name)
    return entity_references


def get_entity_references_by_question(
    stack: list[dict[str, Any]],
    row: dict[str, Any],
    row_number: int,
    question_name: str,
    entity_declarations: dict[str, dict[str, Any]],
    entity_variable_references: dict[str, dict[str, list[str]]],
    entity_references_by_question: defaultdict[str, list[ReferenceSource]],
    is_container_begin: bool,
    is_container_end: bool,
) -> None:
    """
    For each question store the saveto or variable references that link it to an entity.
    """
    # TODO: pre-calculate the current_path externally - maybe as part of the stack? It only
    #   changes when the container opens/closes so may be unnecessarily re-calculated and
    #   this block is recursing up the stack each time so may be non-trivial impact
    if len(stack) > 1:
        container_path = (
            ContainerNode(name=const.SURVEY, type=const.SURVEY),
            *(
                ContainerNode(
                    name=container.get("control_name"), type=container.get("control_type")
                )
                for container in stack[1:]
            ),
        )
    else:
        container_path = (ContainerNode(name=const.SURVEY, type=const.SURVEY),)

    # Collect references for later reconciliation, because otherwise the first
    # referent found will determine the scope but there may be deeper refs.
    saveto = row.get(const.BIND, {}).get(const.ENTITIES_SAVETO_NS, "")
    if saveto:
        if not entity_declarations:
            raise PyXFormError(ErrorCode.ENTITY_001.value.format(row=row_number))

        if "#" in saveto:
            dataset_name, saveto = saveto.split("#", maxsplit=1)
            row[const.BIND][const.ENTITIES_SAVETO_NS] = saveto
        else:
            dataset_name = next(iter(entity_declarations.keys()))

        if dataset_name not in entity_declarations:
            raise PyXFormError(
                ErrorCode.ENTITY_004.value.format(row=row_number, dataset=dataset_name)
            )

        entity_references = entity_references_by_question[dataset_name]

        validate_entity_saveto(
            saveto=saveto,
            row_number=row_number,
            is_container_begin=is_container_begin,
            is_container_end=is_container_end,
            entity_references=entity_references,
        )

        entity_references.append(
            ReferenceSource(path=container_path, row=row_number, property_name=saveto)
        )

    if entity_variable_references and question_name in entity_variable_references:
        for dataset_name in entity_variable_references[question_name]:
            entity_references_by_question[dataset_name].append(
                ReferenceSource(
                    path=container_path, row=row_number, question_name=question_name
                )
            )


def get_container_scopes(
    entity_references_by_question: defaultdict[str, list[ReferenceSource]],
) -> defaultdict[tuple[ContainerNode, ...], dict[str, list[ReferenceSource]]]:
    """
    Find/validate the deepest scope among the entity_references.
    """
    scope_paths = defaultdict(dict)

    for dataset_name, entity_references in entity_references_by_question.items():
        scope_path = (ContainerNode(name=const.SURVEY, type=const.SURVEY),)

        # Assumes entity_references is already in row order.
        for s in entity_references:
            deepest_scope = s.get_scope_boundary()

            if len(deepest_scope) == len(scope_path) and deepest_scope != scope_path:
                raise PyXFormError(
                    f"Scope Breach for '{dataset_name}': subscriber trying to switch scope at same level"
                )
            elif len(deepest_scope) > len(scope_path):
                scope_path = deepest_scope

        scope_paths[scope_path][dataset_name] = entity_references

    return scope_paths


def get_allocation_requests(
    scope_path: tuple[ContainerNode, ...],
    entity_references: dict[str, list[ReferenceSource]],
):
    """
    Assign/validate the preferred path for each entity declaration.
    """
    allocation_requests = []
    for dataset_name, references in entity_references.items():
        if not references:
            continue

        # Determine the repeat lineage of the first subscriber to use as a baseline
        requested_ref = max(references, key=lambda s: len(s.path))

        # Prioritise saveto since they must be in the nearest container.
        save_tos = tuple(s for s in references if s.property_name is not None)
        if save_tos:
            lca_saveto = max(save_tos, key=lambda s: len(s.path))
            requested_ref = min((requested_ref, lca_saveto), key=lambda s: len(s.path))

        # Check saveto entity_refs match the scope_path
        for ref in references:
            ref_scope_stack = ref.get_scope_boundary()

            if (
                ref.property_name is not None
                and ref_scope_stack
                and scope_path
                and ref_scope_stack != scope_path
            ):
                raise PyXFormError(
                    f"Scope Breach for '{dataset_name}': saveto references "
                    f"(rows {requested_ref.row}, {ref.row}) "
                    "exist across inconsistent repeat boundaries."
                )

        allocation_requests.append(
            {
                "dataset_name": dataset_name,
                "requested_path": requested_ref.path,
                "minimum_depth": len(scope_path),
                "rows": [s.row for s in references],
                "has_savetos": int(bool(save_tos)),
            }
        )

    return allocation_requests


def allocate_entities_to_paths(
    scope_path: tuple[ContainerNode, ...], requests: list[dict[str, Any]]
) -> dict[tuple[ContainerNode, ...], str]:
    """
    Assign the requested allocations to available allowed container nodes if possible.
    """
    allocations = {}

    # Prioritise save_to references but otherwise try to put deepest allocation first.
    requests.sort(
        key=lambda x: (x["has_savetos"], len(x["requested_path"])), reverse=True
    )

    for item in requests:
        current_path = item["requested_path"]
        placed = False

        # Attempt to place as low as possible, but try going up to the highest allowed.
        while len(current_path) >= item["minimum_depth"]:
            if current_path not in allocations:
                allocations[current_path] = item["dataset_name"]
                placed = True
                break
            current_path = current_path[:-1]

        if not placed:
            rows = ", ".join(str(r) for r in item["rows"])
            raise PyXFormError(
                f"Conflict in scope '{scope_path[-1]}': Referent '{item['dataset_name']}' "
                f"(rows {rows}) has no available allowed container slots."
            )

    return allocations


def allocate_entities_to_containers(
    entity_references_by_question: defaultdict[str, list[ReferenceSource]],
) -> dict[tuple[ContainerNode, ...], str]:
    """
    Get the paths into which the entities will be placed.
    """
    all_allocations = {}
    scope_paths = get_container_scopes(
        entity_references_by_question=entity_references_by_question
    )
    for scope_path, entity_references in scope_paths.items():
        requests = get_allocation_requests(
            scope_path=scope_path, entity_references=entity_references
        )
        allocations = allocate_entities_to_paths(scope_path=scope_path, requests=requests)
        all_allocations.update(allocations)

    return all_allocations


def inject_entities_into_json(
    node: dict[str, Any],
    allocations: dict[tuple[ContainerNode, ...], str],
    entity_declarations: dict[str, dict[str, Any]],
    current_path: tuple[ContainerNode, ...],
    search_prefixes: set[tuple[ContainerNode, ...]],
    entities_allocated: set[str] | None = None,
    has_repeat_ancestor: bool = False,
) -> dict[str, Any]:
    """
    Recursively traverse the json_dict to inject entity declarations.
    """
    if entities_allocated is None:
        entities_allocated = set()

    dataset_name = allocations.get(current_path, None)
    if dataset_name and dataset_name not in entities_allocated:
        entity_decl = entity_declarations.get(dataset_name, None)
        # TODO: seems unlikely but perhaps there should be an error on `entity_decl is None`
        if entity_decl:
            if has_repeat_ancestor:
                id_attr = next(
                    iter(c for c in entity_decl[const.CHILDREN] if c[const.NAME] == "id"),
                    None,
                )
                # TODO: could do with a more explicit way of signaling that repeat is allowed
                # TODO: should there be an error if the id attr is not found? could that ever happen
                if id_attr and id_attr["actions"]:
                    new_repeat = action.ActionLibrary.setvalue_new_repeat.value.to_dict()
                    new_repeat["value"] = "uuid()"
                    if new_repeat not in id_attr["actions"]:
                        id_attr["actions"].append(new_repeat)

            if const.CHILDREN not in node:
                node[const.CHILDREN] = []

            node[const.CHILDREN].append(get_meta_group(children=[entity_decl]))
            entities_allocated.add(dataset_name)

    for child in node.get(const.CHILDREN, []):
        child_name = child.get(const.NAME)
        child_type = child.get(const.TYPE)
        if child_name and child_type in {const.GROUP, const.REPEAT}:
            child_path = (*current_path, ContainerNode(name=child_name, type=child_type))
            if not has_repeat_ancestor and child_type == const.REPEAT:
                has_repeat_ancestor = True
            if child_path in search_prefixes:
                inject_entities_into_json(
                    node=child,
                    allocations=allocations,
                    entity_declarations=entity_declarations,
                    current_path=child_path,
                    search_prefixes=search_prefixes,
                    entities_allocated=entities_allocated,
                    has_repeat_ancestor=has_repeat_ancestor,
                )

    return node


def get_search_prefixes(
    allocations: dict[tuple[ContainerNode, ...], str],
) -> set[tuple[ContainerNode, ...]]:
    """
    Get all the relevant path prefixes to help reduce the path search space.

    :param allocations: The entity path allocations.
    :return: path prefixes like (a, b, c) -> ((a,), (a, b), (a, b, c))
    """
    active = set()
    for path in allocations.keys():
        # Add every prefix of the path to the set
        for i in range(1, len(path) + 1):
            active.add(path[:i])
    return active


def apply_entities_declarations(
    entity_declarations: dict[str, dict[str, Any]],
    entity_references_by_question: defaultdict[str, list[ReferenceSource]],
    json_dict: dict[str, Any],
    meta_children: list[dict[str, Any]],
) -> None:
    """
    Traverse the json_dict tree and add meta/entity blocks where appropriate.

    Processing phases:
    1. for each question collect references in get_entity_references_by_question
    2. calculate entity container assignments in allocate_entities_to_containers
    3. apply those meta/entity declarations in inject_entities_into_json

    :param entity_declarations: Entity definition data to be passed to EntityDeclaration,
      structured as `{dataset_name: entity_declaration}`.
    :param entity_references_by_question: For each entity, details of where and how they
      are referred to, structured as `{dataset_name: list[ReferenceSource]}`.
    :param json_dict: The output dict structure to be emitted from `workbook_to_json`.
    :param meta_children: Details of the nodes to be added to the (parent) meta block.
    :return: The json_dict is modified in-place
    """
    has_allocations = False
    has_repeats = False
    if entity_references_by_question:
        allocations = allocate_entities_to_containers(
            entity_references_by_question=entity_references_by_question
        )
        if allocations:
            has_allocations = True
            has_repeats = any(
                p.type == const.REPEAT for i in allocations.keys() for p in i
            )
            has_repeat_ancestor = json_dict.get(const.TYPE) == const.REPEAT
            json_dict = inject_entities_into_json(
                node=json_dict,
                allocations=allocations,
                entity_declarations=entity_declarations,
                current_path=(ContainerNode(name=const.SURVEY, type=const.SURVEY),),
                search_prefixes=get_search_prefixes(allocations=allocations),
                has_repeat_ancestor=has_repeat_ancestor,
            )

    if len(entity_declarations) > 1 or has_repeats:
        json_dict[const.ENTITY_VERSION] = const.EntityVersion.v2025_1_0
    else:
        json_dict[const.ENTITY_VERSION] = const.EntityVersion.v2024_1_0
        if not has_allocations:
            if len(entity_declarations) > 1:
                # TODO: raise error if not already caught / handled elsewhere
                pass
            else:
                # TODO: could this func chain deal with the no-reference case as well?
                meta_children.append(next(iter(entity_declarations.values())))

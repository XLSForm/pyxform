from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, NamedTuple

from pyxform import constants as const
from pyxform.elements import action
from pyxform.errors import ErrorCode, PyXFormError
from pyxform.parsing.expression import is_xml_tag
from pyxform.question_type_dictionary import get_meta_group
from pyxform.validators.pyxform.pyxform_reference import parse_pyxform_references

EC = const.EntityColumns


@dataclass(frozen=True, slots=True)
class ContainerNode:
    """
    Details of a XForm container: the survey root, a group, or a repeat.
    """

    name: str
    type: str


@dataclass(frozen=True, slots=True)
class ContainerPath:
    """
    Details of a collection of containers, ordered by their depth, which forms a path.

    Example: /survey/group1/repeat1/group2
    """

    nodes: tuple[ContainerNode, ...]

    @classmethod
    def default(cls) -> "ContainerPath":
        """
        Create the default ContainerPath, which is the '/survey' root path.
        """
        return cls((ContainerNode(name=const.SURVEY, type=const.SURVEY),))

    @classmethod
    def from_stack(cls, stack: list[dict[str, Any]]) -> "ContainerPath":
        """
        Create a ContainerPath from the workbook_to_json container stack.
        """
        if len(stack) > 1:
            return cls(
                (
                    *stack[-2]["container_path"].nodes,
                    ContainerNode(
                        name=stack[-1]["control_name"],
                        type=stack[-1]["control_type"],
                    ),
                )
            )
        else:
            return cls.default()


@dataclass(frozen=True, slots=True)
class ReferenceSource:
    path: ContainerPath
    row: int
    property_name: str | None = None
    question_name: str | None = None

    def __post_init__(self):
        if self.property_name is None and self.question_name is None:
            raise PyXFormError(
                ErrorCode.INTERNAL_002.value.format(path=self.path_as_str())
            )

    def get_scope_boundary(self) -> ContainerPath:
        for i in range(len(self.path.nodes) - 1, -1, -1):
            if self.path.nodes[i].type in {const.REPEAT, const.SURVEY}:
                return ContainerPath(self.path.nodes[: i + 1])
        return ContainerPath.default()

    def path_as_str(self) -> str:
        return f"/{'/'.join(p.name for p in self.path.nodes)}"


@dataclass(slots=True)
class EntityReferences:
    dataset_name: str
    row_number: int = field(compare=False, hash=False)
    references: list[ReferenceSource] = field(
        compare=False, hash=False, default_factory=list
    )

    def get_allocation_request(self) -> "AllocationRequest":
        """
        Find/validate the preferred path for each entity declaration.
        """
        deepest_scope_ref = None
        deepest_scope_boundary = None
        deepest_container_ref = self.references[0]
        deepest_saveto = None
        boundaries = []

        # Find the request constraints for this entity.
        for ref in self.references:
            ref_path_length = len(ref.path.nodes)
            if ref_path_length > len(deepest_container_ref.path.nodes):
                deepest_container_ref = ref

            if ref.property_name is not None and (
                deepest_saveto is None or ref_path_length > len(deepest_saveto.path.nodes)
            ):
                deepest_saveto = ref

            boundary = ref.get_scope_boundary()
            boundary_length = len(boundary.nodes)
            if deepest_scope_boundary is None or boundary_length > len(
                deepest_scope_boundary.nodes
            ):
                deepest_scope_boundary = boundary
                deepest_scope_ref = ref

            boundaries.append((ref, boundary, boundary_length))

        # Prioritise saveto since they must be in the nearest container with an entity.
        if deepest_saveto:
            requested_ref = deepest_saveto
        else:
            requested_ref = deepest_container_ref

        # Validate each reference against the request constraints.
        for ref_source, scope_boundary, scope_boundary_length in boundaries:
            if (
                deepest_scope_boundary.nodes[:scope_boundary_length]
                != scope_boundary.nodes
            ):
                if ref_source.property_name is not None:  # save_to
                    raise PyXFormError(
                        ErrorCode.ENTITY_011.value.format(
                            row=ref_source.row,
                            dataset=self.dataset_name,
                            other_scope=deepest_scope_ref.path_as_str(),
                            scope=ref_source.path_as_str(),
                        )
                    )
                else:  # variable
                    raise PyXFormError(
                        ErrorCode.ENTITY_012.value.format(
                            row=self.row_number,
                            dataset=self.dataset_name,
                            other_scope=deepest_scope_ref.path_as_str(),
                            scope=ref_source.path_as_str(),
                            question=ref_source.question_name,
                        )
                    )

            if (
                ref_source.property_name is not None  # save_to
                and deepest_scope_boundary != scope_boundary
            ):
                raise PyXFormError(
                    ErrorCode.ENTITY_011.value.format(
                        row=ref_source.row,
                        dataset=self.dataset_name,
                        other_scope=requested_ref.path_as_str(),
                        scope=ref_source.path_as_str(),
                    )
                )

        return AllocationRequest(
            scope_path=deepest_scope_boundary,
            dataset_name=self.dataset_name,
            requested_path=requested_ref.path,
            sorting_key=(int(bool(deepest_saveto)), len(requested_ref.path.nodes)),
            entity_row_number=self.row_number,
        )


class AllocationRequest(NamedTuple):
    """
    Details required to place an entity in a valid container path.

    Attributes:
        scope_path: The scope boundary for the entity.
        dataset_name: The entity list_name.
        requested_path: The preferred path for the entity based on references.
        sorting_key: First item - if 1 (true), there are save_tos among the references.
          Second item - the length of the requested path.
        entity_row_number: The entity sheet row number of the entity.
    """

    scope_path: ContainerPath
    dataset_name: str
    requested_path: ContainerPath
    sorting_key: tuple[int, int]
    entity_row_number: int


def get_entity_declaration(row: dict, row_number: int) -> dict[str, Any]:
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
    :param row_number: The sheet row number as a user would see it, counting from row 1.
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
            ErrorCode.ENTITY_007.value.format(row=row_number, dataset=dataset_name)
        )

    if entity_id and create_if and not update_if:
        raise PyXFormError(
            ErrorCode.ENTITY_006.value.format(row=row_number, dataset=dataset_name)
        )

    if not entity_id and not label:
        raise PyXFormError(
            ErrorCode.ENTITY_005.value.format(row=row_number, dataset=dataset_name)
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
        "__row_number": row_number,
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

        if not entity_id:
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
    entity_references: EntityReferences,
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
        for ref_source in entity_references.references:
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
        entity = get_entity_declaration(row=row, row_number=row_number)
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
    container_path: ContainerPath,
    row: dict[str, Any],
    row_number: int,
    question_name: str,
    entity_declarations: dict[str, dict[str, Any]],
    entity_variable_references: dict[str, dict[str, list[str]]],
    entity_references_by_question: dict[str, EntityReferences],
    is_container_begin: bool,
    is_container_end: bool,
) -> None:
    """
    For each question store the saveto or variable references that link it to an entity.
    """
    # Collect references for later reconciliation, because otherwise the first
    # referent found will determine the scope but there may be deeper refs.
    saveto = row.get(const.BIND, {}).get(const.ENTITIES_SAVETO_NS, "")
    if saveto:
        if not entity_declarations:
            raise PyXFormError(ErrorCode.ENTITY_001.value.format(row=row_number))

        delimiter_count = saveto.count("#")
        if delimiter_count == 1:
            dataset_name, saveto = saveto.split("#", maxsplit=1)
            row[const.BIND][const.ENTITIES_SAVETO_NS] = saveto
        elif delimiter_count > 1:
            raise PyXFormError(ErrorCode.ENTITY_013.value.format(row=row_number))
        else:
            if len(entity_declarations) > 1:
                raise PyXFormError(ErrorCode.ENTITY_008.value.format(row=row_number))

            dataset_name = next(iter(entity_declarations.keys()))

        if dataset_name not in entity_declarations:
            raise PyXFormError(
                ErrorCode.ENTITY_004.value.format(row=row_number, dataset=dataset_name)
            )

        if dataset_name not in entity_references_by_question:
            entity_references_by_question[dataset_name] = EntityReferences(
                dataset_name=dataset_name,
                row_number=entity_declarations[dataset_name]["__row_number"],
            )

        validate_entity_saveto(
            saveto=saveto,
            row_number=row_number,
            is_container_begin=is_container_begin,
            is_container_end=is_container_end,
            entity_references=entity_references_by_question[dataset_name],
        )

        entity_references_by_question[dataset_name].references.append(
            ReferenceSource(path=container_path, row=row_number, property_name=saveto)
        )

    if entity_variable_references and question_name in entity_variable_references:
        for dataset_name in entity_variable_references[question_name]:
            if dataset_name not in entity_references_by_question:
                entity_references_by_question[dataset_name] = EntityReferences(
                    dataset_name=dataset_name,
                    row_number=entity_declarations[dataset_name]["__row_number"],
                )
            entity_references_by_question[dataset_name].references.append(
                ReferenceSource(
                    path=container_path, row=row_number, question_name=question_name
                )
            )


def allocate_entities_to_containers(
    entity_references_by_question: dict[str, EntityReferences],
) -> dict[ContainerPath, str]:
    """
    Get the paths into which the entities will be placed.
    """
    allocations = {}
    scope_paths = defaultdict(list)

    # Group requests by container scope.
    for entity_references in entity_references_by_question.values():
        req = entity_references.get_allocation_request()
        scope_paths[req.scope_path].append(req)

    # Assign the requests to available allowed container nodes.
    for scope_path, requests in scope_paths.items():
        scope_path_depth_limit = len(scope_path.nodes) - 1

        # Prioritise save_to references but otherwise try to put deepest allocation first.
        for req in sorted(requests, key=lambda x: x.sorting_key, reverse=True):
            placed = False

            # Attempt to place as low as possible, but try going up to the highest allowed.
            for depth in range(req.sorting_key[1], scope_path_depth_limit, -1):
                current_path = ContainerPath(req.requested_path.nodes[:depth])

                if current_path in allocations:
                    # Request with a save_to wants a group that already has an entity.
                    if req.sorting_key[0] == 1:
                        break
                else:
                    allocations[current_path] = req.dataset_name
                    placed = True
                    break

            if not placed:
                raise PyXFormError(
                    ErrorCode.ENTITY_009.value.format(
                        row=req.entity_row_number,
                        scope=f"/{'/'.join(p.name for p in scope_path.nodes)}",
                    )
                )

    return allocations


def inject_entities_into_json(
    node: dict[str, Any],
    allocations: dict[ContainerPath, str],
    entity_declarations: dict[str, dict[str, Any]],
    current_path: ContainerPath,
    search_prefixes: set[ContainerPath],
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
        entity_decl = entity_declarations[dataset_name]
        if has_repeat_ancestor:
            id_attr = next(
                iter(c for c in entity_decl[const.CHILDREN] if c[const.NAME] == "id"),
                None,
            )
            if id_attr and len(id_attr["actions"]) == 1:
                new_repeat = action.ActionLibrary.setvalue_new_repeat.value.to_dict()
                new_repeat["value"] = id_attr["actions"][0]["value"]
                id_attr["actions"].append(new_repeat)

        if const.CHILDREN not in node:
            node[const.CHILDREN] = []

        node[const.CHILDREN].append(get_meta_group(children=[entity_decl]))
        entities_allocated.add(dataset_name)

    for child in node.get(const.CHILDREN, []):
        child_name = child.get(const.NAME)
        child_type = child.get(const.TYPE)
        if child_name and child_type in {const.GROUP, const.REPEAT}:
            child_path = ContainerPath(
                (*current_path.nodes, ContainerNode(name=child_name, type=child_type))
            )
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
    allocations: dict[ContainerPath, str],
) -> set[ContainerPath]:
    """
    Get all the relevant path prefixes to help reduce the path search space.

    :param allocations: The entity path allocations.
    :return: path prefixes like (a, b, c) -> ((a,), (a, b), (a, b, c))
    """
    active = set()
    for path in allocations.keys():
        # Add every prefix of the path to the set
        for i in range(1, len(path.nodes) + 1):
            active.add(ContainerPath(path.nodes[:i]))
    return active


def apply_entities_declarations(
    entity_declarations: dict[str, dict[str, Any]],
    entity_references_by_question: dict[str, EntityReferences],
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
      are referred to, structured as `{dataset_name: EntityReferences}`.
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
                p.type == const.REPEAT for i in allocations.keys() for p in i.nodes
            )
            has_repeat_ancestor = json_dict.get(const.TYPE) == const.REPEAT
            json_dict = inject_entities_into_json(
                node=json_dict,
                allocations=allocations,
                entity_declarations=entity_declarations,
                current_path=ContainerPath.default(),
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

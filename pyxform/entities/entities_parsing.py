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

    def __str__(self):
        return self.path_as_str()

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

    def get_scope_boundary(self) -> "ContainerPath":
        """
        Get the full path to the nearest ancestor boundary scope node.
        """
        for i in range(len(self.nodes) - 1, -1, -1):
            if self.nodes[i].type in {const.REPEAT, const.SURVEY}:
                return ContainerPath(self.nodes[: i + 1])
        return ContainerPath.default()

    def get_scope_boundary_node_count(self) -> int:
        """
        Count boundary nodes from the root to the parent container.

        If zero, the boundary is the root node.
        """
        return sum(
            1
            for i in range(len(self.nodes) - 1, 0, -1)
            if self.nodes[i].type == const.REPEAT
        )

    def get_scope_boundary_subpath_node_count(self) -> int:
        """
        Count containers from the parent container to the nearest ancestor boundary scope.

        If zero, the parent is a boundary node.
        """
        count = 0
        for i in range(len(self.nodes) - 1, -1, -1):
            if self.nodes[i].type in {const.REPEAT, const.SURVEY}:
                break
            count += 1
        return count

    def path_as_str(self) -> str:
        return f"/{'/'.join(p.name for p in self.nodes)}"


@dataclass(frozen=True, slots=True)
class ReferenceSource:
    path: ContainerPath
    row: int
    property_name: str | None = None
    question_name: str | None = None

    def __post_init__(self):
        if self.property_name is None and self.question_name is None:
            raise PyXFormError(
                ErrorCode.INTERNAL_002.value.format(path=self.path.path_as_str())
            )


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
        deepest_container_ref = None
        deepest_saveto = None
        saveto_lineages = {}
        boundaries = []

        # Find the request constraints for this entity.
        for ref in self.references:
            ref_subpath_length = ref.path.get_scope_boundary_subpath_node_count()

            boundary = ref.path.get_scope_boundary()
            boundary_length = boundary.get_scope_boundary_node_count()
            if (
                deepest_scope_boundary is None
                or boundary_length
                > deepest_scope_boundary.get_scope_boundary_node_count()
            ):
                # Found a deeper scope so set deepest container/saveto to the current ref.
                if boundary != deepest_scope_boundary:
                    deepest_container_ref = ref
                    if ref.property_name is not None:
                        deepest_saveto = ref
                deepest_scope_boundary = boundary
                deepest_scope_ref = ref

            boundaries.append((ref, boundary, len(boundary.nodes)))

            # Deepest container not set, or in deepest scope and current ref is deeper.
            if deepest_container_ref is None or (
                boundary == deepest_scope_boundary
                and ref_subpath_length
                > deepest_container_ref.path.get_scope_boundary_subpath_node_count()
            ):
                deepest_container_ref = ref

            if ref.property_name is not None:
                saveto_lineages[ref.path] = None
                # Deepest saveto not set, or in deepest scope and current ref is deeper.
                if deepest_saveto is None or (
                    boundary == deepest_scope_boundary
                    and ref_subpath_length
                    > deepest_saveto.path.get_scope_boundary_subpath_node_count()
                ):
                    deepest_saveto = ref

        # Prioritise saveto since they must be in the nearest container with an entity.
        if deepest_saveto:
            requested_path = deepest_saveto.path
        else:
            requested_path = deepest_container_ref.path

        if saveto_lineages:
            # Uses overall path length here since the common path has to align overall.
            min_len = min(len(p.nodes) for p in saveto_lineages)
            any_ref = next(iter(saveto_lineages))
            common_path = ContainerPath(any_ref.nodes[:min_len])

            if len(saveto_lineages) > 1:
                for i in range(min_len):
                    target = any_ref.nodes[i]
                    for j in saveto_lineages:
                        if j.nodes[i] != target:
                            common_path = ContainerPath(any_ref.nodes[:i])
                            break

                # Use the deepest scope, or the deepest container in the deepest scope.
                # (neither are necessarily the same as the longest path)
                requested_path = max(
                    (deepest_saveto.path.get_scope_boundary(), common_path),
                    key=lambda x: (
                        x.get_scope_boundary_node_count(),
                        x.get_scope_boundary_subpath_node_count(),
                    ),
                )
            else:
                requested_path = common_path

        requested_path_scope_boundary = requested_path.get_scope_boundary()

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
                            other_scope=deepest_scope_ref.path.path_as_str(),
                            scope=ref_source.path.path_as_str(),
                        )
                    )
                else:  # variable
                    raise PyXFormError(
                        ErrorCode.ENTITY_012.value.format(
                            row=self.row_number,
                            dataset=self.dataset_name,
                            other_scope=deepest_scope_ref.path.path_as_str(),
                            scope=ref_source.path.path_as_str(),
                            question=ref_source.question_name,
                        )
                    )

            if (
                ref_source.property_name is not None  # save_to
                and requested_path_scope_boundary != scope_boundary
            ):
                raise PyXFormError(
                    ErrorCode.ENTITY_011.value.format(
                        row=ref_source.row,
                        dataset=self.dataset_name,
                        other_scope=requested_path.path_as_str(),
                        scope=ref_source.path.path_as_str(),
                    )
                )

        return AllocationRequest(
            scope_path=deepest_scope_boundary,
            dataset_name=self.dataset_name,
            requested_path=requested_path,
            requested_path_length=len(requested_path.nodes),
            entity_row_number=self.row_number,
            saveto_lineages=saveto_lineages,
        )


class AllocationRequest(NamedTuple):
    """
    Details required to place an entity in a valid container path.

    Attributes:
        scope_path: The scope boundary for the entity.
        dataset_name: The entity list_name.
        requested_path: The preferred path for the entity based on references.
        requested_path_length: Count of container nodes in the requested_path.
        entity_row_number: The entity sheet row number of the entity.
        saveto_lineages: The full paths of all saveto references for the entity.
    """

    scope_path: ContainerPath
    dataset_name: str
    requested_path: ContainerPath
    requested_path_length: int
    entity_row_number: int
    saveto_lineages: dict[ContainerPath, None]


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

    dataset_name = row.get(EC.DATASET, None)
    entity_id = row.get(EC.ENTITY_ID, None)
    create_if = row.get(EC.CREATE_IF, None)
    update_if = row.get(EC.UPDATE_IF, None)
    label = row.get(EC.LABEL, None)

    validate_dataset_name(dataset_name=dataset_name, row_number=row_number)
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

    variable_references = set()
    for column in (entity_id, create_if, update_if, label):
        if column is not None:
            references = parse_pyxform_references(value=column)
            if references:
                for ref in references:
                    variable_references.add(ref.name)

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
        "__variable_references": variable_references,
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


def validate_dataset_name(dataset_name: str | None, row_number: int) -> None:
    """
    Check the dataset_name passes all naming rules.

    :param dataset_name: The value to check.
    :param row_number: The entities sheet row number.
    """
    if not dataset_name:
        raise PyXFormError(ErrorCode.NAMES_015.value.format(row=row_number))
    elif dataset_name.startswith(const.ENTITIES_RESERVED_PREFIX):
        raise PyXFormError(
            ErrorCode.NAMES_010.value.format(
                sheet=const.ENTITIES, row=row_number, column=EC.DATASET.value
            )
        )
    elif "." in dataset_name:
        raise PyXFormError(
            ErrorCode.NAMES_011.value.format(
                sheet=const.ENTITIES, row=row_number, column=EC.DATASET.value
            )
        )
    elif not is_xml_tag(dataset_name):
        raise PyXFormError(
            ErrorCode.NAMES_008.value.format(
                sheet=const.ENTITIES, row=row_number, column=EC.DATASET.value
            )
        )


def validate_saveto(
    saveto: str | None,
    row_number: int,
    is_container_begin: bool,
    is_container_end: bool,
    entity_references: EntityReferences,
) -> None:
    """
    Check the saveto passes all naming rules.

    :param saveto: The value to check.
    :param row_number: The entities sheet row number.
    :param is_container_begin: If True, the row type is a "begin_repeat" or "begin_group"
      or some parsed alias of these.
    :param is_container_end: If True, the row type is a "end_repeat" or "end_group"
      or some parsed alias of these.
    :param entity_references: All entity references parsed so far in the form.
    """
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
    entity_declarations: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    """
    Group variable references in the entities delarations by question_name.

    :return: dict[question_name: str, list[dataset_name: str]]
    """
    variable_references = defaultdict(list)
    for dataset_name, declaration in entity_declarations.items():
        # Not needed anywhere else so remove from declaration.
        references = declaration.pop("__variable_references", None)
        if references:
            for question_name in references:
                variable_references[question_name].append(dataset_name)

    return variable_references


def get_entity_references_by_question(
    container_path: ContainerPath,
    row: dict[str, Any],
    row_number: int,
    question_name: str,
    entity_declarations: dict[str, dict[str, Any]],
    entity_variable_references: dict[str, list[str]],
    entity_references_by_question: dict[str, EntityReferences],
    is_container_begin: bool,
    is_container_end: bool,
) -> None:
    """
    For each question store the saveto or variable references that link it to an entity.
    """
    # Collect references for later reconciliation, because otherwise the first
    # referent found will determine the scope but there may be deeper refs.
    saveto = row.get(const.BIND, {}).get(const.ENTITIES_SAVETO_NS)
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

        validate_saveto(
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
    entity_declarations: dict[str, dict[str, Any]],
    entity_references_by_question: dict[str, EntityReferences],
) -> dict[ContainerPath, str]:
    """
    Get the paths into which the entities will be placed.
    """
    allocations: dict[ContainerPath, str] = {}
    scope_paths: defaultdict[ContainerPath, list[AllocationRequest]] = defaultdict(list)
    survey_path = ContainerPath.default()

    # Group requests by container scope.
    for entity_references in entity_references_by_question.values():
        req = entity_references.get_allocation_request()
        scope_paths[req.scope_path].append(req)

    # For unreferenced declarations, default to the survey scope.
    for dataset_name, declaration in entity_declarations.items():
        if dataset_name not in entity_references_by_question:
            scope_paths[survey_path].append(
                AllocationRequest(
                    scope_path=survey_path,
                    dataset_name=dataset_name,
                    requested_path=survey_path,
                    requested_path_length=1,
                    entity_row_number=declaration["__row_number"],
                    saveto_lineages={},
                )
            )

    # If there's only one entity, and it's scope is the survey, then allocate to the survey.
    # (avoids unnecessarily nested meta/entity blocks, for spec 2024.1.0 compatibility)
    if len(scope_paths) == 1:
        scope_path, requests = next(iter(scope_paths.items()))
        if scope_path == survey_path and len(requests) == 1:
            return {survey_path: requests[0].dataset_name}

    # Assign the requests to available allowed container nodes.
    reserved_paths: dict[ContainerPath, str] = {}
    for scope_path, requests in scope_paths.items():
        scope_path_depth_limit = len(scope_path.nodes) - 1

        # Prioritise save_to references but otherwise try to put deepest allocation first.
        for req in sorted(requests, key=lambda x: x.entity_row_number):
            conflict_dataset = None

            # Attempt to place as low as possible, but try going up to the highest allowed.
            for depth in range(req.requested_path_length, scope_path_depth_limit, -1):
                current_path = ContainerPath(req.requested_path.nodes[:depth])

                conflict_dataset = allocations.get(
                    current_path, reserved_paths.get(current_path)
                )
                if conflict_dataset is not None:
                    # May be n conflicts but search stops at the first one (row order).
                    conflict_dataset_saveto = next(
                        (reserved_paths.get(i) for i in req.saveto_lineages), None
                    )
                    # Request with save_tos wants a container reserved by another entity.
                    if conflict_dataset_saveto:
                        conflict_dataset = conflict_dataset_saveto
                        break
                    # Otherwise continue the search for an available container.
                    else:
                        continue
                else:
                    allocations[current_path] = req.dataset_name
                    reserved_paths[current_path] = req.dataset_name
                    # Reserve all nodes between each lineage leaf and the assigned node.
                    for lineage in req.saveto_lineages:
                        for i in range(
                            len(lineage.nodes), len(current_path.nodes) - 1, -1
                        ):
                            reserved_paths[ContainerPath(lineage.nodes[:i])] = (
                                req.dataset_name
                            )
                    break

            if conflict_dataset is not None:
                raise PyXFormError(
                    ErrorCode.ENTITY_009.value.format(
                        row=req.entity_row_number,
                        scope=scope_path.path_as_str(),
                        other_row=entity_declarations[conflict_dataset]["__row_number"],
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
    :return: The json_dict is modified in-place
    """
    allocations = allocate_entities_to_containers(
        entity_declarations=entity_declarations,
        entity_references_by_question=entity_references_by_question,
    )
    json_dict = inject_entities_into_json(
        node=json_dict,
        allocations=allocations,
        entity_declarations=entity_declarations,
        current_path=ContainerPath.default(),
        search_prefixes=get_search_prefixes(allocations=allocations),
        has_repeat_ancestor=json_dict.get(const.TYPE) == const.REPEAT,
    )

    if len(entity_declarations) > 1 or any(
        i.get_scope_boundary_node_count() > 0 for i in allocations.keys()
    ):
        json_dict[const.ENTITY_VERSION] = const.EntityVersion.v2025_1_0
    else:
        json_dict[const.ENTITY_VERSION] = const.EntityVersion.v2024_1_0

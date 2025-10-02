from typing import TYPE_CHECKING

from pyxform import constants as const
from pyxform.elements import action
from pyxform.entities.label import Label
from pyxform.section import Section
from pyxform.survey_element import SURVEY_ELEMENT_FIELDS
from pyxform.utils import combine_lists, node

if TYPE_CHECKING:
    from pyxform.survey import Survey


EC = const.EntityColumns
ENTITY_EXTRA_FIELDS = (const.PARAMETERS,)
ENTITY_FIELDS = (*SURVEY_ELEMENT_FIELDS, *ENTITY_EXTRA_FIELDS)


class EntityDeclaration(Section):
    """
    An entity declaration includes an entity instance node with optional label child, some attributes, and corresponding bindings.

    The ODK XForms Entities specification can be found at https://getodk.github.io/xforms-spec/entities

    XLSForm uses a combination of the entity_id, create_if and update_if columns to determine what entity action is intended:
        id    create  update  result
        1     0       0       always update
        1     0       1       update based on condition
        1     1       0       error, id only acceptable when updating
        1     1       1       include conditions for create and update, user's responsibility to make sure they're exclusive
        0     0       0       always create
        0     0       1       error, need id to update
        0     1       0       create based on condition
        0     1       1       error, need id to update
    """

    __slots__ = ENTITY_EXTRA_FIELDS

    @staticmethod
    def get_slot_names() -> tuple[str, ...]:
        return ENTITY_FIELDS

    def __init__(self, name: str, type: str, parameters: dict, **kwargs):
        super().__init__(name=name, type=type, **kwargs)
        self.parameters: dict = parameters
        self.children: list[Label] | None = None

        choices = combine_lists(
            a=kwargs.pop("children", None), b=kwargs.pop(const.CHILDREN, None)
        )
        if choices:
            self.children = [Label(name="label", **c) for c in choices]
            self._link_children()
        else:
            self.children = []

    def xml_instance(self, survey: "Survey", **kwargs):
        parameters = self.parameters

        attributes = {
            EC.DATASET.value: parameters.get(EC.DATASET, ""),
            "id": "",
        }

        entity_id_expression = parameters.get(EC.ENTITY_ID, None)
        create_condition = parameters.get(EC.CREATE_IF, None)
        update_condition = parameters.get(EC.UPDATE_IF, None)

        if entity_id_expression:
            attributes["update"] = "1"
            attributes["baseVersion"] = ""
            attributes["trunkVersion"] = ""
            attributes["branchId"] = ""

        if create_condition or (not update_condition and not entity_id_expression):
            attributes["create"] = "1"

        return super().xml_instance(survey=survey, **attributes)

    def xml_bindings(self, survey: "Survey"):
        """
        See the class comment for an explanation of the logic for generating bindings.
        """
        parameters = self.parameters
        entity_id_expression = parameters.get(EC.ENTITY_ID, None)
        create_condition = parameters.get(EC.CREATE_IF, None)
        update_condition = parameters.get(EC.UPDATE_IF, None)

        if create_condition:
            yield self._get_bind_node(survey, create_condition, "/@create")

        yield self._get_id_bind_node(survey, entity_id_expression)

        if update_condition:
            yield self._get_bind_node(survey, update_condition, "/@update")

        if entity_id_expression:
            dataset_name = parameters.get(EC.DATASET, "")
            entity = f"instance('{dataset_name}')/root/item[name={entity_id_expression}]"
            yield self._get_bind_node(survey, f"{entity}/__version", "/@baseVersion")
            yield self._get_bind_node(
                survey, f"{entity}/__trunkVersion", "/@trunkVersion"
            )
            yield self._get_bind_node(survey, f"{entity}/__branchId", "/@branchId")

        for e in self.iter_descendants():
            if e is not self:
                yield from e.xml_bindings(survey=survey)

    def _get_id_bind_node(self, survey, entity_id_expression):
        extra_attrs = {}

        if entity_id_expression:
            extra_attrs["calculate"] = survey.insert_xpaths(
                text=entity_id_expression, context=self
            )

        return node(
            const.BIND,
            nodeset=f"{self.get_xpath()}/@id",
            type="string",
            readonly="true()",
            **extra_attrs,
        )

    def xml_actions(self, survey: "Survey", in_repeat: bool = False):
        if self.parameters.get(EC.CREATE_IF, None) or not self.parameters.get(
            EC.ENTITY_ID, None
        ):
            if in_repeat:
                setvalue_action = action.ActionLibrary.setvalue_new_repeat.value
            else:
                setvalue_action = action.ActionLibrary.setvalue_first_load.value

            yield action.ACTION_CLASSES[setvalue_action.name](
                ref=f"{self.get_xpath()}/@id",
                event=action.Event(setvalue_action.event),
                value="uuid()",
            ).node()

    def _get_bind_node(self, survey, expression, destination):
        return node(
            const.BIND,
            nodeset=f"{self.get_xpath()}{destination}",
            calculate=survey.insert_xpaths(text=expression, context=self),
            type="string",
            readonly="true()",
        )

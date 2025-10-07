from pyxform import constants as const
from pyxform.section import Section
from pyxform.survey_element import SURVEY_ELEMENT_FIELDS
from pyxform.survey_elements.attribute import Attribute
from pyxform.survey_elements.label import Label
from pyxform.utils import combine_lists

EC = const.EntityColumns
ENTITY_EXTRA_FIELDS = (const.CHILDREN,)
ENTITY_FIELDS = (*SURVEY_ELEMENT_FIELDS, *ENTITY_EXTRA_FIELDS)
CHILD_TYPES = {"label": Label, "attribute": Attribute}


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

    def __init__(self, name: str, type: str, **kwargs):
        super().__init__(name=name, type=type, **kwargs)
        self.children: list[Label | Attribute] = []

        children = combine_lists(
            a=kwargs.pop("children", None), b=kwargs.pop(const.CHILDREN, None)
        )
        if children:
            self.children = [CHILD_TYPES[c["type"]](**c) for c in children]
            self._link_children()

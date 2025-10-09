from itertools import chain
from typing import TYPE_CHECKING

from pyxform import constants as const
from pyxform.survey_element import SURVEY_ELEMENT_FIELDS, SurveyElement
from pyxform.utils import node

if TYPE_CHECKING:
    from pyxform.survey import Survey


LABEL_EXTRA_FIELDS = (
    const.BIND,
    const.TYPE,
)
LABEL_FIELDS = (*SURVEY_ELEMENT_FIELDS, *LABEL_EXTRA_FIELDS)


class Label(SurveyElement):
    @staticmethod
    def get_slot_names() -> tuple[str, ...]:
        return LABEL_FIELDS

    def __init__(self, fields: tuple[str, ...] | None = None, **kwargs):
        # Structure
        self.bind: dict | None = None
        self.type: str | None = None

        if fields is None:
            fields = LABEL_FIELDS
        else:
            fields = chain(LABEL_EXTRA_FIELDS, fields)
        super().__init__(fields=fields, **kwargs)

    def xml_instance(self, survey: "Survey", **kwargs):
        return node(self.name)

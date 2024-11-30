"""
ExternalInstance class module
"""

from typing import TYPE_CHECKING

from pyxform import constants
from pyxform.survey_element import SURVEY_ELEMENT_FIELDS, SurveyElement

if TYPE_CHECKING:
    from pyxform.survey import Survey


EXTERNAL_INSTANCE_EXTRA_FIELDS = (constants.TYPE,)
EXTERNAL_INSTANCE_FIELDS = (*SURVEY_ELEMENT_FIELDS, *EXTERNAL_INSTANCE_EXTRA_FIELDS)


class ExternalInstance(SurveyElement):
    __slots__ = EXTERNAL_INSTANCE_EXTRA_FIELDS

    @staticmethod
    def get_slot_names() -> tuple[str, ...]:
        return EXTERNAL_INSTANCE_FIELDS

    def __init__(self, name: str, type: str, **kwargs):
        self.type: str = type
        super().__init__(name=name, **kwargs)

    def xml_control(self, survey: "Survey"):
        """
        No-op since there is no associated form control to place under <body/>.

        Exists here because there's a soft abstractmethod in SurveyElement.
        """

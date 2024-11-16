"""
ExternalInstance class module
"""

from typing import TYPE_CHECKING

from pyxform.survey_element import SurveyElement

if TYPE_CHECKING:
    from pyxform.survey import Survey


class ExternalInstance(SurveyElement):
    def xml_control(self, survey: "Survey"):
        """
        No-op since there is no associated form control to place under <body/>.

        Exists here because there's a soft abstractmethod in SurveyElement.
        """

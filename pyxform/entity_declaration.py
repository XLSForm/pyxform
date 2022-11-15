# -*- coding: utf-8 -*-

from pyxform.survey_element import SurveyElement
from pyxform.utils import node


class EntityDeclaration(SurveyElement):
    def xml_instance(self, **kwargs):
        attributes = {}
        attributes["dataset"] = self.get("parameters", {}).get("dataset", "")

        return node("entity", **attributes)

    def xml_control(self):
        """
        No-op since there is no associated form control to place under <body/>.

        Exists here because there's a soft abstractmethod in SurveyElement.
        """
        pass

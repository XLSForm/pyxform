# -*- coding: utf-8 -*-

from pyxform.survey_element import SurveyElement
from pyxform.utils import node


class EntityDeclaration(SurveyElement):
    def xml_instance(self, **kwargs):
        attributes = {}
        attributes["dataset"] = self.get("parameters", {}).get("dataset", "")
        attributes["create"] = "1"

        return node("entity", **attributes)

    def xml_bindings(self):
        bind_dict = {"calculate": self.get("parameters", {}).get("create", "true()")}
        return [node("bind", nodeset=self.get_xpath() + "/@create", **bind_dict)]

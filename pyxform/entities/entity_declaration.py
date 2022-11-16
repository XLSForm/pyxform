# -*- coding: utf-8 -*-

from pyxform.survey_element import SurveyElement
from pyxform.utils import node


class EntityDeclaration(SurveyElement):
    def xml_instance(self, **kwargs):
        attributes = {}
        attributes["dataset"] = self.get("parameters", {}).get("dataset", "")
        attributes["create"] = "1"
        attributes["id"] = ""

        label_node = node("label")
        return node("entity", label_node, **attributes)

    def xml_bindings(self):
        survey = self.get_root()

        create_expr = survey.insert_xpaths(
            self.get("parameters", {}).get("create", "true()"), context=self
        )
        create_bind = {
            "calculate": create_expr,
            "type": "string",
            "readonly": "true()",
        }
        create_node = node("bind", nodeset=self.get_xpath() + "/@create", **create_bind)

        id_bind = {"type": "string", "readonly": "true()"}
        id_node = node("bind", nodeset=self.get_xpath() + "/@id", **id_bind)

        id_setvalue_attrs = {
            "event": "odk-instance-first-load",
            "type": "string",
            "readonly": "true()",
            "value": "uuid()",
        }
        id_setvalue = node("setvalue", ref=self.get_xpath() + "/@id", **id_setvalue_attrs)

        label_expr = survey.insert_xpaths(
            self.get("parameters", {}).get("label", ""), context=self
        )
        label_bind = {
            "calculate": label_expr,
            "type": "string",
            "readonly": "true()",
        }
        label_node = node("bind", nodeset=self.get_xpath() + "/label", **label_bind)
        return [create_node, id_node, id_setvalue, label_node]

# -*- coding: utf-8 -*-

from pyxform.survey_element import SurveyElement
from pyxform.utils import node


class EntityDeclaration(SurveyElement):
    def xml_instance(self, **kwargs):
        attributes = {}
        attributes["dataset"] = self.get("parameters", {}).get("dataset", "")
        attributes["id"] = ""

        entity_id_expression = self.get("parameters", {}).get("entity_id", None)
        create_condition = self.get("parameters", {}).get("create", None)
        update_condition = self.get("parameters", {}).get("update", None)

        if entity_id_expression:
            attributes["update"] = "1"
            attributes["baseVersion"] = ""

        if create_condition or (not (update_condition) and not (entity_id_expression)):
            attributes["create"] = "1"

        if self.get("parameters", {}).get("label", None):
            return node("entity", node("label"), **attributes)
        else:
            return node("entity", **attributes)

    def xml_bindings(self):
        survey = self.get_root()
        entity_id_expression = self.get("parameters", {}).get("entity_id", None)
        create_condition = self.get("parameters", {}).get("create", None)
        update_condition = self.get("parameters", {}).get("update", None)
        label_expression = self.get("parameters", {}).get("label", None)

        bind_nodes = []

        if create_condition:
            bind_nodes.append(self._get_bind_node(survey, create_condition, "/@create"))

        bind_nodes.append(self._get_id_bind_node(survey, entity_id_expression))

        if create_condition or not (entity_id_expression):
            bind_nodes.append(self._get_id_setvalue_node())

        if update_condition:
            bind_nodes.append(self._get_bind_node(survey, update_condition, "/@update"))

        if entity_id_expression:
            dataset_name = self.get("parameters", {}).get("dataset", "")
            base_version_expression = f"instance('{dataset_name}')/root/item[name={entity_id_expression}]/__version"
            bind_nodes.append(
                self._get_bind_node(survey, base_version_expression, "/@baseVersion")
            )

        if label_expression:
            bind_nodes.append(self._get_bind_node(survey, label_expression, "/label"))

        return bind_nodes

    def _get_id_bind_node(self, survey, entity_id_expression):
        id_bind = {"type": "string", "readonly": "true()"}

        if entity_id_expression:
            id_bind["calculate"] = survey.insert_xpaths(
                entity_id_expression, context=self
            )

        return node("bind", nodeset=self.get_xpath() + "/@id", **id_bind)

    def _get_id_setvalue_node(self):
        id_setvalue_attrs = {
            "event": "odk-instance-first-load",
            "type": "string",
            "readonly": "true()",
            "value": "uuid()",
        }

        return node("setvalue", ref=self.get_xpath() + "/@id", **id_setvalue_attrs)

    def _get_bind_node(self, survey, expression, destination):
        expr = survey.insert_xpaths(expression, context=self)
        bind_attrs = {
            "calculate": expr,
            "type": "string",
            "readonly": "true()",
        }

        return node("bind", nodeset=self.get_xpath() + destination, **bind_attrs)

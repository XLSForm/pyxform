from pyxform import constants as const
from pyxform.survey_element import SurveyElement
from pyxform.utils import node

EC = const.EntityColumns


class EntityDeclaration(SurveyElement):
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

    def xml_instance(self, **kwargs):
        parameters = self.get(const.PARAMETERS, {})

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
            if parameters.get(EC.OFFLINE, None):
                attributes["trunkVersion"] = ""
                attributes["branchId"] = ""

        if create_condition or (not update_condition and not entity_id_expression):
            attributes["create"] = "1"

        if parameters.get(EC.LABEL, None):
            return node(const.ENTITY, node(const.LABEL), **attributes)
        else:
            return node(const.ENTITY, **attributes)

    def xml_bindings(self):
        """
        See the class comment for an explanation of the logic for generating bindings.
        """
        survey = self.get_root()
        parameters = self.get(const.PARAMETERS, {})
        entity_id_expression = parameters.get(EC.ENTITY_ID, None)
        create_condition = parameters.get(EC.CREATE_IF, None)
        update_condition = parameters.get(EC.UPDATE_IF, None)
        label_expression = parameters.get(EC.LABEL, None)

        bind_nodes = []

        if create_condition:
            bind_nodes.append(self._get_bind_node(survey, create_condition, "/@create"))

        bind_nodes.append(self._get_id_bind_node(survey, entity_id_expression))

        if create_condition or not entity_id_expression:
            bind_nodes.append(self._get_id_setvalue_node())

        if update_condition:
            bind_nodes.append(self._get_bind_node(survey, update_condition, "/@update"))

        if entity_id_expression:
            dataset_name = parameters.get(EC.DATASET, "")
            entity = f"instance('{dataset_name}')/root/item[name={entity_id_expression}]"
            bind_nodes.append(
                self._get_bind_node(survey, f"{entity}/__version", "/@baseVersion")
            )
            if parameters.get(EC.OFFLINE, None):
                bind_nodes.append(
                    self._get_bind_node(
                        survey, f"{entity}/__trunkVersion", "/@trunkVersion"
                    )
                )
                bind_nodes.append(
                    self._get_bind_node(survey, f"{entity}/__branchId", "/@branchId")
                )

        if label_expression:
            bind_nodes.append(self._get_bind_node(survey, label_expression, "/label"))

        return bind_nodes

    def _get_id_bind_node(self, survey, entity_id_expression):
        id_bind = {const.TYPE: "string", "readonly": "true()"}

        if entity_id_expression:
            id_bind["calculate"] = survey.insert_xpaths(
                entity_id_expression, context=self
            )

        return node(const.BIND, nodeset=self.get_xpath() + "/@id", **id_bind)

    def _get_id_setvalue_node(self):
        id_setvalue_attrs = {
            "event": "odk-instance-first-load",
            const.TYPE: "string",
            "readonly": "true()",
            "value": "uuid()",
        }

        return node("setvalue", ref=self.get_xpath() + "/@id", **id_setvalue_attrs)

    def _get_bind_node(self, survey, expression, destination):
        expr = survey.insert_xpaths(expression, context=self)
        bind_attrs = {
            "calculate": expr,
            const.TYPE: "string",
            "readonly": "true()",
        }

        return node(const.BIND, nodeset=self.get_xpath() + destination, **bind_attrs)

    def xml_control(self):
        raise NotImplementedError()

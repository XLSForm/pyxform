"""
XForm Survey element classes for different question types.
"""

import os.path

from pyxform.constants import (
    EXTERNAL_CHOICES_ITEMSET_REF_LABEL,
    EXTERNAL_CHOICES_ITEMSET_REF_LABEL_GEOJSON,
    EXTERNAL_CHOICES_ITEMSET_REF_VALUE,
    EXTERNAL_CHOICES_ITEMSET_REF_VALUE_GEOJSON,
    EXTERNAL_INSTANCE_EXTENSIONS,
)
from pyxform.errors import PyXFormError
from pyxform.question_type_dictionary import QUESTION_TYPE_DICT
from pyxform.survey_element import SurveyElement
from pyxform.utils import PYXFORM_REFERENCE_REGEX, default_is_dynamic, node


class Question(SurveyElement):
    FIELDS = SurveyElement.FIELDS.copy()
    FIELDS.update(
        {
            "_itemset_multi_language": bool,
            "_itemset_has_media": bool,
            "_itemset_dyn_label": bool,
        }
    )

    def validate(self):
        SurveyElement.validate(self)

        # make sure that the type of this question exists in the
        # question type dictionary.
        if self.type not in QUESTION_TYPE_DICT:
            raise PyXFormError(f"Unknown question type '{self.type}'.")

    def xml_instance(self, **kwargs):
        survey = self.get_root()
        attributes = {}
        attributes.update(self.get("instance", {}))
        for key, value in attributes.items():
            attributes[key] = survey.insert_xpaths(value, self)

        if self.get("default") and not default_is_dynamic(self.default, self.type):
            return node(self.name, str(self.get("default")), **attributes)
        return node(self.name, **attributes)

    def xml_control(self):
        if self.type == "calculate" or (
            ("calculate" in self.bind or self.trigger) and not (self.label or self.hint)
        ):
            nested_setvalues = self.get_root().get_setvalues_for_question_name(self.name)
            if nested_setvalues:
                for setvalue in nested_setvalues:
                    msg = (
                        f"The question ${{{self.name}}} is not user-visible "
                        "so it can't be used as a calculation trigger for "
                        f"question ${{{setvalue[0]}}}."
                    )
                    raise PyXFormError(msg)
            return None

        xml_node = self.build_xml()

        if xml_node:
            self.nest_setvalues(xml_node)

        return xml_node

    def nest_setvalues(self, xml_node):
        nested_setvalues = self.get_root().get_setvalues_for_question_name(self.name)

        if nested_setvalues:
            for setvalue in nested_setvalues:
                setvalue_attrs = {
                    "ref": self.get_root()
                    .insert_xpaths(f"${{{setvalue[0]}}}", self.get_root())
                    .strip(),
                    "event": "xforms-value-changed",
                }
                if not setvalue[1] == "":
                    setvalue_attrs["value"] = self.get_root().insert_xpaths(
                        setvalue[1], self
                    )

                setvalue_node = node("setvalue", **setvalue_attrs)

                xml_node.appendChild(setvalue_node)

    def build_xml(self):
        return None


class InputQuestion(Question):
    """
    This control string is the same for: strings, integers, decimals,
    dates, geopoints, barcodes ...
    """

    def build_xml(self):
        control_dict = self.control
        label_and_hint = self.xml_label_and_hint()
        survey = self.get_root()
        # Resolve field references in attributes
        for key, value in control_dict.items():
            control_dict[key] = survey.insert_xpaths(value, self)
        control_dict["ref"] = self.get_xpath()

        result = node(**control_dict)
        if label_and_hint:
            for element in self.xml_label_and_hint():
                result.appendChild(element)

        # Input types are used for selects with external choices sheets.
        if self["query"]:
            choice_filter = self.get("choice_filter")
            query = "instance('" + self["query"] + "')/root/item"
            choice_filter = survey.insert_xpaths(choice_filter, self, True)
            if choice_filter:
                query += "[" + choice_filter + "]"
            result.setAttribute("query", query)
        return result


class TriggerQuestion(Question):
    def build_xml(self):
        control_dict = self.control
        survey = self.get_root()
        # Resolve field references in attributes
        for key, value in control_dict.items():
            control_dict[key] = survey.insert_xpaths(value, self)
        control_dict["ref"] = self.get_xpath()
        return node("trigger", *self.xml_label_and_hint(), **control_dict)


class UploadQuestion(Question):
    def _get_media_type(self):
        return self.control["mediatype"]

    def build_xml(self):
        control_dict = self.control
        survey = self.get_root()
        # Resolve field references in attributes
        for key, value in control_dict.items():
            control_dict[key] = survey.insert_xpaths(value, self)
        control_dict["ref"] = self.get_xpath()
        control_dict["mediatype"] = self._get_media_type()
        return node("upload", *self.xml_label_and_hint(), **control_dict)


class Option(SurveyElement):
    def xml_value(self):
        return node("value", self.name)

    def xml(self):
        item = node("item")
        self.xml_label()
        item.appendChild(self.xml_label())
        item.appendChild(self.xml_value())

        return item

    def validate(self):
        pass

    def xml_control(self):
        raise NotImplementedError()

    def _translation_path(self, display_element):
        choice_itext_id = self.get("_choice_itext_id")
        if choice_itext_id is not None:
            return choice_itext_id
        return super()._translation_path(display_element=display_element)


class MultipleChoiceQuestion(Question):
    def __init__(self, **kwargs):
        kwargs_copy = kwargs.copy()
        # Notice that choices can be specified under choices or children.
        # I'm going to try to stick to just choices.
        # Aliases in the json format will make it more difficult
        # to use going forward.
        choices = list(kwargs_copy.pop("choices", [])) + list(
            kwargs_copy.pop("children", [])
        )
        Question.__init__(self, **kwargs_copy)
        for choice in choices:
            self.add_choice(**choice)

    def add_choice(self, **kwargs):
        option = Option(**kwargs)
        self.add_child(option)

    def validate(self):
        Question.validate(self)
        descendants = self.iter_descendants()
        next(descendants)  # iter_descendants includes self; we need to pop it

        for choice in descendants:
            choice.validate()

    def build_xml(self):
        if self.bind["type"] not in ["string", "odk:rank"]:
            raise PyXFormError("""Invalid value for `self.bind["type"]`.""")
        survey = self.get_root()
        control_dict = self.control.copy()
        # Resolve field references in attributes
        for key, value in control_dict.items():
            control_dict[key] = survey.insert_xpaths(value, self)
        control_dict["ref"] = self.get_xpath()

        result = node(**control_dict)
        for element in self.xml_label_and_hint():
            result.appendChild(element)

        # itemset are only supposed to be strings,
        # check to prevent the rare dicts that show up
        if self["itemset"] and isinstance(self["itemset"], str):
            choice_filter = self.get("choice_filter")

            itemset, file_extension = os.path.splitext(self["itemset"])
            itemset_value_ref = self.parameters.get(
                "value",
                EXTERNAL_CHOICES_ITEMSET_REF_VALUE_GEOJSON
                if file_extension == ".geojson"
                else EXTERNAL_CHOICES_ITEMSET_REF_VALUE,
            )
            itemset_label_ref = self.parameters.get(
                "label",
                EXTERNAL_CHOICES_ITEMSET_REF_LABEL_GEOJSON
                if file_extension == ".geojson"
                else EXTERNAL_CHOICES_ITEMSET_REF_LABEL,
            )

            multi_language = self.get("_itemset_multi_language", False)
            has_media = self.get("_itemset_has_media", False)
            has_dyn_label = self.get("_itemset_dyn_label", False)
            is_previous_question = bool(
                PYXFORM_REFERENCE_REGEX.search(self.get("itemset"))
            )

            if file_extension in EXTERNAL_INSTANCE_EXTENSIONS:
                pass
            elif not multi_language and not has_media and not has_dyn_label:
                itemset = self["itemset"]
            else:
                itemset = self["itemset"]
                itemset_label_ref = "jr:itext(itextId)"

            choice_filter = survey.insert_xpaths(
                choice_filter, self, True, is_previous_question
            )
            if is_previous_question:
                path = (
                    survey.insert_xpaths(self["itemset"], self, reference_parent=True)
                    .strip()
                    .split("/")
                )
                nodeset = "/".join(path[:-1])
                itemset_value_ref = path[-1]
                itemset_label_ref = path[-1]
                if choice_filter:
                    choice_filter = choice_filter.replace(
                        "current()/" + nodeset, "."
                    ).replace(nodeset, ".")
                else:
                    # Choices must have a value. Filter out repeat instances without
                    # an answer for the linked question
                    name = path[-1]
                    choice_filter = f"./{name} != ''"
            else:
                nodeset = "instance('" + itemset + "')/root/item"

            if choice_filter:
                nodeset += "[" + choice_filter + "]"

            if self["parameters"]:
                params = self["parameters"]

                if "randomize" in params and params["randomize"] == "true":
                    nodeset = "randomize(" + nodeset

                    if "seed" in params:
                        if params["seed"].startswith("${"):
                            nodeset = (
                                nodeset
                                + ", "
                                + survey.insert_xpaths(params["seed"], self).strip()
                            )
                        else:
                            nodeset = nodeset + ", " + params["seed"]

                    nodeset += ")"

            itemset_children = [
                node("value", ref=itemset_value_ref),
                node("label", ref=itemset_label_ref),
            ]
            result.appendChild(node("itemset", *itemset_children, nodeset=nodeset))
        else:
            for child in self.children:
                result.appendChild(child.xml())

        return result


class SelectOneQuestion(MultipleChoiceQuestion):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._dict[self.TYPE] = "select one"


class Tag(SurveyElement):
    def __init__(self, **kwargs):
        kwargs_copy = kwargs.copy()
        choices = kwargs_copy.pop("choices", []) + kwargs_copy.pop("children", [])

        super().__init__(**kwargs_copy)

        if choices:
            self.children = []

            for choice in choices:
                option = Option(**choice)
                self.add_child(option)

    def xml(self):
        result = node("tag", key=self.name)
        self.xml_label()
        result.appendChild(self.xml_label())
        for choice in self.children:
            result.appendChild(choice.xml())

        return result

    def validate(self):
        pass

    def xml_control(self):
        raise NotImplementedError()


class OsmUploadQuestion(UploadQuestion):
    def __init__(self, **kwargs):
        kwargs_copy = kwargs.copy()
        tags = kwargs_copy.pop("tags", []) + kwargs_copy.pop("children", [])

        super().__init__(**kwargs_copy)

        if tags:
            self.children = []

            for tag in tags:
                self.add_tag(**tag)

    def add_tag(self, **kwargs):
        tag = Tag(**kwargs)
        self.add_child(tag)

    def build_xml(self):
        control_dict = self.control
        control_dict["ref"] = self.get_xpath()
        control_dict["mediatype"] = self._get_media_type()
        result = node("upload", *self.xml_label_and_hint(), **control_dict)

        for osm_tag in self.children:
            result.appendChild(osm_tag.xml())

        return result


class RangeQuestion(Question):
    def build_xml(self):
        control_dict = self.control
        label_and_hint = self.xml_label_and_hint()
        survey = self.get_root()
        # Resolve field references in attributes
        for key, value in control_dict.items():
            control_dict[key] = survey.insert_xpaths(value, self)
        control_dict["ref"] = self.get_xpath()
        params = self.get("parameters", {})
        control_dict.update(params)
        result = node(**control_dict)
        if label_and_hint:
            for element in self.xml_label_and_hint():
                result.appendChild(element)

        return result

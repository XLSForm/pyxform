"""
xform2json module - Transform an XForm to a JSON dictionary.
"""

import copy
import json
import logging
import re
from collections.abc import Mapping
from operator import itemgetter
from typing import Any
from xml.etree.ElementTree import Element

from defusedxml.ElementTree import ParseError, XMLParser, fromstring, parse

from pyxform import builder
from pyxform.constants import NSMAP
from pyxform.errors import PyXFormError

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


QUESTION_TYPES = {
    "select": "select all that apply",
    "select1": "select one",
    "int": "integer",
    "dateTime": "datetime",
    "string": "text",
}


# {{{ http://code.activestate.com/recipes/573463/ (r7)
class XmlDictObject(dict):
    """
    Adds object like functionality to the standard dictionary.
    """

    def __init__(self, initdict=None):
        if initdict is None:
            initdict = {}
        dict.__init__(self, initdict)

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __setattr__(self, item, value):
        self.__setitem__(item, value)

    def __str__(self):
        if "_text" in self:
            return self.__getitem__("_text")
        else:
            return ""

    @staticmethod
    def wrap(x):
        """
        Static method to wrap a dictionary recursively as an XmlDictObject
        """

        if isinstance(x, dict):
            return XmlDictObject((k, XmlDictObject.Wrap(v)) for (k, v) in iter(x.items()))
        elif isinstance(x, list):
            return [XmlDictObject.Wrap(v) for v in x]
        else:
            return x

    @staticmethod
    def _un_wrap(x):
        if isinstance(x, dict):
            return {k: XmlDictObject._un_wrap(v) for k, v in x.items()}
        elif isinstance(x, list):
            return [XmlDictObject._un_wrap(v) for v in x]
        else:
            return x

    def un_wrap(self):
        """
        Recursively converts an XmlDictObject to a standard dictionary
        and returns the result.
        """

        return XmlDictObject._un_wrap(self)


def _convert_dict_to_xml_recurse(parent, dictitem):
    if isinstance(dictitem, list):
        raise PyXFormError("""Invalid value for `dictitem`.""")

    if isinstance(dictitem, dict):
        for tag, child in iter(dictitem.items()):
            if str(tag) == "_text":
                parent.text = str(child)
            elif isinstance(child, list):
                # iterate through the array and convert
                for listchild in child:
                    elem = Element(tag)
                    parent.append(elem)
                    _convert_dict_to_xml_recurse(elem, listchild)
            else:
                elem = Element(tag)
                parent.append(elem)
                _convert_dict_to_xml_recurse(elem, child)
    else:
        parent.text = str(dictitem)


def convert_dict_to_xml(xmldict):
    """
    Converts a dictionary to an XML ElementTree Element
    """

    roottag = xmldict.keys()[0]
    root = Element(roottag)
    _convert_dict_to_xml_recurse(root, xmldict[roottag])
    return root


def _convert_xml_to_dict_recurse(node, dictclass):
    nodedict = dictclass()

    if len(node.items()) > 0:
        # if we have attributes, set them
        nodedict.update(dict(node.items()))

    for child in node:
        # recursively add the element's children
        newitem = _convert_xml_to_dict_recurse(child, dictclass)
        # if tag in between text node, capture the tail end
        if child.tail is not None and child.tail.strip() != "":
            newitem["tail"] = child.tail
        if child.tag in nodedict:
            # found duplicate tag, force a list
            if isinstance(nodedict[child.tag], list):
                # append to existing list
                nodedict[child.tag].append(newitem)
            else:
                # convert to list
                nodedict[child.tag] = [nodedict[child.tag], newitem]
        else:
            # only one, directly set the dictionary
            nodedict[child.tag] = newitem

    if node.text is None:
        text = ""
    else:
        text = node.text.strip()

    if len(nodedict) > 0:
        # if we have a dictionary
        # add the text as a dictionary value (if there is any)
        if len(text) > 0:
            nodedict["_text"] = text
    else:
        # if we don't have child nodes or attributes, just set the text
        nodedict = text

    return nodedict


def convert_xml_to_dict(root, dictclass=XmlDictObject):
    """
    Converts an XML file or ElementTree Element to a dictionary
    """
    # If a string is passed in, try to open it as a file
    if isinstance(root, str):
        root = _try_parse(root)
    elif not isinstance(root, Element):
        raise TypeError("Expected ElementTree.Element or file path string")

    return dictclass({root.tag: _convert_xml_to_dict_recurse(root, dictclass)})


# end of http://code.activestate.com/recipes/573463/ }}}


def _try_parse(root, parser=None):
    """
    Try to parse the root from a string or a file/file-like object.
    """
    root = root.encode("UTF-8")
    try:
        parsed_root = fromstring(root, parser)
    except ParseError:
        parsed_root = parse(root, parser=parser).getroot()
    return parsed_root


class XFormToDict:
    def __init__(self, root):
        if isinstance(root, str):
            parser = XMLParser(encoding="UTF-8")
            self._root = _try_parse(root, parser)
            self._dict = XmlDictObject(
                {self._root.tag: _convert_xml_to_dict_recurse(self._root, XmlDictObject)}
            )
        elif not isinstance(root, Element):
            raise TypeError("Expected ElementTree.Element or file path string")

    def get_dict(self):
        json_str = json.dumps(self._dict)
        for uri in NSMAP.values():
            json_str = json_str.replace(f"{{{uri}}}", "")
        return json.loads(json_str)


def create_survey_element_from_xml(xml_file):
    sb = XFormToDictBuilder(xml_file)
    return sb.survey()


class XFormToDictBuilder:
    """Experimental XFORM xml to XFORM JSON"""

    def __init__(self, xml_file):
        doc_as_dict = XFormToDict(xml_file).get_dict()
        self._xmldict = doc_as_dict

        if "html" not in doc_as_dict:
            raise PyXFormError("""Invalid value for `doc_as_dict`.""")
        if "body" not in doc_as_dict["html"]:
            raise PyXFormError("""Invalid value for `doc_as_dict`.""")
        if "head" not in doc_as_dict["html"]:
            raise PyXFormError("""Invalid value for `doc_as_dict`.""")
        if "model" not in doc_as_dict["html"]["head"]:
            raise PyXFormError("""Invalid value for `doc_as_dict`.""")
        if "title" not in doc_as_dict["html"]["head"]:
            raise PyXFormError("""Invalid value for `doc_as_dict`.""")
        if "bind" not in doc_as_dict["html"]["head"]["model"]:
            raise PyXFormError("""Invalid value for `doc_as_dict`.""")

        self.body = doc_as_dict["html"]["body"]
        self.model = doc_as_dict["html"]["head"]["model"]
        self.bindings = copy.deepcopy(self.model["bind"])
        self._bind_list = copy.deepcopy(self.model["bind"])
        self.title = doc_as_dict["html"]["head"]["title"]
        secondary = []
        if isinstance(self.model["instance"], list):
            secondary = self.model["instance"][1:]
        self.secondary_instances = secondary
        self.translations = self._get_translations()
        self.choices = self._get_choices()
        self.new_doc = {
            "type": "survey",
            "title": self.title,
            "children": [],
            "id_string": self.title,
            "sms_keyword": self.title,
            "default_language": "default",
            "choices": self.choices,
        }
        self._set_submission_info()
        self._set_survey_name()
        self.children = []
        self.ordered_binding_refs = []
        self._set_binding_order()

        for key, obj in iter(self.body.items()):
            if isinstance(obj, dict):
                self.children.append(self._get_question_from_object(obj, type=key))
            elif isinstance(obj, list):
                for item in obj:
                    self.children.append(self._get_question_from_object(item, type=key))
        self._cleanup_bind_list()
        self._cleanup_children()
        self.new_doc["children"] = self.children

    def _set_binding_order(self):
        self.ordered_binding_refs = []
        for bind in self.bindings:
            self.ordered_binding_refs.append(bind["nodeset"])

    def _set_survey_name(self):
        name = self.bindings[0]["nodeset"].split("/")[1]
        self.new_doc["name"] = name
        instances = self.model["instance"]
        if isinstance(instances, Mapping):
            id_string = instances[name]["id"]
        elif isinstance(instances, list):
            id_string = instances[0][name]["id"]
        else:
            raise PyXFormError(f"Unexpected type for model instances: {type(instances)}")
        self.new_doc["id_string"] = id_string

    def _set_submission_info(self):
        if "submission" in self.model:
            submission = self.model["submission"]
            if "action" in submission:
                self.new_doc["submission_url"] = submission["action"]
            if "base64RsaPublicKey" in submission:
                self.new_doc["public_key"] = submission["base64RsaPublicKey"]
            if "auto-send" in submission:
                self.new_doc["auto_send"] = submission["auto-send"]
            if "auto-delete" in submission:
                self.new_doc["auto_delete"] = submission["auto-delete"]

    def _cleanup_children(self):
        def remove_refs(children):
            for child in children:
                if isinstance(child, dict):
                    if "nodeset" in child:
                        del child["nodeset"]
                    if "ref" in child:
                        del child["ref"]
                    if "__order" in child:
                        del child["__order"]
                    if "children" in child:
                        remove_refs(child["children"])

        # do some ordering, order is specified by bindings
        def order_children(children):
            if isinstance(children, list):
                try:
                    children.sort(key=itemgetter("__order"))
                except KeyError:
                    pass
                for child in children:
                    if isinstance(child, dict) and "children" in child:
                        order_children(child["children"])

        order_children(self.children)
        remove_refs(self.children)

    def _cleanup_bind_list(self):
        for item in self._bind_list:
            ref = item["nodeset"]
            name = self._get_name_from_ref(ref)
            parent_ref = ref[: ref.find(f"/{name}")]
            question = self._get_question_params_from_bindings(ref)
            question["name"] = name
            question["__order"] = self._get_question_order(ref)
            if "calculate" in item:
                question["type"] = "calculate"
            if ref.split("/").__len__() == 3:
                # just append on root node, has no group
                question["ref"] = ref
                self.children.append(question)
                continue
            for child in self.children:
                if child["ref"] == parent_ref:
                    question["ref"] = ref
                    updated = False
                    for c in child["children"]:
                        if isinstance(c, dict) and "ref" in c and c["ref"] == ref:
                            c.update(question)
                            updated = True
                    if not updated:
                        child["children"].append(question)
            if "ref" not in question:
                new_ref = "/".join(ref.split("/")[2:])
                root_ref = "/".join(ref.split("/")[:2])
                q = self._get_item_func(root_ref, new_ref, item)
                if "type" not in q and "type" in question:
                    q.update(question)
                if q["type"] == "group" and q["name"] == "meta":
                    q["control"] = {"bodyless": True}
                    q["__order"] = self._get_question_order(ref)
                self.children.append(q)
                self._bind_list.append(item)
                break
        if self._bind_list:
            self._cleanup_bind_list()

    def _get_item_func(self, ref, name, item):
        rs = {}
        name_splits = name.split("/")
        rs["name"] = name_splits[0]
        ref = f"""{ref}/{rs["name"]}"""
        rs["ref"] = ref
        if name_splits.__len__() > 1:
            rs["type"] = "group"
            rs["children"] = [self._get_item_func(ref, "/".join(name_splits[1:]), item)]
        return rs

    def survey(self):
        new_doc = json.dumps(self.new_doc)
        _survey = builder.create_survey_element_from_json(new_doc)
        return _survey

    def _get_question_order(self, ref):
        try:
            return self.ordered_binding_refs.index(ref)
        except ValueError:
            # likely a group
            for i in self.ordered_binding_refs:
                if i.startswith(ref):
                    return self.ordered_binding_refs.index(i) + 1
            return self.ordered_binding_refs.__len__() + 1

    def _get_question_from_object(self, obj, type=None):
        try:
            ref = obj["ref"]
        except KeyError:
            try:
                ref = obj["nodeset"]
            except KeyError as node_err:
                raise PyXFormError(
                    f'Cannot find "ref" or "nodeset" in {obj!r}'
                ) from node_err
        question = {
            "ref": ref,
            "__order": self._get_question_order(ref),
            "name": self._get_name_from_ref(ref),
        }
        if "hint" in obj:
            k, v = self._get_label(obj["hint"], "hint")
            question[k] = v
        if "label" in obj:
            k, v = self._get_label(obj["label"])
            if isinstance(v, dict) and "label" in v.keys() and "media" in v.keys():
                question.update(v)
            else:
                question[k] = v
        if "autoplay" in obj or "appearance" in obj or "count" in obj or "rows" in obj:
            question["control"] = {}
        if "appearance" in obj:
            question["control"].update({"appearance": obj["appearance"]})
        if "rows" in obj:
            question["control"].update({"rows": obj["rows"]})
        if "autoplay" in obj:
            question["control"].update({"autoplay": obj["autoplay"]})
        question_params = self._get_question_params_from_bindings(ref)

        if isinstance(question_params, dict):
            question.update(question_params)

        # Some values set from bindings are incorrect or incomplete. Correct them now.
        if "mediatype" in obj:
            question["type"] = obj["mediatype"].replace("/*", "")
        if "item" in obj:
            children = []
            for i in obj["item"]:
                if isinstance(i, dict) and "label" in i.keys() and "value" in i.keys():
                    k, v = self._get_label(i["label"])
                    children.append({"name": i["value"], k: v})
            question["children"] = children
        question_type = question["type"] if "type" in question else type
        if (
            question_type == "text"
            and "bind" in question
            and "readonly" in question["bind"]
        ):
            question_type = question["type"] = "note"
            del question["bind"]["readonly"]
            if len(question["bind"].keys()) == 0:
                del question["bind"]
        if question_type in ["group", "repeat"]:
            if question_type == "group" and "repeat" in obj:
                question["children"] = self._get_children_questions(obj["repeat"])
                question_type = "repeat"
                if "count" in obj["repeat"]:
                    if "control" not in question:
                        question["control"] = {}
                    question["control"].update(
                        {
                            "jr:count": self._shorten_xpaths_in_string(
                                obj["repeat"]["count"].strip()
                            )
                        }
                    )
            else:
                question["children"] = self._get_children_questions(obj)
            question["type"] = question_type
        if type == "trigger":
            question["type"] = "acknowledge"
        if type in [
            "select1",
            "select",
        ]:  # Select bind type is 'string' https://github.com/XLSForm/pyxform/issues/168
            question["type"] = QUESTION_TYPES[type]
        if question_type == "geopoint" and "hint" in question:
            del question["hint"]
        if "type" not in question and type:
            question["type"] = question_type
        if "itemset" in obj:
            # Secondary instances
            nodeset = obj["itemset"]["nodeset"]
            choices_name = re.findall(r"^instance\('(.*?)'\)", nodeset)[0]
            question["itemset"] = choices_name
            question["list_name"] = choices_name
            question["choices"] = self.choices[choices_name]
            # Choice filters - attempt parsing XPath like "/node/name[./something =cf]"
            filter_ref = re.findall(rf"\[ /{self.new_doc['name']}/(.*?) ", nodeset)
            filter_exp = re.findall(rf"{filter_ref} (.*?)]$", nodeset)
            if 1 == len(filter_ref) and 1 == len(filter_exp):
                question["choice_filter"] = f"${{{filter_ref[0]}}}{filter_exp[0]}"
                question["query"] = choices_name
        return question

    def _get_children_questions(self, obj):
        children = []
        for k, v in iter(obj.items()):
            if k in ["ref", "label", "nodeset"]:
                continue
            if isinstance(v, dict):
                child = self._get_question_from_object(v, type=k)
                children.append(child)
            elif isinstance(v, list):
                for i in v:
                    child = self._get_question_from_object(i, type=k)
                    children.append(child)
        return children

    def _get_question_params_from_bindings(self, ref):
        for item in self.bindings:
            if item["nodeset"] == ref:
                try:
                    self._bind_list.remove(item)
                except ValueError:
                    pass
                rs = {}
                for k, v in iter(item.items()):
                    if k == "nodeset":
                        continue
                    if k == "type":
                        v = self._get_question_type(question_type=v)
                    if k in [
                        "relevant",
                        "required",
                        "constraint",
                        "constraintMsg",
                        "readonly",
                        "calculate",
                        "noAppErrorString",
                        "requiredMsg",
                    ]:
                        if k == "noAppErrorString":
                            k = "jr:noAppErrorString"
                        if k == "requiredMsg":
                            k = "jr:requiredMsg"
                        if k == "constraintMsg":
                            k = "jr:constraintMsg"
                            v = self._get_constraint_msg(v)
                        if k == "required":
                            if v == "true()":
                                v = "yes"
                            elif v == "false()":
                                v = "no"
                        if k in ["constraint", "relevant", "calculate"]:
                            v = self._shorten_xpaths_in_string(v)
                        if "bind" not in rs:
                            rs["bind"] = {}
                        rs["bind"][k] = v
                        continue
                    if k == "preload" and v == "uid":
                        if "bind" not in rs:
                            rs["bind"] = {}
                        rs["bind"]["jr:preload"] = v
                    rs[k] = v
                if "preloadParams" in rs and "preload" in rs:
                    rs["type"] = rs["preloadParams"]
                    del rs["preloadParams"]
                    del rs["preload"]
                return rs
        return None

    @staticmethod
    def _get_question_type(question_type):
        if question_type in QUESTION_TYPES.keys():
            return QUESTION_TYPES[question_type]
        return question_type

    def _get_translations(self) -> list[dict]:
        if "itext" not in self.model:
            return []
        if "translation" not in self.model["itext"]:
            raise PyXFormError("""Invalid value for `self.model["itext"]`.""")
        translations = self.model["itext"]["translation"]
        if isinstance(translations, dict):
            translations = [translations]
        if "text" not in translations[0]:
            raise PyXFormError("""Invalid value for `translations[0]`.""")
        if "lang" not in translations[0]:
            raise PyXFormError("""Invalid value for `translations[0]`.""")
        return translations

    def _get_label(self, label_obj, key="label"):
        if isinstance(label_obj, dict):
            try:
                ref = label_obj["ref"].replace("jr:itext('", "").replace("')", "")
            except KeyError:
                return key, self._get_output_text(label_obj)
            else:
                return self._get_text_from_translation(ref, key)
        return key, label_obj

    def _get_output_text(self, value):
        if "output" in value and "_text" in value:
            v = [value["_text"], self._get_bracketed_name(value["output"]["value"])]
            text = " ".join(v)
            if "tail" in value["output"]:
                text = "".join([text, value["output"]["tail"]])
        elif "output" in value and "_text" not in value:
            text = self._get_bracketed_name(value["output"]["value"])
        else:
            return value
        return text

    def _get_text_from_translation(self, ref, key="label"):
        label = {}
        for translation in self.translations:
            lang = translation["lang"]
            label_list = translation["text"]
            for lbl in label_list:
                if "value" not in lbl or lbl["value"] == "-":  # skip blank label
                    continue
                if lbl["id"] == ref:
                    text = value = lbl["value"]
                    if isinstance(value, dict):
                        if "output" in value:
                            text = self._get_output_text(value)
                        if "form" in value and "_text" in value:
                            key = "media"
                            v = value["_text"]
                            if value["form"] == "image":
                                v = v.replace("jr://images/", "")
                            else:
                                v = v.replace(f"jr://{value['form']}/", "")
                            if v == "-":  # skip blank
                                continue
                            text = {value["form"]: v}
                    if isinstance(value, list):
                        for item in value:
                            if "form" in item and "_text" in item:
                                k = "media"
                                m_type = item["form"]
                                v = item["_text"]
                                if m_type == "image":
                                    v = v.replace("jr://images/", "")
                                else:
                                    v = v.replace(f"jr://{m_type}/", "")
                                if v == "-":
                                    continue
                                if k not in label:
                                    label[k] = {}
                                if m_type not in label[k]:
                                    label[k][m_type] = {}
                                label[k][m_type][lang] = v
                                continue
                            if isinstance(item, str):
                                if item == "-":
                                    continue
                            if "label" not in label:
                                label["label"] = {}
                            label["label"][lang] = item
                        continue

                    label[lang] = text
                    break
        if key == "media" and list(label.keys()) == ["default"]:
            label = label["default"]
        return key, label

    def _get_bracketed_name(self, ref):
        name = self._get_name_from_ref(ref)
        return "".join(["${", name.strip(), "}"])

    def _get_constraint_msg(self, constraint_msg):
        if isinstance(constraint_msg, str):
            if constraint_msg.find(":jr:constraintMsg") != -1:
                ref = constraint_msg.replace("jr:itext('", "").replace("')", "")
                k, constraint_msg = self._get_text_from_translation(ref)
        return constraint_msg

    def _get_choices(self) -> dict[str, Any]:
        """
        Get all form choices, using the model/instance and model/itext.
        """
        choices = {}
        for instance in self.secondary_instances:
            items = []
            for choice in instance["root"]["item"]:
                item = copy.deepcopy(choice)
                if "itextId" in choice:
                    key, label = self._get_text_from_translation(
                        ref=item.pop("itextId"), key="label"
                    )
                    item[key] = label
                items.append(item)
            choices[instance["id"]] = items
        return choices

    @staticmethod
    def _get_name_from_ref(ref):
        """given /xlsform_spec_test/launch,
        return the string after the last occurance of the character '/'
        """
        pos = ref.rfind("/")
        if pos == -1:
            return ref
        else:
            return ref[pos + 1 :].strip()

    @staticmethod
    def _expand_child(obj_list):
        return obj_list

    @staticmethod
    def _shorten_xpaths_in_string(text):
        def get_last_item(xpath_str):
            last_item = xpath_str.split("/")
            return last_item[len(last_item) - 1].strip()

        def replace_function(match):
            return f"${{{get_last_item(match.group())}}}"

        # moving re flags into compile for python 2.6 compat
        pattern = "( /[a-z0-9-_]+(?:/[a-z0-9-_]+)+ )"
        text = re.compile(pattern, flags=re.I).sub(replace_function, text)
        pattern = "(/[a-z0-9-_]+(?:/[a-z0-9-_]+)+)"
        text = re.compile(pattern, flags=re.I).sub(replace_function, text)
        return text


def write_object_to_file(filename, obj):
    """Writes to a JSON filename the dictionary obj."""
    with open(filename, "w", encoding="utf-8") as output_file:
        output_file.write(json.dumps(obj, indent=2))
    logger.info("object written to file: %s", filename)

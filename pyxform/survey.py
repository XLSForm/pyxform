"""
Survey module with XForm Survey objects and utility functions.
"""

import os
import re
import tempfile
import xml.etree.ElementTree as ETree
from collections import defaultdict
from collections.abc import Generator, Iterator
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from pyxform import aliases, constants
from pyxform.constants import EXTERNAL_INSTANCE_EXTENSIONS, NSMAP
from pyxform.errors import PyXFormError, ValidationError
from pyxform.external_instance import ExternalInstance
from pyxform.instance import SurveyInstance
from pyxform.parsing import instance_expression
from pyxform.question import Option, Question
from pyxform.section import Section
from pyxform.survey_element import SurveyElement
from pyxform.utils import (
    BRACKETED_TAG_REGEX,
    LAST_SAVED_INSTANCE_NAME,
    LAST_SAVED_REGEX,
    DetachableElement,
    PatchedText,
    get_languages_with_bad_tags,
    has_dynamic_label,
    node,
)
from pyxform.validators import enketo_validate, odk_validate

RE_BRACKET = re.compile(r"\[([^]]+)\]")
RE_FUNCTION_ARGS = re.compile(r"\b[^()]+\((.*)\)$")
RE_INDEXED_REPEAT = re.compile(r"indexed-repeat\([^)]+\)")
RE_INSTANCE = re.compile(r"instance\([^)]+.+")
RE_INSTANCE_SECONDARY_REF = re.compile(
    r"(instance\(.*\)\/root\/item\[.*?(\$\{.*\})\]\/.*?)\s"
)
RE_PULLDATA = re.compile(r"(pulldata\s*\(\s*)(.*?),")
SEARCH_FUNCTION_REGEX = re.compile(r"search\(.*?\)")


class InstanceInfo:
    """Standardise Instance details relevant during XML generation."""

    __slots__ = ("type", "context", "name", "src", "instance")

    def __init__(
        self,
        type: str,
        context: str | None,
        name: str,
        src: str | None,
        instance: "DetachableElement",
    ):
        self.type: str = type
        self.context: str | None = context
        self.name: str = name
        self.src: str | None = src
        self.instance: DetachableElement = instance


def register_nsmap():
    """Function to register NSMAP namespaces with ETree"""
    for prefix, uri in NSMAP.items():
        prefix_no_xmlns = prefix.replace("xmlns", "").replace(":", "")
        ETree.register_namespace(prefix_no_xmlns, uri)


register_nsmap()


@lru_cache(maxsize=65536)  # 2^16
def is_parent_a_repeat(survey, xpath):
    """
    Returns the XPATH of the first repeat of the given xpath in the survey,
    otherwise False will be returned.
    """
    parent_xpath = "/".join(xpath.split("/")[:-1])
    if not parent_xpath:
        return False

    if survey.any_repeat(parent_xpath):
        return parent_xpath

    return is_parent_a_repeat(survey, parent_xpath)


@lru_cache(maxsize=65536)  # 2^16
def share_same_repeat_parent(survey, xpath, context_xpath, reference_parent=False):
    """
    Returns a tuple of the number of steps from the context xpath to the shared
    repeat parent and the xpath to the target xpath from the shared repeat
    parent.

    For example,
        xpath = /data/repeat_a/group_a/name
        context_xpath = /data/repeat_a/group_b/age

        returns (2, '/group_a/name')'
    """

    def _get_steps_and_target_xpath(context_parent, xpath_parent, include_parent=False):
        parts = []
        steps = 1
        if not include_parent:
            remainder_xpath = xpath[len(xpath_parent) :]
            context_parts = context_xpath[len(xpath_parent) + 1 :].split("/")
            xpath_parts = xpath[len(xpath_parent) + 1 :].split("/")
        else:
            split_idx = len(xpath_parent.split("/"))
            context_parts = context_xpath.split("/")[split_idx - 1 :]
            xpath_parts = xpath.split("/")[split_idx - 1 :]
            remainder_xpath = "/".join(xpath_parts)

        for index, item in enumerate(context_parts[:-1]):
            try:
                if xpath[len(context_parent) + 1 :].split("/")[index] != item:
                    steps = len(context_parts[index:])
                    parts = xpath_parts[index:]
                    break
                else:
                    parts = remainder_xpath.split("/")[index + 2 :]
            except IndexError:
                steps = len(context_parts[index - 1 :])
                parts = xpath_parts[index - 1 :]
                break
        return (steps, "/" + "/".join(parts) if parts else remainder_xpath)

    context_parent = is_parent_a_repeat(survey, context_xpath)
    xpath_parent = is_parent_a_repeat(survey, xpath)
    if context_parent and xpath_parent and xpath_parent in context_parent:
        if (not context_parent == xpath_parent and reference_parent) or bool(
            is_parent_a_repeat(survey, context_parent)
        ):
            context_shared_ancestor = is_parent_a_repeat(survey, context_parent)
            if context_shared_ancestor == xpath_parent:
                # Check if context_parent is a child repeat of the xpath_parent
                # If the context_parent is a child of the xpath_parent reference the entire
                # xpath_parent in the generated nodeset
                context_parent = context_shared_ancestor
            elif context_parent == xpath_parent and context_shared_ancestor:
                # If the context_parent is a child of another
                # repeat and is equal to the xpath_parent
                # we avoid refrencing the context_parent and instead reference the shared
                # ancestor
                reference_parent = False
        return _get_steps_and_target_xpath(context_parent, xpath_parent, reference_parent)
    elif context_parent and xpath_parent:
        # Check if context_parent and xpath_parent share a common
        # repeat ancestor
        context_shared_ancestor = is_parent_a_repeat(survey, context_parent)
        xpath_shared_ancestor = is_parent_a_repeat(survey, xpath_parent)

        if (
            xpath_shared_ancestor
            and context_shared_ancestor
            and xpath_shared_ancestor == context_shared_ancestor
        ):
            return _get_steps_and_target_xpath(
                context_shared_ancestor, xpath_shared_ancestor
            )

    return (None, None)


@lru_cache(maxsize=65536)  # 2^16
def is_label_dynamic(label: str) -> bool:
    return (
        label is not None
        and isinstance(label, str)
        and re.search(BRACKETED_TAG_REGEX, label) is not None
    )


def recursive_dict():
    return defaultdict(recursive_dict)


class Survey(Section):
    """
    Survey class - represents the full XForm XML.
    """

    FIELDS = Section.FIELDS.copy()
    FIELDS.update(
        {
            "_xpath": dict,
            "_created": datetime.now,  # This can't be dumped to json
            "setvalues_by_triggering_ref": dict,
            "title": str,
            "id_string": str,
            "sms_keyword": str,
            "sms_separator": str,
            "sms_allow_media": bool,
            "sms_date_format": str,
            "sms_datetime_format": str,
            "sms_response": str,
            constants.COMPACT_PREFIX: str,
            constants.COMPACT_DELIMITER: str,
            "file_name": str,
            "default_language": str,
            "_translations": recursive_dict,
            "submission_url": str,
            "auto_send": str,
            "auto_delete": str,
            "public_key": str,
            "instance_xmlns": str,
            "version": str,
            "choices": dict,
            "style": str,
            "attribute": dict,
            "namespaces": str,
            constants.ENTITY_FEATURES: list,
        }
    )

    def validate(self):
        if self.id_string in [None, "None"]:
            raise PyXFormError("Survey cannot have an empty id_string")
        super().validate()
        self._validate_uniqueness_of_section_names()

    def _validate_uniqueness_of_section_names(self):
        root_node_name = self.name
        section_names = []
        for element in self.iter_descendants():
            if isinstance(element, Section):
                if element.name in section_names:
                    if element.name == root_node_name:
                        # The root node name is rarely explictly set; explain
                        # the problem in a more helpful way (#510)
                        msg = (
                            f"The name '{element.name}' is the same as the form name. "
                            "Use a different section name (or change the form name in "
                            "the 'name' column of the settings sheet)."
                        )
                        raise PyXFormError(msg)
                    msg = f"There are two sections with the name {element.name}."
                    raise PyXFormError(msg)
                section_names.append(element.name)

    def get_nsmap(self):
        """Add additional namespaces"""
        namespaces = getattr(self, constants.NAMESPACES, "")
        if len(getattr(self, constants.ENTITY_FEATURES, [])) > 0:
            namespaces += " entities=http://www.opendatakit.org/xforms/entities"

        if namespaces and isinstance(namespaces, str):
            nslist = [
                ns.split("=")
                for ns in namespaces.split()
                if len(ns.split("=")) == 2 and ns.split("=")[0] != ""
            ]
            xmlns = "xmlns:"
            nsmap = NSMAP.copy()
            nsmap.update(
                {
                    xmlns + k: v.replace('"', "").replace("'", "")
                    for k, v in nslist
                    if xmlns + k not in nsmap
                }
            )
            return nsmap

        return NSMAP

    def xml(self):
        """
        calls necessary preparation methods, then returns the xml.
        """
        self.validate()
        self._setup_xpath_dictionary()

        for triggering_reference in self.setvalues_by_triggering_ref.keys():
            if not re.search(BRACKETED_TAG_REGEX, triggering_reference):
                raise PyXFormError(
                    "Only references to other fields are allowed in the 'trigger' column."
                )

            # try to resolve reference and fail if can't
            self.insert_xpaths(triggering_reference, self)

        body_kwargs = {}
        if hasattr(self, constants.STYLE) and getattr(self, constants.STYLE):
            body_kwargs["class"] = getattr(self, constants.STYLE)
        nsmap = self.get_nsmap()

        return node(
            "h:html",
            node("h:head", node("h:title", self.title), self.xml_model()),
            node("h:body", *self.xml_control(), **body_kwargs),
            **nsmap,
        )

    def get_setvalues_for_question_name(self, question_name):
        return self.setvalues_by_triggering_ref.get(f"${{{question_name}}}")

    def _generate_static_instances(self, list_name, choice_list) -> InstanceInfo:
        """
        Generate <instance> elements for static data (e.g. choices for selects)
        """
        instance_element_list = []
        has_media = bool(choice_list[0].get("media"))
        has_dyn_label = has_dynamic_label(choice_list)
        multi_language = False
        if isinstance(self._translations, dict):
            choices = tuple(
                k
                for items in self._translations.values()
                for k, v in items.items()
                if v.get(constants.TYPE, "") == constants.CHOICE
                and "-".join(k.split("-")[:-1]) == list_name
            )
            if 0 < len(choices):
                multi_language = True

        for idx, choice in enumerate(choice_list):
            choice_element_list = []
            # Add a unique id to the choice element in case there are itext references
            if multi_language or has_media or has_dyn_label:
                itext_id = "-".join([list_name, str(idx)])
                choice_element_list.append(node("itextId", itext_id))

            for name, value in choice.items():
                if isinstance(value, str) and name != "label":
                    choice_element_list.append(node(name, str(value)))
                if (
                    not multi_language
                    and not has_media
                    and not has_dyn_label
                    and isinstance(value, str)
                    and name == "label"
                ):
                    choice_element_list.append(node(name, str(value)))

            instance_element_list.append(node("item", *choice_element_list))

        return InstanceInfo(
            type="choice",
            context="survey",
            name=list_name,
            src=None,
            instance=node("instance", node("root", *instance_element_list), id=list_name),
        )

    @staticmethod
    def _generate_external_instances(element) -> InstanceInfo | None:
        if isinstance(element, ExternalInstance):
            name = element["name"]
            extension = element["type"].split("-")[0]
            prefix = "file-csv" if extension == "csv" else "file"
            src = f"jr://{prefix}/{name}.{extension}"
            return InstanceInfo(
                type="external",
                context="[type: {t}, name: {n}]".format(
                    t=element["parent"]["type"], n=element["parent"]["name"]
                ),
                name=name,
                src=src,
                instance=node("instance", id=name, src=src),
            )

        return None

    @staticmethod
    def _validate_external_instances(instances) -> None:
        """
        Must have unique names.

        - Duplications could come from across groups; this checks the form.
        - Errors are pooled together into a (hopefully) helpful message.
        """
        seen = {}
        for i in instances:
            element = i.name
            if seen.get(element) is None:
                seen[element] = [i]
            else:
                seen[element].append(i)
        errors = []
        for element, copies in seen.items():
            if len(copies) > 1:
                contexts = ", ".join(f"{x.context}({x.type})" for x in copies)
                errors.append(
                    "Instance names must be unique within a form. "
                    f"The name '{element}' was found {len(copies)} time(s), "
                    f"under these contexts: {contexts}"
                )
        if errors:
            raise ValidationError("\n".join(errors))

    @staticmethod
    def _generate_pulldata_instances(element) -> list[InstanceInfo] | None:
        def get_pulldata_functions(element):
            """
            Returns a list of different pulldata(... function strings if
            pulldata function is defined at least once for any of:
            calculate, constraint, readonly, required, relevant

            :param: element (pyxform.survey.Survey):
            """
            functions_present = []
            for formula_name in constants.EXTERNAL_INSTANCES:
                if "pulldata(" in str(element["bind"].get(formula_name)):
                    functions_present.append(element["bind"][formula_name])
            if "pulldata(" in str(element["choice_filter"]):
                functions_present.append(element["choice_filter"])
            if "pulldata(" in str(element["default"]):
                functions_present.append(element["default"])

            return functions_present

        def get_instance_info(element, file_id):
            uri = f"jr://file-csv/{file_id}.csv"

            return InstanceInfo(
                type="pulldata",
                context="[type: {t}, name: {n}]".format(
                    t=element["parent"]["type"], n=element["parent"]["name"]
                ),
                name=file_id,
                src=uri,
                instance=node("instance", id=file_id, src=uri),
            )

        pulldata_usages = get_pulldata_functions(element)
        if len(pulldata_usages) > 0:
            pulldata_instances = []
            for usage in pulldata_usages:
                for call_match in re.finditer(RE_PULLDATA, usage):
                    groups = call_match.groups()
                    if len(groups) == 2:
                        first_argument = (  # first argument to pulldata()
                            groups[1].replace("'", "").replace('"', "").strip()
                        )
                        pulldata_instances.append(
                            get_instance_info(element, first_argument)
                        )
            return pulldata_instances
        return None

    @staticmethod
    def _generate_from_file_instances(element) -> InstanceInfo | None:
        itemset = element.get("itemset")
        file_id, ext = os.path.splitext(itemset)
        if itemset and ext in EXTERNAL_INSTANCE_EXTENSIONS:
            file_ext = "file" if ext in {".xml", ".geojson"} else f"file-{ext[1:]}"
            uri = f"jr://{file_ext}/{itemset}"
            return InstanceInfo(
                type="file",
                context="[type: {t}, name: {n}]".format(
                    t=element["parent"]["type"], n=element["parent"]["name"]
                ),
                name=file_id,
                src=uri,
                instance=node("instance", id=file_id, src=uri),
            )

        return None

    @staticmethod
    def _generate_last_saved_instance(element) -> bool:
        """
        True if a last-saved instance should be generated, false otherwise.
        """
        for expression_type in constants.EXTERNAL_INSTANCES:
            last_saved_expression = re.search(
                LAST_SAVED_REGEX, str(element["bind"].get(expression_type))
            )
            if last_saved_expression:
                return True

        return bool(
            re.search(LAST_SAVED_REGEX, str(element["choice_filter"]))
            or re.search(LAST_SAVED_REGEX, str(element["default"]))
        )

    @staticmethod
    def _get_last_saved_instance() -> InstanceInfo:
        name = "__last-saved"  # double underscore used to minimize risk of name conflicts
        uri = "jr://instance/last-saved"

        return InstanceInfo(
            type="instance",
            context=None,
            name=name,
            src=uri,
            instance=node("instance", id=name, src=uri),
        )

    def _generate_instances(self) -> Iterator[DetachableElement]:
        """
        Get instances from all the different ways that they may be generated.

        An opportunity to validate instances before output to the XML model.

        Instance names used for the id attribute are generated as follows:

        - xml-external: item name value (for type==xml-external)
        - pulldata: first arg to calculation->pulldata()
        - select from file: file name arg to type->itemset
        - choices: list_name (for type==select_*)
        - last-saved: static name of jr://instance/last-saved

        Validation and business rules for output of instances:

        - xml-external item name must be unique across the XForm and the form
          is considered invalid if there is a duplicate name. This differs from
          other item types which allow duplicates if not in the same group.
        - for all instance sources, if the same instance name is encountered,
          the following rules are used to allow re-using instances but prevent
          overwriting conflicting instances:
          - same id, same src URI: skip adding the second (duplicate) instance
          - same id, different src URI: raise an error
          - otherwise: output the instance

        There are two other things currently supported by pyxform that involve
        external files and are not explicitly handled here, but may be relevant
        to future efforts to harmonise / simplify external data workflows:

        - `search` appearance/function: works a lot like pulldata but the csv
          isn't made explicit in the form.
        - `select_one_external`: implicitly relies on a `itemsets.csv` file and
          uses XPath-like expressions for querying.
        """
        instances = []
        generate_last_saved = False
        for i in self.iter_descendants():
            i_ext = self._generate_external_instances(element=i)
            i_pull = self._generate_pulldata_instances(element=i)
            i_file = self._generate_from_file_instances(element=i)
            if not generate_last_saved:
                generate_last_saved = self._generate_last_saved_instance(element=i)
            for x in [i_ext, i_pull, i_file]:
                if x is not None:
                    instances += x if isinstance(x, list) else [x]

        if generate_last_saved:
            instances += [self._get_last_saved_instance()]

        # Append last so the choice instance is excluded on a name clash.
        for name, value in self.choices.items():
            instances += [
                self._generate_static_instances(list_name=name, choice_list=value)
            ]

        # Check that external instances have unique names.
        if instances:
            ext_only = [x for x in instances if x.type == "external"]
            self._validate_external_instances(instances=ext_only)

        seen = {}
        for i in instances:
            if i.name in seen.keys() and seen[i.name].src != i.src:
                # Instance id exists with different src URI -> error.
                msg = (
                    "The same instance id will be generated for different "
                    "external instance source URIs. Please check the form."
                    f" Instance name: '{i.name}', Existing type: '{seen[i.name].type}', "
                    f"Existing URI: '{seen[i.name].src}', Duplicate type: '{i.type}', "
                    f"Duplicate URI: '{i.src}', Duplicate context: '{i.context}'."
                )
                raise PyXFormError(msg)
            elif i.name in seen.keys() and seen[i.name].src == i.src:
                # Instance id exists with same src URI -> ok, don't duplicate.
                continue
            else:
                # Instance doesn't exist yet -> add it.
                yield i.instance
            seen[i.name] = i

    def xml_model(self):
        """
        Generate the xform <model> element
        """
        self._setup_translations()
        self._setup_media()
        self._add_empty_translations()

        model_kwargs = {"odk:xforms-version": constants.CURRENT_XFORMS_VERSION}

        entity_features = getattr(self, constants.ENTITY_FEATURES, [])
        if len(entity_features) > 0:
            if "offline" in entity_features:
                model_kwargs["entities:entities-version"] = (
                    constants.ENTITIES_OFFLINE_VERSION
                )
            elif "update" in entity_features:
                model_kwargs["entities:entities-version"] = (
                    constants.ENTITIES_UPDATE_VERSION
                )
            else:
                model_kwargs["entities:entities-version"] = (
                    constants.ENTITIES_CREATE_VERSION
                )

        model_children = []
        if self._translations:
            model_children.append(self.itext())
        model_children += [node("instance", self.xml_instance())]
        model_children += list(self._generate_instances())
        model_children += self.xml_descendent_bindings()
        model_children += self.xml_actions()

        if self.submission_url or self.public_key or self.auto_send or self.auto_delete:
            submission_attrs = {}
            if self.submission_url:
                submission_attrs["action"] = self.submission_url
                submission_attrs["method"] = "post"
            if self.public_key:
                submission_attrs["base64RsaPublicKey"] = self.public_key
            if self.auto_send:
                submission_attrs["orx:auto-send"] = self.auto_send
            if self.auto_delete:
                submission_attrs["orx:auto-delete"] = self.auto_delete
            submission_node = node("submission", **submission_attrs)
            model_children.insert(0, submission_node)

        return node("model", *model_children, **model_kwargs)

    def xml_instance(self, **kwargs):
        result = Section.xml_instance(self, **kwargs)

        # set these first to prevent overwriting id and version
        for key, value in self.attribute.items():
            result.setAttribute(str(key), value)

        result.setAttribute("id", self.id_string)

        # add instance xmlns attribute to the instance node
        if self.instance_xmlns:
            result.setAttribute("xmlns", self.instance_xmlns)

        if self.version:
            result.setAttribute("version", self.version)

        if self.prefix:
            result.setAttribute("odk:prefix", self.prefix)

        if self.delimiter:
            result.setAttribute("odk:delimiter", self.delimiter)

        return result

    def _add_to_nested_dict(self, dicty, path, value):
        if len(path) == 1:
            key = path[0]
            if key in dicty and isinstance(dicty[key], dict) and isinstance(value, dict):
                dicty[key].update(value)
            else:
                dicty[key] = value
            return
        if path[0] not in dicty:
            dicty[path[0]] = {}
        self._add_to_nested_dict(dicty[path[0]], path[1:], value)

    def _redirect_is_search_itext(self, element: SurveyElement) -> bool:
        """
        For selects using the "search()" function, redirect itext for in-line items.

        External selects from a "search" function alone don't work in Enketo. In Collect
        they must have the "item" elements in the body, rather than in an "itemset".

        The "itemset" reference is cleared below, so that the element will get in-line
        items instead of an itemset reference to a secondary instance. The itext ref is
        passed to the options/choices so they can use the generated translations. This
        accounts for questions with and without a "search()" function sharing choices.

        :param element: A select type question.
        :return: If True, the element uses the search function.
        """
        try:
            is_search = bool(
                SEARCH_FUNCTION_REGEX.search(
                    element[constants.CONTROL][constants.APPEARANCE]
                )
            )
        except (KeyError, TypeError):
            is_search = False
        if is_search:
            file_id, ext = os.path.splitext(element[constants.ITEMSET])
            if ext in EXTERNAL_INSTANCE_EXTENSIONS:
                msg = (
                    f"Question '{element[constants.NAME]}' is a select from file type, "
                    "using 'search()'. This combination is not supported. "
                    "Remove the 'search()' usage, or change the select type."
                )
                raise PyXFormError(msg)
            itemset = element[constants.ITEMSET]
            self.choices.pop(itemset, None)
            element[constants.ITEMSET] = ""
            for i, opt in enumerate(element.get(constants.CHILDREN, [])):
                opt["_choice_itext_id"] = f"{element[constants.LIST_NAME_U]}-{i}"
        return is_search

    def _setup_translations(self):
        """
        set up the self._translations dict which will be referenced in the
        setup media and itext functions
        """

        def _setup_choice_translations(
            name, choice_value, itext_id
        ) -> Generator[tuple[list[str], str], None, None]:
            for media_or_lang, value in choice_value.items():
                if isinstance(value, dict):
                    for language, val in value.items():
                        yield ([language, itext_id, media_or_lang], val)
                elif name == constants.MEDIA:
                    yield ([self.default_language, itext_id, media_or_lang], value)
                else:
                    yield ([media_or_lang, itext_id, "long"], value)

        itemsets_multi_language = set()
        itemsets_has_media = set()
        itemsets_has_dyn_label = set()

        def get_choices():
            for list_name, choice_list in self.choices.items():
                multi_language = False
                has_media = False
                dyn_label = False
                choices = []
                for idx, choice in enumerate(choice_list):
                    for col_name, choice_value in choice.items():
                        lang_choice = None
                        if col_name == constants.MEDIA:
                            has_media = True
                        if isinstance(choice_value, dict):
                            lang_choice = choice_value
                            multi_language = True
                        elif col_name == constants.LABEL:
                            lang_choice = {self.default_language: choice_value}
                            if is_label_dynamic(choice_value):
                                dyn_label = True
                        if lang_choice is not None:
                            # e.g. (label, {"default": "Yes"}, "consent", 0)
                            choices.append((col_name, lang_choice, list_name, idx))
                if multi_language or has_media or dyn_label:
                    if multi_language:
                        itemsets_multi_language.add(list_name)
                    if has_media:
                        itemsets_has_media.add(list_name)
                    if dyn_label:
                        itemsets_has_dyn_label.add(list_name)
                    for c in choices:
                        yield from _setup_choice_translations(
                            c[0], c[1], f"{c[2]}-{c[3]}"
                        )

        for path, value in get_choices():
            last_path = path.pop()
            leaf_value = {last_path: value, constants.TYPE: constants.CHOICE}
            self._add_to_nested_dict(self._translations, path, leaf_value)

        select_types = set(aliases.select.keys())
        search_lists = set()
        non_search_lists = set()
        for element in self.iter_descendants():
            itemset = element.get("itemset")
            if itemset is not None:
                element._itemset_multi_language = itemset in itemsets_multi_language
                element._itemset_has_media = itemset in itemsets_has_media
                element._itemset_dyn_label = itemset in itemsets_has_dyn_label

            if element[constants.TYPE] in select_types:
                select_ref = (element[constants.NAME], element[constants.LIST_NAME_U])
                if self._redirect_is_search_itext(element=element):
                    search_lists.add(select_ref)
                else:
                    non_search_lists.add(select_ref)

            # Skip creation of translations for choices in selects. The creation of these
            # translations is done above in this function.
            parent = element.get("parent")
            if parent is not None and parent[constants.TYPE] not in select_types:
                for d in element.get_translations(self.default_language):
                    translation_path = d["path"]
                    form = "long"

                    if "guidance_hint" in d["path"]:
                        translation_path = d["path"].replace("guidance_hint", "hint")
                        form = "guidance"

                    self._translations[d["lang"]][translation_path] = self._translations[
                        d["lang"]
                    ].get(translation_path, {})

                    self._translations[d["lang"]][translation_path].update(
                        {
                            form: {
                                "text": d["text"],
                                "output_context": d["output_context"],
                            },
                            constants.TYPE: constants.QUESTION,
                        }
                    )

        for q_name, list_name in search_lists:
            choice_refs = [f"'{q}'" for q, c in non_search_lists if c == list_name]
            if len(choice_refs) > 0:
                refs_str = ", ".join(choice_refs)
                msg = (
                    f"Question '{q_name}' uses 'search()', and its select type references"
                    f" the choice list name '{list_name}'. This choice list name is "
                    f"referenced by at least one other question that is not using "
                    f"'search()', which will not work: {refs_str}. Either 1) use "
                    f"'search()' for all questions using this choice list name, or 2) "
                    f"use a different choice list name for the question using 'search()'."
                )
                raise PyXFormError(msg)

    def _add_empty_translations(self):
        """
        Adds translations so that every itext element has the same elements across every
        language. When translations are not provided "-" will be used.
        This disables any of the default_language fallback functionality.
        """
        paths = {}
        for translation in self._translations.values():
            for path, content in translation.items():
                paths[path] = paths.get(path, set()).union(content.keys())

        for lang in self._translations:
            for path, content_types in paths.items():
                if path not in self._translations[lang]:
                    self._translations[lang][path] = {}
                for content_type in content_types:
                    if content_type not in self._translations[lang][path]:
                        self._translations[lang][path][content_type] = "-"

    def _setup_media(self):
        """
        Traverse the survey, find all the media, and put in into the \
        _translations data structure which looks like this:
        {language : {element_xpath : {media_type : media}}}
        It matches the xform nesting order.
        """

        def _set_up_media_translations(media_dict, translation_key):
            # This is probably papering over a real problem, but anyway,
            # in py3, sometimes if an item is on an xform with multiple
            # languages and the item only has media defined in # "default"
            # (e.g. no "image" vs. "image::lang"), the media dict will be
            # nested inside of a dict with key "default", e.g.
            # {"default": {"image": "my_image.jpg"}}
            media_dict_default = media_dict.get("default", None)
            if isinstance(media_dict_default, dict):
                media_dict = media_dict_default

            for media_type, possibly_localized_media in media_dict.items():
                if media_type not in SurveyElement.SUPPORTED_MEDIA:
                    raise PyXFormError("Media type: " + media_type + " not supported")

                if isinstance(possibly_localized_media, dict):
                    # media is localized
                    localized_media = possibly_localized_media
                else:
                    # media is not localized so create a localized version
                    # using the default language
                    localized_media = {self.default_language: possibly_localized_media}

                for language, media in localized_media.items():
                    # Create the required dictionaries in _translations,
                    # then add media as a leaf value:
                    if language not in self._translations:
                        self._translations[language] = {}

                    translations_language = self._translations[language]

                    if translation_key not in translations_language:
                        translations_language[translation_key] = {}

                    translations_trans_key = translations_language[translation_key]

                    if media_type not in translations_trans_key:
                        translations_trans_key[media_type] = {}

                    translations_trans_key[media_type] = media

        for survey_element in self.iter_descendants():
            # Skip set up of media for choices in selects. Translations for their media
            # content should have been set up in _setup_translations, with one copy of
            # each choice translation per language (after _add_empty_translations).
            if not isinstance(survey_element, Option):
                media_dict = survey_element.get("media")
                if isinstance(media_dict, dict) and 0 < len(media_dict):
                    translation_key = survey_element.get_xpath() + ":label"
                    _set_up_media_translations(media_dict, translation_key)

    def itext(self):
        """
        This function creates the survey's itext nodes from _translations
        @see _setup_media _setup_translations
        itext nodes are localized images/audio/video/text
        @see http://code.google.com/p/opendatakit/wiki/XFormDesignGuidelines
        """
        result = []
        for lang, translation in self._translations.items():
            if lang == self.default_language:
                result.append(node("translation", lang=lang, default="true()"))
            else:
                result.append(node("translation", lang=lang))

            for label_name, content in translation.items():
                itext_nodes = []
                label_type = label_name.partition(":")[-1]

                if not isinstance(content, dict):
                    raise PyXFormError("""Invalid value for `content`.""")

                for media_type, media_value in content.items():
                    # Ignore key indicating Question or Choice translation type.
                    if media_type == constants.TYPE:
                        continue
                    if isinstance(media_value, dict):
                        value, output_inserted = self.insert_output_values(
                            media_value["text"], context=media_value["output_context"]
                        )
                    else:
                        value, output_inserted = self.insert_output_values(media_value)

                    if label_type == "hint":
                        if media_type == "guidance":
                            itext_nodes.append(
                                node(
                                    "value",
                                    value,
                                    form="guidance",
                                    toParseString=output_inserted,
                                )
                            )
                        else:
                            itext_nodes.append(
                                node("value", value, toParseString=output_inserted)
                            )
                        continue

                    if media_type == "long":
                        # I'm ignoring long types for now because I don't know
                        # how they are supposed to work.
                        itext_nodes.append(
                            node("value", value, toParseString=output_inserted)
                        )
                    elif media_type in {"image", "big-image"}:
                        if value != "-":
                            itext_nodes.append(
                                node(
                                    "value",
                                    "jr://images/" + value,
                                    form=media_type,
                                    toParseString=output_inserted,
                                )
                            )
                    elif value != "-":
                        itext_nodes.append(
                            node(
                                "value",
                                "jr://" + media_type + "/" + value,
                                form=media_type,
                                toParseString=output_inserted,
                            )
                        )

                result[-1].appendChild(node("text", *itext_nodes, id=label_name))

        return node("itext", *result)

    def date_stamp(self):
        """Returns a date string with the format of %Y_%m_%d."""
        return self._created.strftime("%Y_%m_%d")

    def _to_ugly_xml(self) -> str:
        return '<?xml version="1.0"?>' + self.xml().toxml()

    def _to_pretty_xml(self) -> str:
        """Get the XForm with human readable formatting."""
        return '<?xml version="1.0"?>\n' + self.xml().toprettyxml(indent="  ")

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return f"<pyxform.survey.Survey instance at {hex(id(self))}>"

    def _setup_xpath_dictionary(self):
        self._xpath = {}  # pylint: disable=attribute-defined-outside-init
        for element in self.iter_descendants():
            if isinstance(element, Question | Section):
                if element.name in self._xpath:
                    self._xpath[element.name] = None
                else:
                    self._xpath[element.name] = element.get_xpath()

    def _var_repl_function(
        self, matchobj, context, use_current=False, reference_parent=False
    ):
        """
        Given a dictionary of xpaths, return a function we can use to
        replace ${varname} with the xpath to varname.
        """

        name = matchobj.group(2)
        last_saved = matchobj.group(1) is not None
        is_indexed_repeat = matchobj.string.find("indexed-repeat(") > -1

        def _in_secondary_instance_predicate() -> bool:
            """
            check if ${} expression represented by matchobj
            is in a predicate for a path expression for a secondary instance
            """

            if RE_INSTANCE.search(matchobj.string) is not None:
                bracket_regex_match_iter = RE_BRACKET.finditer(matchobj.string)
                # Check whether current ${varname} is in the correct bracket_regex_match
                for bracket_regex_match in bracket_regex_match_iter:
                    if (
                        matchobj.start() >= bracket_regex_match.start()
                        and matchobj.end() <= bracket_regex_match.end()
                    ):
                        return True
                return False
            return False

        def _relative_path(ref_name: str, _use_current: bool) -> str | None:
            """Given name in ${name}, return relative xpath to ${name}."""
            return_path = None
            xpath = self._xpath[ref_name]
            context_xpath = context.get_xpath()
            # share same root i.e repeat_a from /data/repeat_a/...
            if (
                len(context_xpath.split("/")) > 2
                and xpath.split("/")[2] == context_xpath.split("/")[2]
            ):
                # if context xpath and target xpath fall under the same
                # repeat use relative xpath referencing.
                steps, ref_path = share_same_repeat_parent(
                    self, xpath, context_xpath, reference_parent
                )
                if steps:
                    ref_path = ref_path if ref_path.endswith(ref_name) else f"/{name}"
                    prefix = " current()/" if _use_current else " "
                    return_path = prefix + "/".join([".."] * steps) + ref_path + " "

            return return_path

        def _is_return_relative_path() -> bool:
            """Determine condition to return relative xpath of current ${name}."""
            indexed_repeat_relative_path_args_index = [0, 1, 3, 5]
            current_matchobj = matchobj

            if not last_saved and context:
                if not is_indexed_repeat:
                    return True

                # It is possible to have multiple indexed-repeat in an expression
                indexed_repeats_iter = RE_INDEXED_REPEAT.finditer(matchobj.string)
                for indexed_repeat in indexed_repeats_iter:
                    # Make sure current ${name} is in the correct indexed-repeat
                    if current_matchobj.end() > indexed_repeat.end():
                        try:
                            next(indexed_repeats_iter)
                            continue
                        except StopIteration:
                            return True

                    # ${name} outside of indexed-repeat always using relative path
                    if (
                        current_matchobj.end() < indexed_repeat.start()
                        or current_matchobj.start() > indexed_repeat.end()
                    ):
                        return True

                    indexed_repeat_name_index = None
                    indexed_repeat_args = (
                        RE_FUNCTION_ARGS.search(indexed_repeat.group())
                        .group(1)
                        .split(",")
                    )
                    name_arg = f"${{{name}}}"
                    for idx, arg in enumerate(indexed_repeat_args):
                        if name_arg in arg.strip():
                            indexed_repeat_name_index = idx

                    return (
                        indexed_repeat_name_index is not None
                        and indexed_repeat_name_index
                        not in indexed_repeat_relative_path_args_index
                    )

            return False

        intro = (
            f"There has been a problem trying to replace {matchobj.group(0)} with the "
            f"XPath to the survey element named '{name}'."
        )
        if name not in self._xpath:
            raise PyXFormError(intro + " There is no survey element with this name.")
        if self._xpath[name] is None:
            raise PyXFormError(
                intro + " There are multiple survey elements" " with this name."
            )

        if _is_return_relative_path():
            if not use_current:
                use_current = _in_secondary_instance_predicate()
            relative_path = _relative_path(ref_name=name, _use_current=use_current)
            if relative_path:
                return relative_path

        last_saved_prefix = (
            "instance('" + LAST_SAVED_INSTANCE_NAME + "')" if last_saved else ""
        )
        return " " + last_saved_prefix + self._xpath[name] + " "

    def insert_xpaths(self, text, context, use_current=False, reference_parent=False):
        """
        Replace all instances of ${var} with the xpath to var.
        """

        def _var_repl_function(matchobj):
            return self._var_repl_function(
                matchobj, context, use_current, reference_parent
            )

        return re.sub(BRACKETED_TAG_REGEX, _var_repl_function, str(text))

    def _var_repl_output_function(self, matchobj, context):
        """
        A regex substitution function that will replace
        ${varname} with an output element that has the xpath to varname.
        """
        return '<output value="' + self._var_repl_function(matchobj, context) + '" />'

    def insert_output_values(
        self,
        text: str,
        context: SurveyElement | None = None,
    ) -> tuple[str, bool]:
        """
        Replace all the ${variables} in text with xpaths.
        Returns that and a boolean indicating if there were any ${variables}
        present.

        :param text: Input text to process.
        :param context: The document node that the text belongs to.
        :return: The output text, and a flag indicating whether any changes were made.
        """

        def _var_repl_output_function(matchobj):
            return self._var_repl_output_function(matchobj, context)

        # There was a bug where escaping is completely turned off in labels
        # where variable replacement is used.
        # For exampke, `${name} < 3` causes an error but `< 3` does not.
        # This is my hacky fix for it, which does string escaping prior to
        # variable replacement:
        text_node = PatchedText()
        text_node.data = text
        original_xml = text_node.toxml()

        # need to make sure we have reason to replace
        # since at this point < is &lt,
        # the net effect &lt gets translated again to &amp;lt;
        xml_text = instance_expression.replace_with_output(original_xml, context, self)
        if "{" in xml_text:
            xml_text = re.sub(BRACKETED_TAG_REGEX, _var_repl_output_function, xml_text)
        changed = xml_text != original_xml
        if changed:
            return xml_text, True
        else:
            return text, False

    def print_xform_to_file(
        self, path=None, validate=True, pretty_print=True, warnings=None, enketo=False
    ) -> str:
        """
        Print the xForm to a file and optionally validate it as well by
        throwing exceptions and adding warnings to the warnings array.
        """
        if warnings is None:
            warnings = []
        if not path:
            path = self._print_name + ".xml"
        if pretty_print:
            xml = self._to_pretty_xml()
        else:
            xml = self._to_ugly_xml()
        try:
            with open(path, mode="w", encoding="utf-8") as file_obj:
                file_obj.write(xml)
        except Exception:
            if os.path.exists(path):
                os.unlink(path)
            raise
        if validate:
            warnings.extend(odk_validate.check_xform(path))
        if enketo:
            warnings.extend(enketo_validate.check_xform(path))

        # Warn if one or more translation is missing a valid IANA subtag
        translations = self._translations.keys()
        if translations:
            bad_languages = get_languages_with_bad_tags(translations)
            if bad_languages:
                warnings.append(
                    "The following language declarations do not contain "
                    "valid machine-readable codes: "
                    + ", ".join(bad_languages)
                    + ". "
                    + "Learn more: http://xlsform.org#multiple-language-support"
                )
        return xml

    def to_xml(self, validate=True, pretty_print=True, warnings=None, enketo=False):
        """
        Generates the XForm XML.
        validate is True by default - pass the XForm XML through ODK Validator.
        pretty_print is True by default - formats the XML for readability.
        warnings - if a list is passed it stores all warnings generated
        enketo - pass the XForm XML though Enketo Validator.

        Return XForm XML string.
        """
        # On Windows, NamedTemporaryFile must be opened exclusively.
        # So it must be explicitly created, opened, closed, and removed.
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.close()
        try:
            # this will throw an exception if the xml is not valid
            xml = self.print_xform_to_file(
                path=tmp.name,
                validate=validate,
                pretty_print=pretty_print,
                warnings=warnings,
                enketo=enketo,
            )
        finally:
            Path(tmp.name).unlink(missing_ok=True)
        return xml

    def instantiate(self):
        """
        Instantiate as in return a instance of SurveyInstance for collected
        data.
        """
        return SurveyInstance(self)

"""
Survey module with XForm Survey objects and utility functions.
"""

import os
import re
import tempfile
import xml.etree.ElementTree as ETree
from collections import defaultdict
from collections.abc import Generator, Iterable
from datetime import datetime
from itertools import chain
from pathlib import Path

from pyxform import aliases, constants
from pyxform.constants import EXTERNAL_INSTANCE_EXTENSIONS, NSMAP
from pyxform.errors import PyXFormError, ValidationError
from pyxform.external_instance import ExternalInstance
from pyxform.instance import SurveyInstance
from pyxform.parsing.expression import RE_PYXFORM_REF
from pyxform.parsing.instance_expression import replace_with_output
from pyxform.question import Itemset, MultipleChoiceQuestion, Option, Question, Tag
from pyxform.section import SECTION_EXTRA_FIELDS, RepeatingSection, Section
from pyxform.survey_element import _GET_SENTINEL, SURVEY_ELEMENT_FIELDS, SurveyElement
from pyxform.survey_elements.attribute import Attribute
from pyxform.utils import (
    LAST_SAVED_INSTANCE_NAME,
    DetachableElement,
    escape_text_for_xml,
    node,
)
from pyxform.validators import enketo_validate, odk_validate
from pyxform.validators.pyxform import unique_names
from pyxform.validators.pyxform.iana_subtags.validation import get_languages_with_bad_tags
from pyxform.validators.pyxform.pyxform_reference import (
    has_pyxform_reference_with_last_saved,
    is_pyxform_reference_candidate,
)

RE_BRACKET = re.compile(r"\[([^]]+)\]")
RE_FUNCTION_ARGS = re.compile(r"\b[^()]+\((.*)\)$")
RE_INDEXED_REPEAT = re.compile(r"indexed-repeat\([^)]+\)")
RE_INSTANCE = re.compile(r"instance\([^)]+.+")
RE_INSTANCE_SECONDARY_REF = re.compile(
    r"(instance\(.*\)\/root\/item\[.*?(\$\{.*\})\]\/.*?)\s"
)
RE_PULLDATA = re.compile(r"(pulldata\s*\(\s*)(.*?),")
SEARCH_FUNCTION_REGEX = re.compile(r"search\(.*?\)")
SELECT_TYPES = set(aliases.select)


class InstanceInfo:
    """Standardise Instance details relevant during XML generation."""

    __slots__ = ("context", "instance", "name", "src", "type")

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


def get_path_relative_to_lcar(
    target: SurveyElement,
    source: SurveyElement,
    lcar_steps_source: int,
    lcar: SurveyElement,
    reference_parent: bool = False,
) -> tuple[int, str]:
    """
    Get the number of steps from the source to the LCAR, and the path to the target.

    Implementation assumes that it is only called if target and source have an LCAR.

    Example:
        target = /data/repeat_a/group_a/name
        source = /data/repeat_a/group_b/age
        return = (2, "/group_a/name")

    :param target: The reference target, like "/data/repeat/q1" for "${q1}"
    :param source: The reference source, where the reference is located.
    :param lcar_steps_source: The number of path segments from the source to the LCAR.
    :param lcar: The lowest common ancestor repeat.
    :param reference_parent: If True, calculate to the LCAR parent rather than the LCAR.
      This may not be actually honoured depending on the topography.
    """

    def is_repeat(e: SurveyElement) -> bool:
        return isinstance(e, Section) and e.type == constants.REPEAT

    # Currently reference_parent only used for itemsets containing a pyxform variable,
    # i.e. `select_one ${ref}`. In that case, an extra step up the reference path may be
    # required, to allow appending a choice filter predicate.
    if reference_parent:
        # The LCAR may or may not be the closest ancestor repeat for source or target,
        # but there's always at least the LCAR, so a check for None isn't needed.
        source_car, _ = next(source.iter_ancestors(condition=is_repeat), (None, None))
        target_car, _ = next(target.iter_ancestors(condition=is_repeat), (None, None))
        # May return None if LCAR is a child of the Survey, or only non-repeating group(s).
        lcar_not_in_repeat = next(lcar.iter_ancestors(condition=is_repeat), None) is None

        if lcar is target_car and (lcar_not_in_repeat or source_car is not lcar):
            # Only honour the request for a reference relative to lcar parent
            # if the target is not inside nested repeat(s) under lcar, and either:
            # a) lcar is not in a repeat.
            # b) source is in nested repeats under lcar.
            return lcar_steps_source + 1, target.get_xpath(relative_to=lcar.parent)

    _, lca_steps_source, _, lca = source.lowest_common_ancestor(target)
    return lca_steps_source, target.get_xpath(relative_to=lca)


def recursive_dict():
    return defaultdict(recursive_dict)


SURVEY_EXTRA_FIELDS = (
    "_created",
    "_translations",
    "_xpath",
    "add_none_option",
    "clean_text_values",
    "attribute",
    "auto_delete",
    "auto_send",
    "choices",
    "default_language",
    "file_name",
    "id_string",
    "instance_name",
    "instance_xmlns",
    "namespaces",
    "omit_instanceID",
    "public_key",
    "setgeopoint_by_triggering_ref",
    "setvalues_by_triggering_ref",
    "sms_allow_media",
    "sms_date_format",
    "sms_datetime_format",
    "sms_keyword",
    "sms_response",
    "sms_separator",
    "style",
    "submission_url",
    "title",
    "version",
    constants.ALLOW_CHOICE_DUPLICATES,
    constants.CLIENT_EDITABLE,
    constants.COMPACT_DELIMITER,
    constants.COMPACT_PREFIX,
    constants.ENTITY_VERSION,
)
SURVEY_FIELDS = (*SURVEY_ELEMENT_FIELDS, *SECTION_EXTRA_FIELDS, *SURVEY_EXTRA_FIELDS)


class Survey(Section):
    """
    Survey class - represents the full XForm XML.
    """

    __slots__ = SURVEY_EXTRA_FIELDS

    @staticmethod
    def get_slot_names() -> tuple[str, ...]:
        return SURVEY_FIELDS

    def __init__(self, **kwargs):
        # Internals
        self._created: datetime.now = datetime.now()
        self._translations: recursive_dict = recursive_dict()
        self._xpath: dict[str, Section | Question | None] | None = None

        # Structure
        # attribute is for custom instance attrs from settings e.g. attribute::abc:xyz
        self.attribute: dict | None = None
        self.choices: dict[str, Itemset] | None = None
        self.entity_version: constants.EntityVersion | None = None
        self.setgeopoint_by_triggering_ref: dict[str, list[str]] = {}
        self.setvalues_by_triggering_ref: dict[str, list[str]] = {}

        # Common / template settings
        self.default_language: str = ""
        self.id_string: str = ""
        self.instance_name: str = ""
        self.style: str | None = None
        self.title: str = ""
        self.version: str = ""

        # Other settings
        self.add_none_option: bool = False
        self.allow_choice_duplicates: bool = False
        self.auto_delete: str | None = None
        self.auto_send: str | None = None
        self.clean_text_values: bool = False
        self.client_editable: bool = False
        self.instance_xmlns: str | None = None
        self.namespaces: str | None = None
        self.omit_instanceID: bool = False
        self.public_key: str | None = None
        self.submission_url: str | None = None

        # SMS / compact settings
        self.delimiter: str | None = None
        self.prefix: str | None = None
        self.sms_allow_media: bool | None = None
        self.sms_date_format: str | None = None
        self.sms_datetime_format: str | None = None
        self.sms_keyword: str | None = None
        self.sms_response: str | None = None
        self.sms_separator: str | None = None

        choices = kwargs.pop("choices", None)
        if choices and isinstance(choices, dict):
            self.choices = {
                list_name: Itemset(name=list_name, choices=values)
                for list_name, values in choices.items()
            }
        kwargs[constants.TYPE] = constants.SURVEY
        super().__init__(fields=SURVEY_EXTRA_FIELDS, **kwargs)

    def to_json_dict(self, delete_keys: Iterable[str] | None = None) -> dict:
        to_delete = (k for k in self.get_slot_names() if k.startswith("_"))
        if delete_keys is not None:
            to_delete = chain(to_delete, delete_keys)
        return super().to_json_dict(delete_keys=to_delete)

    def validate(self):
        if self.id_string in {None, "None"}:
            raise PyXFormError("Survey cannot have an empty id_string")
        super().validate()
        self._validate_uniqueness_of_section_names()

    def _validate_uniqueness_of_section_names(self):
        root_node_name = self.name
        repeat_names = set()
        for element in self.iter_descendants(
            condition=lambda i: isinstance(i, RepeatingSection)
        ):
            unique_names.validate_repeat_name(
                name=element.name,
                control_type=constants.REPEAT,
                instance_element_name=root_node_name,
                seen_names=repeat_names,
            )

    def get_nsmap(self):
        """Add additional namespaces"""
        if self.entity_version:
            entities_ns = " entities=http://www.opendatakit.org/xforms/entities"
            if self.namespaces is None:
                self.namespaces = entities_ns
            else:
                self.namespaces += entities_ns

        if self.namespaces:
            nslist = [
                ns.split("=")
                for ns in self.namespaces.split()
                if len(ns.split("=")) == 2 and ns.split("=")[0] != ""
            ]
            nsmap = NSMAP.copy()
            nsmap.update(
                {
                    f"xmlns:{k}": v.replace('"', "").replace("'", "")
                    for k, v in nslist
                    if f"xmlns:{k}" not in nsmap
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

        body_kwargs = {}
        if self.style:
            body_kwargs["class"] = self.style
        nsmap = self.get_nsmap()

        return node(
            "h:html",
            node("h:head", node("h:title", self.title), self.xml_model()),
            node("h:body", *self.xml_control(survey=self), **body_kwargs),
            **nsmap,
        )

    def _generate_static_instances(
        self, list_name: str, itemset: Itemset
    ) -> InstanceInfo:
        """
        Generate <instance> elements for static data (e.g. choices for selects)
        """

        def choice_nodes(idx, choice):
            # Add a unique id to the choice element in case there are itext references
            if itemset.requires_itext:
                yield node("itextId", f"{list_name}-{idx}")
            yield node(constants.NAME, choice.name)
            choice_label = choice.label
            if not itemset.requires_itext and isinstance(choice_label, str):
                yield node(constants.LABEL, choice_label)
            choice_extra_data = choice.extra_data
            if choice_extra_data and isinstance(choice_extra_data, dict):
                for k, v in choice_extra_data.items():
                    yield node(k, v)
            choice_sms_option = choice.sms_option
            if choice_sms_option and isinstance(choice_sms_option, str):
                yield node("sms_option", choice_sms_option)

        def instance_nodes(choices):
            for idx, choice in enumerate(choices):
                yield node("item", choice_nodes(idx, choice))

        return InstanceInfo(
            type="choice",
            context="survey",
            name=list_name,
            src=None,
            instance=node(
                "instance",
                node("root", instance_nodes(itemset.options)),
                id=list_name,
            ),
        )

    @staticmethod
    def _generate_external_instances(element: ExternalInstance) -> InstanceInfo:
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
    def _generate_pulldata_instances(
        element: Question | Section,
    ) -> Generator[InstanceInfo, None, None]:
        def get_pulldata_functions(element):
            """
            Returns a list of different pulldata(... function strings if
            pulldata function is defined at least once for any of:
            calculate, constraint, readonly, required, relevant
            """
            functions_present = []
            for formula_name in constants.EXTERNAL_INSTANCES:
                if (
                    hasattr(element, "bind")
                    and element.bind is not None
                    and "pulldata(" in str(element["bind"].get(formula_name))
                ):
                    functions_present.append(element["bind"][formula_name])
            if (
                hasattr(element, constants.CHOICE_FILTER)
                and element.choice_filter is not None
                and "pulldata(" in str(element[constants.CHOICE_FILTER])
            ):
                functions_present.append(element[constants.CHOICE_FILTER])
            if (
                hasattr(element, "default")
                and element.default is not None
                and "pulldata(" in str(element["default"])
            ):
                functions_present.append(element["default"])

            return functions_present

        def get_instance_info(elem, file_id):
            uri = f"jr://file-csv/{file_id}.csv"
            parent = elem.parent

            return InstanceInfo(
                type="pulldata",
                context=f"[type: {parent.type}, name: {parent.name}]",
                name=file_id,
                src=uri,
                instance=node("instance", id=file_id, src=uri),
            )

        pulldata_usages = get_pulldata_functions(element)
        if len(pulldata_usages) > 0:
            for usage in pulldata_usages:
                for call_match in re.finditer(RE_PULLDATA, usage):
                    groups = call_match.groups()
                    if len(groups) == 2:
                        first_argument = (  # first argument to pulldata()
                            groups[1].replace("'", "").replace('"', "").strip()
                        )
                        yield get_instance_info(element, first_argument)

    @staticmethod
    def _generate_from_file_instances(
        element: MultipleChoiceQuestion,
    ) -> InstanceInfo | None:
        itemset = element.itemset
        if not itemset:
            return None
        file_id, ext = os.path.splitext(itemset)
        if itemset and ext in EXTERNAL_INSTANCE_EXTENSIONS:
            file_ext = "file" if ext in {".xml", ".geojson"} else f"file-{ext[1:]}"
            uri = f"jr://{file_ext}/{itemset}"
            return InstanceInfo(
                type="file",
                context=f"[type: {element.parent.type}, name: {element.parent.name}]",
                name=file_id,
                src=uri,
                instance=node("instance", id=file_id, src=uri),
            )

    @staticmethod
    def _generate_last_saved_instance(element: Question) -> bool:
        """
        True if a last-saved instance should be generated, false otherwise.
        """
        if element.default and has_pyxform_reference_with_last_saved(element.default):
            return True
        if element.choice_filter and has_pyxform_reference_with_last_saved(
            element.choice_filter
        ):
            return True
        if element.bind:
            # Assuming average len(bind) < 10 and len(EXTERNAL_INSTANCES) = 5 and the
            # current has_last_saved implementation, iterating bind keys is fastest.
            for k, v in element.bind.items():
                if (
                    k in constants.EXTERNAL_INSTANCES
                    and v
                    and has_pyxform_reference_with_last_saved(v)
                ):
                    return True
        return False

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

    def _generate_instances(self) -> Generator[DetachableElement, None, None]:
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

        def get_element_instances():
            generate_last_saved = False
            for i in self.iter_descendants():
                if isinstance(i, Question):
                    yield from self._generate_pulldata_instances(element=i)
                    if isinstance(i, MultipleChoiceQuestion):
                        i_file = self._generate_from_file_instances(element=i)
                        if i_file:
                            yield i_file
                    if not generate_last_saved:
                        generate_last_saved = self._generate_last_saved_instance(
                            element=i
                        )
                elif isinstance(i, Section):
                    yield from self._generate_pulldata_instances(element=i)
                elif isinstance(i, ExternalInstance):
                    yield self._generate_external_instances(element=i)

            if generate_last_saved:
                yield self._get_last_saved_instance()

            # Append last so the choice instance is excluded on a name clash.
            if self.choices:
                for k, v in self.choices.items():
                    if not v.used_by_search:
                        yield self._generate_static_instances(list_name=k, itemset=v)

        instances = tuple(get_element_instances())

        # Check that external instances have unique names.
        if instances:
            self._validate_external_instances(
                instances=(x for x in instances if x.type == "external")
            )

        seen = {}
        for i in instances:
            prior = seen.get(i.name)
            if prior:
                if prior.src != i.src:
                    # Instance id exists with different src URI -> error.
                    msg = (
                        "The same instance id will be generated for different "
                        "external instance source URIs. Please check the form."
                        f" Instance name: '{i.name}', Existing type: '{prior.type}', "
                        f"Existing URI: '{prior.src}', Duplicate type: '{i.type}', "
                        f"Duplicate URI: '{i.src}', Duplicate context: '{i.context}'."
                    )
                    raise PyXFormError(msg)
                else:
                    # Instance id exists with same src URI -> ok, don't duplicate.
                    continue
            else:
                # Instance doesn't exist yet -> add it.
                yield i.instance
            seen[i.name] = i

    def xml_model_bindings(self) -> Generator[DetachableElement | None, None, None]:
        """
        Yield bindings (bind or action elements) for this node and all its descendants.
        """
        for e in self.iter_descendants(
            condition=lambda i: not isinstance(i, Option | Tag)
        ):
            yield from e.xml_bindings(survey=self)

            if isinstance(e, Attribute | Question):
                yield from e.xml_actions(survey=self, in_repeat=False)

    def xml_model(self):
        """
        Generate the xform <model> element
        """
        self._setup_translations()
        self._setup_media()
        self._add_empty_translations()

        model_kwargs = {"odk:xforms-version": constants.CURRENT_XFORMS_VERSION}

        if self.entity_version:
            model_kwargs["entities:entities-version"] = self.entity_version.value

        model_children = []
        if self._translations:
            model_children.append(self.itext())
        model_children.append(
            node("instance", self.xml_instance()),
        )

        if any(
            (
                self.submission_url,
                self.public_key,
                self.auto_send,
                self.auto_delete,
                self.client_editable,
            )
        ):
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
            if self.client_editable:
                submission_attrs["odk:client-editable"] = "true"
            submission_node = node("submission", **submission_attrs)
            model_children.insert(0, submission_node)

        def model_children_generator():
            yield from model_children
            yield from self._generate_instances()
            yield from self.xml_model_bindings()

        return node("model", model_children_generator(), **model_kwargs)

    def xml_instance(self, **kwargs):
        result = Section.xml_instance(self, survey=self, **kwargs)

        # set these first to prevent overwriting id and version
        if self.attribute:
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

    def _redirect_is_search_itext(self, element: MultipleChoiceQuestion) -> bool:
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
        is_search = False
        try:
            appearance = element.control[constants.APPEARANCE]
            if appearance and len(appearance) > 7:
                is_search = bool(SEARCH_FUNCTION_REGEX.search(appearance))
        except (KeyError, TypeError):
            pass
        if is_search:
            ext = os.path.splitext(element.itemset)[1]
            if ext and ext in EXTERNAL_INSTANCE_EXTENSIONS:
                msg = (
                    f"Question '{element.name}' is a select from file type, "
                    "using 'search()'. This combination is not supported. "
                    "Remove the 'search()' usage, or change the select type."
                )
                raise PyXFormError(msg)

            choices = None
            if self.choices:
                choices = self.choices.get(element.itemset, None)
            if not choices:
                choices = element.choices
            element.itemset = ""
            if not choices.used_by_search:
                choices.used_by_search = True
                for i, opt in enumerate(choices.options):
                    opt._choice_itext_ref = f"jr:itext('{choices.name}-{i}')"
        return is_search

    def _setup_translations(self):
        """
        set up the self._translations dict which will be referenced in the
        setup media and itext functions
        """

        def get_choice_content(name, idx, choice):
            itext_id = f"{name}-{idx}"

            choice_label = choice.label
            if choice_label:
                if isinstance(choice_label, dict):
                    for lang, value in choice_label.items():
                        if isinstance(value, dict):
                            for language, val in value.items():
                                yield ([language, itext_id, lang], val)
                        else:
                            yield ([lang, itext_id, "long"], value)
                else:
                    yield ([self.default_language, itext_id, "long"], choice_label)

            choice_media = choice.media
            if choice_media:
                for media, value in choice_media.items():
                    if isinstance(value, dict):
                        for language, val in value.items():
                            yield ([language, itext_id, media], val)
                    else:
                        yield ([self.default_language, itext_id, media], value)

        def get_choices():
            for name, itemset in self.choices.items():
                if itemset.requires_itext:
                    for idx, choice in enumerate(itemset.options):
                        yield from get_choice_content(name, idx, choice)

        if self.choices:
            for path, value in get_choices():
                last_path = path.pop()
                leaf_value = {last_path: value, constants.TYPE: constants.CHOICE}
                self._add_to_nested_dict(self._translations, path, leaf_value)

        search_lists = set()
        non_search_lists = set()
        for element in self.iter_descendants(
            condition=lambda i: isinstance(i, Question | Section)
        ):
            if isinstance(element, MultipleChoiceQuestion):
                select_ref = (element.name, element.list_name)
                if self._redirect_is_search_itext(element=element):
                    search_lists.add(select_ref)
                else:
                    non_search_lists.add(select_ref)

            # Create translations questions.
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
                paths[path] = paths.get(path, set()).union(content)

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
                if media_type not in constants.SUPPORTED_MEDIA_TYPES:
                    raise PyXFormError(f"Media type: {media_type} not supported")

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

        for item in self.iter_descendants(
            condition=lambda i: isinstance(i, Section | Question)
        ):
            # Skip set up of media for choices in selects. Translations for their media
            # content should have been set up in _setup_translations, with one copy of
            # each choice translation per language (after _add_empty_translations).
            media_dict = item.media
            if isinstance(media_dict, dict) and media_dict:
                translation_key = f"{item.get_xpath()}:label"
                _set_up_media_translations(media_dict, translation_key)

    def itext(self) -> DetachableElement:
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
                                    f"jr://images/{value}",
                                    form=media_type,
                                    toParseString=output_inserted,
                                )
                            )
                    elif value != "-":
                        itext_nodes.append(
                            node(
                                "value",
                                f"jr://{media_type}/{value}",
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
        return f"""<?xml version="1.0"?>{self.xml().toxml()}"""

    def _to_pretty_xml(self) -> str:
        """Get the XForm with human readable formatting."""
        return f"""<?xml version="1.0"?>\n{self.xml().toprettyxml(indent="  ")}"""

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return f"<pyxform.survey.Survey instance at {hex(id(self))}>"

    def _setup_xpath_dictionary(self):
        if self._xpath:
            return
        xpaths = {}
        for element in self.iter_descendants(lambda i: isinstance(i, Question | Section)):
            element_name = element.name
            if element_name in xpaths:
                xpaths[element_name] = None
            else:
                xpaths[element_name] = element
        self._xpath = xpaths

    def get_element_by_name(
        self, name: str, error_prefix: str | None = None
    ) -> SurveyElement:
        element = self._xpath.get(name, _GET_SENTINEL)

        prefix = ""
        if error_prefix:
            prefix = f"{error_prefix} "

        if element is _GET_SENTINEL:
            raise PyXFormError(f"{prefix}There is no survey element named '{name}'.")
        elif element is None:
            raise PyXFormError(
                f"{prefix}There are multiple survey elements named '{name}'."
            )

        return element

    def _var_repl_function(
        self, matchobj, context, use_current=False, reference_parent=False
    ):
        """
        Given a dictionary of xpaths, return a function we can use to
        replace ${varname} with the xpath to varname.
        """

        name = matchobj.group("ncname")
        last_saved = matchobj.group("last_saved") is not None
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
            target = self._xpath[ref_name]
            # if context xpath and target xpath fall under the same
            # repeat use relative xpath referencing.
            relation = context.lowest_common_ancestor(
                other=target, group_type=constants.REPEAT
            )
            if relation[0] == "Common Ancestor":
                steps, ref_path = get_path_relative_to_lcar(
                    target=target,
                    source=context,
                    lcar_steps_source=relation[1],
                    lcar=relation[3],
                    reference_parent=reference_parent,
                )
                if steps:
                    ref_path = ref_path if ref_path.endswith(ref_name) else f"/{name}"
                    prefix = " current()/" if _use_current else " "
                    return_path = (
                        f"""{prefix}{"/".join(".." for _ in range(steps))}{ref_path} """
                    )

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
            f"""There has been a problem trying to replace {matchobj.group("pyxform_ref")} """
            f"""with the XPath to the survey element named '{name}'."""
        )
        target_xpath = self.get_element_by_name(name=name, error_prefix=intro).get_xpath()

        if _is_return_relative_path():
            if not use_current:
                use_current = _in_secondary_instance_predicate()
            relative_path = _relative_path(ref_name=name, _use_current=use_current)
            if relative_path:
                return relative_path

        last_saved_prefix = (
            f"instance('{LAST_SAVED_INSTANCE_NAME}')" if last_saved else ""
        )
        return f" {last_saved_prefix}{target_xpath} "

    def insert_xpaths(
        self,
        text: str,
        context: SurveyElement,
        use_current: bool = False,
        reference_parent: bool = False,
    ):
        """
        Replace all instances of ${var} with the xpath to var.

        :param text: The string to perform dereferencing on.
        :param context: The context to use for relative references (if any).
        :param use_current: If True, use 'current()' in the relative reference (if any).
        :param reference_parent: Reference the lowest common ancestor repeat parent,
          rather than using the shortest possible relative path.
        """
        # "text" may actually be a dict, e.g. for custom attributes.
        value = str(text)

        if not is_pyxform_reference_candidate(value):
            return value

        def _var_repl_function(matchobj):
            return self._var_repl_function(
                matchobj, context, use_current, reference_parent
            )

        return re.sub(RE_PYXFORM_REF, _var_repl_function, value)

    def _var_repl_output_function(self, matchobj, context):
        """
        A regex substitution function that will replace
        ${varname} with an output element that has the xpath to varname.
        """
        return f"""<output value="{self._var_repl_function(matchobj, context)}" />"""

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
        if text == "-":
            return text, False

        def _var_repl_output_function(matchobj):
            return self._var_repl_output_function(matchobj, context)

        # There was a bug where escaping is completely turned off in labels
        # where variable replacement is used.
        # For exampke, `${name} < 3` causes an error but `< 3` does not.
        # This is my hacky fix for it, which does string escaping prior to
        # variable replacement:
        original_xml = escape_text_for_xml(text=text)

        # need to make sure we have reason to replace
        # since at this point < is &lt,
        # the net effect &lt gets translated again to &amp;lt;
        value = replace_with_output(original_xml, context, self)
        if is_pyxform_reference_candidate(value):
            value = re.sub(RE_PYXFORM_REF, _var_repl_output_function, value)
        changed = value != original_xml
        if changed:
            return value, True
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
            path = f"{self.id_string}.xml"
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
        translations = self._translations
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
        tmp_path = Path(tmp.name)
        try:
            # this will throw an exception if the xml is not valid
            xml = self.print_xform_to_file(
                path=tmp_path,
                validate=validate,
                pretty_print=pretty_print,
                warnings=warnings,
                enketo=enketo,
            )
        finally:
            tmp_path.unlink(missing_ok=True)
        return xml

    def instantiate(self):
        """
        Instantiate as in return a instance of SurveyInstance for collected
        data.
        """
        return SurveyInstance(self)

from section import Section
from question import Question
from utils import node, XFORM_TAG_REGEXP
from collections import defaultdict
import codecs
from datetime import datetime
import re
import os
from odk_validate import check_xform
from survey_element import SurveyElement
from errors import PyXFormError


nsmap = {
    u"xmlns": u"http://www.w3.org/2002/xforms",
    u"xmlns:h": u"http://www.w3.org/1999/xhtml",
    u"xmlns:ev": u"http://www.w3.org/2001/xml-events",
    u"xmlns:xsd": u"http://www.w3.org/2001/XMLSchema",
    u"xmlns:jr": u"http://openrosa.org/javarosa",
    }

class Survey(Section):
    
    FIELDS = Section.FIELDS.copy()
    FIELDS.update(
        {
            u"_xpath": dict,
            u"_created": datetime.now,
            u"title": unicode,
            u"id_string": unicode,
            u"file_name": unicode,
            u"default_language": unicode,
            u"_translations": dict,
            }
        )

    def validate(self):
        super(Survey, self).validate()
        self._validate_uniqueness_of_section_names()

    def _validate_uniqueness_of_section_names(self):
        section_names = []
        for e in self.iter_descendants():
            if isinstance(e, Section):
                if e.name in section_names:
                    raise PyXFormError("There are two sections with the name %s." % e.name)
                section_names.append(e.name)

    #TODO: Maybe rename XML functions to generate_[x], so it's clear they are not just getters.
    def xml(self):
        """
        calls necessary preparation methods, then returns the xml.
        """
        self.validate()
        self._setup_xpath_dictionary()
        return node(u"h:html",
                    node(u"h:head",
                         node(u"h:title", self.title),
                         self.xml_model()
                        ),
                    node(u"h:body", *self.xml_control()),
                    **nsmap
                    )

    def xml_model(self):
        self._setup_translations()
        # self._setup_media()
        if self._translations:
            return node("model",
                        self.itext(),
                        node("instance", self.xml_instance()),
                        *self.xml_bindings()
                        )
        return node("model",
                    node("instance", self.xml_instance()),
                    *self.xml_bindings()
                    )

    def xml_instance(self):
        result = Section.xml_instance(self)
        result.setAttribute(u"id", self.id_string)
        return result

    def _setup_translations(self):
        self._translations = defaultdict(dict)
        for e in self.iter_descendants():
            for d in e.get_translations():
                self._translations[d['lang']][d['path']] = d['text']
        self._add_empty_translations()

    def _add_empty_translations(self):
        paths = []
        for lang, d in self._translations.items():
            for path, text in d.items():
                if path not in paths:
                    paths.append(path)
        for lang, d in self._translations.items():
            for path in paths:
                if path not in d:
                    self._translations[lang][path] = u"-"

    def _setup_media(self):
        """
        Merges any media files in with the translations so that they
        all end up in the itext node. This method is handles the
        following cases:

            -Media files exist and no label translations exist
            -Media files exist and label translations exist
            -Media translations exist and label translations exist

        The following cases are not yet covered:
            -Media files exist and no label is provided at all
        """
        #TODO: Cover the uncovered case.
        translationsExist = self._translations
        if not translationsExist:
            self._translations = defaultdict(dict)
        for e in self.iter_descendants():
            media_keys = e.get_media_keys()
            for key in media_keys:
                media_key = media_keys[key]
                text = e.get(key)
                if type(text) == dict:
                    for media_type in text.keys():
                        #Check if this media file's language is specified
                        langs = [media_type.partition(":")[-1]]
                        media_type_to_store = media_type.partition(":")[0]

                        langsExist = langs != [u'']
                        if not langsExist and not translationsExist:
                            langs = self.default_language
                            print langs
                            media_type_to_store = media_type
                        elif not langsExist and translationsExist:
                            # If no language is specified, but there
                            # are label translations, add the media
                            # file to all languages.
                            langs = self._translations.keys()
                            media_type_to_store = media_type

                        for lang in langs:
                            if media_type_to_store in SurveyElement.SUPPORTED_MEDIA:

                                #Find the translation node we will be adding to
                                translation_key = media_key.partition(":")[0] + ":label"

                                if not translationsExist:
                                    # If there are no translations
                                    # specified, pull the generic
                                    # label.
                                    if u"label" in e.to_dict():
                                        translation_label = e.to_dict()[u"label"]
                                        e.set(u"label", {lang: translation_label})
                                    else:
                                        raise PyXFormError(e.name, "Must include a label")
                                elif not langsExist:
                                    if u"label" in e.to_dict():
                                        translation_label = e.to_dict()[u"label"]

                                        if type(translation_label) == dict:
                                            for key in translation_label:
                                                translation_label = translation_label[key]
                                                break
                                        e.set(u"label", {lang: translation_label})
                                    else:
                                        translation_label = None
                                elif translation_key not in self._translations[lang]:
                                    if u"label" in e.to_dict():
                                        labels = e.to_dict()[u"label"]
                                        if type(labels) == dict and lang in labels:
                                            translation_label = labels[u"lang"]
                                            e.set(u"label", {lang: translation_label})
                                        elif type(labels) == dict and not lang in labels:
                                            translation_label = None
                                            e.set(u"label", {lang: None})
                                        else:
                                            translation_label = e.to_dict()[u"label"]
                                            e.set(u"label", {lang: translation_label})
                                    else:
                                        raise PyXFormError(e.name, "Must include a label")
                                else:
                                    translation_label = self._translations[lang][translation_key]

                                #Initialize the entry to a dictionary
                                if not translation_label:
                                    self._translations[lang][translation_key] = {}
                                if not (translation_key in self._translations[lang] and type(self._translations[lang][translation_key]) == dict):
                                    self._translations[lang][translation_key] = {"long": translation_label}

                                self._translations[lang][translation_key][media_type_to_store] = text[media_type]

                            else:
                                raise PyXFormError("Media type: " + media_type_to_store + " not supported")

    def itext(self):
        """
        itext can be images/audio/video/text
        It can be localized for different languages which is what most of these attributes are for.
        @see http://code.google.com/p/opendatakit/wiki/XFormDesignGuidelines
        """
        children = []
        for lang, d in self._translations.items():
            kwargs = {'lang': lang}
            if lang == self.default_language:
                kwargs['default'] = ''
            children.append(node("translation", **kwargs))

            for path, text in d.items():
                t = node("text", node("value", text), id=path)
                children[-1].appendChild(t)

            # TODO: figure out how to get media in here smoothly

        return node("itext", *children)

    def date_stamp(self):
        return self._created.strftime("%Y_%m_%d")

    def _to_pretty_xml(self):
        """
        I want the to_xml method to by default validate the xml we are
        producing.
        """
        # Hacky way of pretty printing xml without adding extra white
        # space to text
        # TODO: check out pyxml
        # http://ronrothman.com/public/leftbraned/xml-dom-minidom-toprettyxml-and-silly-whitespace/
        xml_with_linebreaks = self.xml().toprettyxml(indent='  ')
        text_re = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)
        output_re = re.compile('\n.*(<output.*>)\n(\s\s\s\s)*')
        prettyXml = text_re.sub('>\g<1></', xml_with_linebreaks)
        inlineOutput = output_re.sub('\g<1>', prettyXml)
        return inlineOutput

    def __unicode__(self):
        return "<survey name='%s' element_count='%s'>" % (self.name, len(self.children))

    def _setup_xpath_dictionary(self):
        self._xpath = {}
        for element in self.iter_descendants():
            if isinstance(element, Question) or isinstance(element, Section):
                if element.name in self._xpath:
                    self._xpath[element.name] = None
                else:
                    self._xpath[element.name] = element.get_xpath()

    def _var_repl_function(self):
        """
        Given a dictionary of xpaths, return a function we can use to
        replace ${varname} with the xpath to varname.
        """
        def repl(matchobj):
            name = matchobj.group(1)
            intro = "There has been a problem trying to replace ${%s} with the XPath to the survey element named '%s'." % (name, name)
            if name not in self._xpath:
                raise PyXFormError(intro + " There is no survey element with this name.")
            if self._xpath[name] is None:
                raise PyXFormError(intro + " There are multiple survey elements with this name.")
            return self._xpath[name]
        return repl

    def insert_xpaths(self, text):
        """
        Replace all instances of ${var} with the xpath to var.
        """
        bracketed_tag = r"\$\{(" + XFORM_TAG_REGEXP + r")\}"
        return re.sub(bracketed_tag, self._var_repl_function(), unicode(text))

    def _var_repl_output_function(self,matchobj):
        """
        Given a dictionary of xpaths, return a function we can use to
        replace ${varname} with the xpath to varname.
        """
        if matchobj.group(1) not in self._xpath:
            raise PyXFormError("There is no survey element with this name.",
                            matchobj.group(1))
        return '<output value="' + self._xpath[matchobj.group(1)] + '" />'


    def insert_output_values(self, text):
        bracketed_tag = r"\$\{(" + XFORM_TAG_REGEXP + r")\}"
        result = re.sub(bracketed_tag, self._var_repl_output_function, unicode(text))
        return result, not result == text

    def print_xform_to_file(self, path="", validate=True):
        if not path:
            path = self._print_name + ".xml"
        fp = codecs.open(path, mode="w", encoding="utf-8")
        fp.write(self._to_pretty_xml())
        fp.close()
        if validate:
            check_xform(path)

    def to_xml(self, validate=True, pretty=True):
        temporary_file_name = "_temporary_file_used_to_validate_xform.xml"
        temporary_file_path = os.path.abspath(temporary_file_name)
        # this will throw an exception if the xml is not valid
        self.print_xform_to_file(temporary_file_path)
        os.remove(temporary_file_name)
        return self._to_pretty_xml()
    
    #TODO: Figure out why we need a survey class and a survey instance class.
    #    This get's called by a test specifically made for it and nothing else.
    def instantiate(self):
        from instance import SurveyInstance
        return SurveyInstance(self)

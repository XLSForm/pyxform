from question import MultipleChoiceQuestion
from section import Section
from question import Question
from utils import node, SEP, XFORM_TAG_REGEXP
from datetime import datetime
from collections import defaultdict
import codecs
import re
import json
import os
from odk_validate import check_xform

nsmap = {
    u"xmlns" : u"http://www.w3.org/2002/xforms",
    u"xmlns:h" : u"http://www.w3.org/1999/xhtml",
    u"xmlns:ev" : u"http://www.w3.org/2001/xml-events",
    u"xmlns:xsd" : u"http://www.w3.org/2001/XMLSchema",
    u"xmlns:jr" : u"http://openrosa.org/javarosa",
    }

class Survey(Section):
    def __init__(self, *args, **kwargs):
        Section.__init__(self, *args, **kwargs)
        self._xpath = {}
        self._parent = None
        self._created = datetime.now()
        self._id_string = kwargs.get(u'id_string')

    def xml(self):
        """
        calls necessary preparation methods, then returns the xml.
        """
        self.validate()
        self._setup_xpath_dictionary()
        return node(u"h:html",
                    node(u"h:head",
                         node(u"h:title", self.get_name()),
                         self.xml_model()
                        ),
                    node(u"h:body", *self.xml_control()),
                    **nsmap
                    )
        
        # return E(ns("h", "html"),
        #          E(ns("h", "head"),
        #            E(ns("h", "title"), self.get_name()),
        #            self.xml_model()
        #            ),
        #          E(ns("h", "body"), *self.xml_control())
        #          )

    def xml_model(self):
        self._setup_translations()
        if self._languages != []:
            return node("model",
                        self.xml_translations(),
                        node("instance", self.xml_instance()),
                        *self.xml_bindings()
                        )
        return node("model",
                    node("instance", self.xml_instance()),
                    *self.xml_bindings()
                    )

    def _setup_translations(self):
        languages = set()
        for survey_element in self.iter_children():
            for display_element in ["label", "hint"]:
                d = survey_element.get(display_element)
                if type(d) == dict:
                    for language in d.keys():
                        languages.add(language)
        self._languages = list(languages)

    def xml_translations(self):
        result = []
        for language in self._languages:
            translation_node = node("translation", lang=language)
            result.append(translation_node)
            for survey_element in self.iter_children():
                for display_element in ["label", "hint"]:
                    d = survey_element.get(display_element)
                    if type(d) == dict and d != {}:
                        text = d.get(language, u"-")
                        translation_path = u":".join([
                                survey_element.get_xpath(),
                                display_element
                                ])
                        result[-1].appendChild(
                            node("text",
                                node("value", text),
                                id=translation_path
                                )
                            )
        return node("itext", *result)

    def date_stamp(self):
        return self._created.strftime("%Y_%m_%d")

    def set_id_string(self, id_string):
        self._id_string = id_string

    def id_string(self):
        if self._id_string is None:
            self._id_string = self.get_name() + "_" + self.date_stamp()
        return self._id_string

    def xml_instance(self):
        result = Section.xml_instance(self)
        result.setAttribute(u"id", self.id_string())
        return result

    def _to_xml(self):
        """
        I want the to_xml method to by default validate the xml we are
        producing.
        """
        return self.xml().toxml()
    
    def __unicode__(self):
        return "<survey name='%s' element_count='%s'>" % (self.get_name(), len(self._children))
    
    def _setup_xpath_dictionary(self):
        self._xpath = {}
        for element in self.iter_children():
            if isinstance(element, Question) or isinstance(element, Section):
                if element.get_name() in self._xpath:
                    self._xpath[element.get_name()] = None
                else:
                    self._xpath[element.get_name()] = element.get_xpath()
        
    def _var_repl_function(self):
        """
        Given a dictionary of xpaths, return a function we can use to
        replace ${varname} with the xpath to varname.
        """
        def repl(matchobj):
            if matchobj.group(1) not in self._xpath:
                raise Exception("There is no survey element with this name.",
                                matchobj.group(1))
            return self._xpath[matchobj.group(1)]
        return repl

    def insert_xpaths(self, text):
        """
        Replace all instances of ${var} with the xpath to var.
        """
        bracketed_tag = r"\$\{(" + XFORM_TAG_REGEXP + r")\}"
        return re.sub(bracketed_tag, self._var_repl_function(), text)

    def print_xform_to_file(self, path="", validate=True):
        if not path: path = self.id_string() + ".xml"
        fp = codecs.open(path, mode="w", encoding="utf-8")
        fp.write(self._to_xml())
        fp.close()
        if validate:
            check_xform(path)

    def to_xml(self):
        temporary_file_name = "_temporary_file_used_to_validate_xform.xml"
        temporary_file_path = os.path.abspath(temporary_file_name)
        # this will throw an exception if the xml is not valid
        self.print_xform_to_file(temporary_file_path)
        os.remove(temporary_file_name)
        return self._to_xml()
        
    def instantiate(self):
        from instance import SurveyInstance
        return SurveyInstance(self)

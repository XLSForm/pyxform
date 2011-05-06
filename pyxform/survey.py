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
from survey_element import SurveyElement

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
        self._setup_media()
        if self._translations:
            return node("model",
                        self.xml_translations_and_media(),
                        node("instance", self.xml_instance()),
                        *self.xml_bindings()
                        )
        return node("model",
                    node("instance", self.xml_instance()),
                    *self.xml_bindings()
                    )

    def _setup_translations(self):
        self._translations = defaultdict(dict)
        for e in self.iter_children():
            translation_keys = e.get_translation_keys()
            for key in translation_keys.keys():
                translation_key = translation_keys[key]
                text = e.get(key)
                if type(text)==dict:
                    for lang in text.keys():
                        if translation_key in self._translations[lang]:
                            assert self._translations[lang][translation_key] == text[lang], "The labels for this translation key are inconsistent %(key)s %(label)s" % {"key" : translation_key, "label" : text[lang]}
                        else:
                            self._translations[lang][translation_key] = text[lang]
                            
    def _setup_media(self):
        """
        Merges any media files in with the translations so that they all end up in the itext node. This method is handles the following cases:
            -Media files exist and no label translations exist
            -Media files exist and label translations exist
            -Media translations exist and label translations exist
            
        The following cases are not yet covered:
            -Media files exist and no label is provided at all
            -Media translations exist and no label translations exist (is this valid? Do we need to support it?)
        """
        translationsExist = self._translations
        if not translationsExist:
            self._translations = defaultdict(dict)
        for e in self.iter_children():
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
                            #If no language is specified, just default to English
                            langs = ["English"]
                            media_type_to_store = media_type
                        elif not langsExist and translationsExist:
                            #If no language is specified, but there are label translations, add the media file to 
                            #all languages
                            langs = self._translations.keys()
                            media_type_to_store = media_type
                        
                        for lang in langs:
                            if media_type_to_store in SurveyElement.SUPPORTED_MEDIA:
                                #Find the translation node we will be adding to
                                translation_key = media_key.partition(":")[0] + ":label"
                                
                                if not translationsExist:
                                    #If there are no translations specified, pull the generic label
                                    translation_label = e.to_dict()[u"label"]
                                else:
                                    translation_label = self._translations[lang][translation_key]
                                
                                #Initialize the entry to a dictionary
                                if not (translation_key in self._translations[lang] and type(self._translations[lang][translation_key]) == dict):
                                    self._translations[lang][translation_key] = {"long": translation_label}
                                
                                self._translations[lang][translation_key][media_type_to_store]= text[media_type]
                            
                            else:
                                raise Exception("Media type: " + media_type_to_store + " not supported")        
    
    def xml_translations_and_media(self):
        result = []
        for lang in self._translations.keys():
            result.append(node("translation", lang=lang))
            for label_name in self._translations[lang].keys():
                itext_nodes = []
                
                if type(self._translations[lang][label_name]) == dict:
                    for media_type in self._translations[lang][label_name]:
                        if media_type == "long":
                            itext_nodes.append(node("value", self._translations[lang][label_name][media_type], form=media_type))
                        else:
                            itext_nodes.append(node("value", "jr://" + media_type + "/" + self._translations[lang][label_name][media_type], form=media_type))
                else:
                    itext_nodes.append(node("value", self._translations[lang][label_name], form="long"))

                result[-1].appendChild(node("text", *itext_nodes, id=label_name))
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

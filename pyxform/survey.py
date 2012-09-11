import tempfile
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
    u"xmlns:orx": u"http://openrosa.org/xforms/"
    }

class Survey(Section):
    
    FIELDS = Section.FIELDS.copy()
    FIELDS.update(
        {
            u"_xpath": dict,
            u"_created": datetime.now, #This can't be dumped to json
            u"title": unicode,
            u"id_string": unicode,
            u"file_name": unicode,
            u"default_language": unicode,
            u"_translations": dict,
            u"submission_url": unicode,
            u"public_key": unicode,
            u"instance_xmlns": unicode
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
        """
        Generate the xform <model> element
        """
        self._setup_translations()
        self._setup_media()
        model_children = [node("instance", self.xml_instance())] + self.xml_bindings()
        if self._translations:
            model_children.insert(0, self.itext())
        if self.submission_url:
            #We need to add a unique form instance id if the form is to be submitted. 
            model_children.append(node("bind", nodeset="/"+self.name+"/meta/instanceID", type="string", readonly="true()", calculate="concat('uuid:', uuid())"))
            
            if self.public_key:
                submission_node = node("submission", method="form-data-post", action=self.submission_url, base64RsaPublicKey=self.public_key)
            else:
                submission_node = node("submission", method="form-data-post", action=self.submission_url)
            model_children.insert(0, submission_node)
        return node("model",  *model_children)

    def xml_instance(self):
        result = Section.xml_instance(self)
        result.setAttribute(u"id", self.id_string)

        #add instance xmlns attribute to the instance node
        if self.instance_xmlns:
            result.setAttribute(u"xmlns", self.instance_xmlns)
        
        #We need to add a unique form instance id if the form is to be submitted.
        if self.submission_url:
            result.appendChild(node("orx:meta", node("orx:instanceID")))
            
        return result

    def _setup_translations(self):
        """
        set up the self._translations dict which will be referenced in the setup media and itext functions
        """
        self._translations = defaultdict(dict)
        for element in self.iter_descendants():
            for d in element.get_translations(self.default_language):
                self._translations[d['lang']][d['path']] = {"long" : d['text']}
        self._add_empty_translations()

    def _add_empty_translations(self):
        """
        For every path used, if a language does not include that path, add it,
        and give it a "-" value. Added because for hints, you want to allow empty
        translations for the default language (otherwise the validator complains).
        """
        paths = []
        for lang, d in self._translations.items():
            for path, text in d.items():
                if path not in paths:
                    paths.append(path)
        
        #We lose the ability to have the default language be the fallback by adding empty translations for everything.
        #we could just add them for the default language by using the following two lines of code instead of the for loop          
        #lang = self.default_language
        #d = self._translations[self.default_language]
        for lang, d in self._translations.items():
            for path in paths:
                if path not in d:
                    self._translations[lang][path] = {"long":u"-"}

    def _setup_media(self):
        """
        Traverse the survey, find all the media, and put in into the _translations data structure which looks like this:
        {language : {element_xpath : {media_type : media}}}
        It matches the xform nesting order.
        """
        if not self._translations:
            self._translations = defaultdict(dict)
        
        for survey_element in self.iter_descendants():
            
            translation_key = survey_element.get_xpath() + ":label"
            media_dict = survey_element.get(u"media")
            
            for media_type, possibly_localized_media in media_dict.items():
                
                if media_type not in SurveyElement.SUPPORTED_MEDIA:
                    raise PyXFormError("Media type: " + media_type + " not supported")
                
                localized_media = dict()
                
                if type(possibly_localized_media) is dict:
                    #media is localized
                    localized_media = possibly_localized_media
                else:    
                    #media is not localized so create a localized version using the default language
                    localized_media = { self.default_language : possibly_localized_media }
                    
                for language, media in localized_media.items():
                    
                    #Create the required dictionaries in _translations, then add media as a leaf value:
                    
                    if language not in self._translations:
                        self._translations[language] = {}
                    
                    translations_language = self._translations[language]
                    
                    if translation_key not in translations_language:
                        translations_language[translation_key] = {}
                    
                    #if type(translations_language[translation_key]) is not dict:
                    #    translations_language[translation_key] = {"long" : translations_language[translation_key]}
                    
                    translations_trans_key = translations_language[translation_key]
                    
                    if media_type not in translations_trans_key:
                            translations_trans_key[media_type] = {}
                        
                    translations_trans_key[media_type] = media

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
                result.append(node("translation", lang=lang,default=u"true()"))
                #result.append(node("translation", lang=lang))
            else:
                result.append(node("translation", lang=lang))

            for label_name, content in translation.items():
                itext_nodes = []
                label_type = label_name.partition(":")[-1]

                if type(content) is not dict: raise Exception()
                
                for media_type, media_value in content.items():
                    
                    #There is a odk/jr bug where hints can't have a value for the "form" attribute.
                    #This is my workaround.
                    if label_type == u"hint":
                        value, outputInserted = self.insert_output_values(media_value)
                        itext_nodes.append(node("value", value, toParseString=outputInserted))
                        continue
                    
                    if media_type == "long":
                        value, outputInserted = self.insert_output_values(media_value)
                        #I'm ignoring long types for now because I don't know how they are supposed to work.
                        #itext_nodes.append(node("value", value, form=media_type, toParseString=outputInserted))
                        itext_nodes.append(node("value", value, toParseString=outputInserted))
                    elif media_type == "image":
                        itext_nodes.append(node("value", "jr://images/" + media_value, form=media_type))
                    else:
                        itext_nodes.append(node("value", "jr://" + media_type + "/" + media_value, form=media_type))


                result[-1].appendChild(node("text", *itext_nodes, id=label_name))
                
        return node("itext", *result)

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
        """
        Replace all the ${variables} in text with xpaths.
        Returns that and a boolean indicating if there were any ${variables} present.
        """
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
        with tempfile.NamedTemporaryFile() as tmp:
            # this will throw an exception if the xml is not valid
            self.print_xform_to_file(tmp.name)
        return self._to_pretty_xml()
    
    def instantiate(self):
        """
        Instantiate as in return a instance of SurveyInstance for collected data.
        """
        from instance import SurveyInstance
        return SurveyInstance(self)

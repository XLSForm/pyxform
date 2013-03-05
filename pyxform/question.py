from utils import node
from survey_element import SurveyElement
from question_type_dictionary import QUESTION_TYPE_DICT
from errors import PyXFormError


class Question(SurveyElement):

    def validate(self):
        SurveyElement.validate(self)

        # make sure that the type of this question exists in the
        # question type dictionary.
        if self.type not in QUESTION_TYPE_DICT:
            raise PyXFormError(
                "Unknown question type '%s'." % self.type
                )

    def xml_instance(self):
        if self.get(u"default"):
            #survey = self.get_root()
            #return node(self.name, survey.insert_xpaths(unicode(self.get(u"default"))))
            return node(self.name, unicode(self.get(u"default")))
        return node(self.name)

    def xml_control(self):
        return None


class InputQuestion(Question):
    """
    This control string is the same for: strings, integers, decimals,
    dates, geopoints, barcodes ...
    """
    def xml_control(self):
        control_dict = self.control
        label_and_hint = self.xml_label_and_hint()
        control_dict['ref'] = self.get_xpath()
        result = node(**control_dict)
        if label_and_hint:
            for element in self.xml_label_and_hint():
                result.appendChild(element)
        return result

class TriggerQuestion(Question):

    def xml_control(self):
        control_dict = self.control
        if u"appearance" in control_dict:
            return node(
                u"trigger", ref=self.get_xpath(),
                appearance=control_dict[u"appearance"],
                *self.xml_label_and_hint()
                )
        else:
            return node(u"trigger",
                ref=self.get_xpath(),
                *self.xml_label_and_hint()
                )


class UploadQuestion(Question):
    def _get_media_type(self):
        return self.control[u"mediatype"]

    def xml_control(self):
        control_dict = self.control
        if u"appearance" in control_dict:
            return node(
                u"upload",
                ref=self.get_xpath(),
                mediatype=self._get_media_type(),
                appearance=control_dict[u"appearance"],
                *self.xml_label_and_hint()
                )
        else:
            return node(
                u"upload",
                ref=self.get_xpath(),
                mediatype=self._get_media_type(),
                *self.xml_label_and_hint()
                )


class Option(SurveyElement):

    def xml_value(self):
        return node(u"value", self.name)

    def xml(self):
        item = node(u"item")
        xml_label = self.xml_label()
        item.appendChild(self.xml_label())
        item.appendChild(self.xml_value())
        return item

    def validate(self):
        pass

#class MultipleChoiceQuestion(Question):
#
#    def xml_control(self):
#        assert self.bind[u"type"] in [u"select", u"select1"]
#        control_dict = self.control.copy()
#        control_dict['ref'] = self.get_xpath()
#        nodeset = "instance('" + self['itemset'] + "')/root/item"
#        choice_filter = self.get('choice_filter')
#        if choice_filter:
#            survey = self.get_root()
#            choice_filter = survey.insert_xpaths(choice_filter)
#            nodeset += '[' + choice_filter + ']'
#        result = node(**control_dict)
#        for element in self.xml_label_and_hint():
#            result.appendChild(element)
#        itemset_label_ref = "jr:itext(itextId)"
#        itemset_children = [node('value', ref='name'), node('label', ref=itemset_label_ref)]
#        result.appendChild(node('itemset', *itemset_children, nodeset=nodeset))
#        return result
#        
#class SelectOneQuestion(MultipleChoiceQuestion):
#    pass
    
class MultipleChoiceQuestion(Question):

    def __init__(self, *args, **kwargs):
        kwargs_copy = kwargs.copy()
        #Notice that choices can be specified under choices or children. I'm going to try to stick to just choices.
        #Aliases in the json format will make it more difficult to use going forward.
        choices = kwargs_copy.pop(u"choices", []) + \
            kwargs_copy.pop(u"children", [])
        Question.__init__(self, *args, **kwargs_copy)
        for choice in choices:
            self.add_choice(**choice)

    def add_choice(self, **kwargs):
        option = Option(**kwargs)
        self.add_child(option)

    def validate(self):
        Question.validate(self)
        descendants = self.iter_descendants()
        descendants.next() # iter_descendants includes self; we need to pop it 
        for choice in descendants: 
            choice.validate()

    def xml_control(self):
        assert self.bind[u"type"] in [u"select", u"select1"]

        control_dict = self.control.copy()
        control_dict['ref'] = self.get_xpath()
        result = node(**control_dict)
        for element in self.xml_label_and_hint():
            result.appendChild(element)
        survey = self.get_root()
        # itemset are only supposed to be strings, check to prevent the rare dicts that show up
        if self['itemset'] and isinstance( self['itemset'] , basestring):
            choice_filter = self.get('choice_filter')
            nodeset = "instance('" + self['itemset'] + "')/root/item"
            choice_filter = survey.insert_xpaths(choice_filter)
            if choice_filter:
                nodeset += '[' + choice_filter + ']'
            itemset_label_ref = "jr:itext(itextId)"
            itemset_children = [node('value', ref='name'), node('label', ref=itemset_label_ref)]
            result.appendChild(node('itemset', *itemset_children, nodeset=nodeset))
        else:
            for n in [o.xml() for o in self.children]:
                result.appendChild(n)
        return result


class SelectOneQuestion(MultipleChoiceQuestion):
    def __init__(self, *args, **kwargs):
        super(SelectOneQuestion, self).__init__(*args, **kwargs)
        self._dict[self.TYPE] = u"select one"

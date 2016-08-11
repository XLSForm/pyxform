import os.path

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
        survey = self.get_root()
        attributes = {}
        attributes.update(self.get(u'instance', {}))
        for key, value in attributes.items():
            attributes[key] = survey.insert_xpaths(value)
        if self.get(u"default"):
            return node(
                self.name, unicode(self.get(u"default")), **attributes
            )
        return node(self.name, **attributes)

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
        survey = self.get_root()
        # Resolve field references in attributes
        for key, value in control_dict.items():
            control_dict[key] = survey.insert_xpaths(value)
        control_dict['ref'] = self.get_xpath()

        result = node(**control_dict)
        if label_and_hint:
            for element in self.xml_label_and_hint():
                result.appendChild(element)

        # Input types are used for selects with external choices sheets.
        if self['query']:
            choice_filter = self.get('choice_filter')
            query = "instance('" + self['query'] + "')/root/item"
            choice_filter = survey.insert_xpaths(choice_filter)
            if choice_filter:
                query += '[' + choice_filter + ']'
            result.setAttribute('query', query)
        return result


class TriggerQuestion(Question):

    def xml_control(self):
        control_dict = self.control
        survey = self.get_root()
        # Resolve field references in attributes
        for key, value in control_dict.items():
            control_dict[key] = survey.insert_xpaths(value)
        control_dict['ref'] = self.get_xpath()
        return node(
            u"trigger",
            *self.xml_label_and_hint(),
            **control_dict
            )


class UploadQuestion(Question):
    def _get_media_type(self):
        return self.control[u"mediatype"]

    def xml_control(self):
        control_dict = self.control
        control_dict['ref'] = self.get_xpath()
        control_dict['mediatype'] = self._get_media_type()
        return node(
            u"upload",
            *self.xml_label_and_hint(),
            **control_dict
            )


class Option(SurveyElement):

    def xml_value(self):
        return node(u"value", self.name)

    def xml(self):
        item = node(u"item")
        self.xml_label()
        item.appendChild(self.xml_label())
        item.appendChild(self.xml_value())

        return item

    def validate(self):
        pass


class MultipleChoiceQuestion(Question):

    def __init__(self, *args, **kwargs):
        kwargs_copy = kwargs.copy()
        # Notice that choices can be specified under choices or children.
        # I'm going to try to stick to just choices.
        # Aliases in the json format will make it more difficult
        # to use going forward.
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
        descendants.next()  # iter_descendants includes self; we need to pop it

        for choice in descendants:
            choice.validate()

    def xml_control(self):
        assert self.bind[u"type"] in [u"select", u"select1"]
        survey = self.get_root()
        control_dict = self.control.copy()
        # Resolve field references in attributes
        for key, value in control_dict.items():
            control_dict[key] = survey.insert_xpaths(value)
        control_dict['ref'] = self.get_xpath()

        result = node(**control_dict)
        for element in self.xml_label_and_hint():
            result.appendChild(element)
        # itemset are only supposed to be strings,
        # check to prevent the rare dicts that show up
        if self['itemset'] and isinstance(self['itemset'], basestring):
            choice_filter = self.get('choice_filter')
            itemset, file_extension = os.path.splitext(self['itemset'])
            itemset = itemset \
                if file_extension in ['.csv', '.xml'] else self['itemset']
            nodeset = "instance('" + itemset + "')/root/item"
            choice_filter = survey.insert_xpaths(choice_filter)
            if choice_filter:
                nodeset += '[' + choice_filter + ']'
            itemset_label_ref = "jr:itext(itextId)"
            itemset_children = [node('value', ref='name'),
                                node('label', ref=itemset_label_ref)]
            result.appendChild(node('itemset', *itemset_children,
                                    nodeset=nodeset))
        else:
            for n in [o.xml() for o in self.children]:
                result.appendChild(n)
        return result


class SelectOneQuestion(MultipleChoiceQuestion):
    def __init__(self, *args, **kwargs):
        super(SelectOneQuestion, self).__init__(*args, **kwargs)
        self._dict[self.TYPE] = u"select one"


class Tag(SurveyElement):
    def __init__(self, *args, **kwargs):
        kwargs_copy = kwargs.copy()
        choices = kwargs_copy.pop(u"choices", []) + \
            kwargs_copy.pop(u"children", [])

        super(Tag, self).__init__(*args, **kwargs_copy)

        if choices:
            self.children = []

            for choice in choices:
                option = Option(**choice)
                self.add_child(option)

    def xml(self):
        result = node(u"tag", key=self.name)
        self.xml_label()
        result.appendChild(self.xml_label())
        for choice in self.children:
            result.appendChild(choice.xml())

        return result

    def validate(self):
        pass


class OsmUploadQuestion(UploadQuestion):
    def __init__(self, *args, **kwargs):
        kwargs_copy = kwargs.copy()
        tags = kwargs_copy.pop(u"tags", []) + \
            kwargs_copy.pop(u"children", [])

        super(OsmUploadQuestion, self).__init__(*args, **kwargs_copy)

        if tags:
            self.children = []

            for tag in tags:
                self.add_tag(**tag)

    def add_tag(self, **kwargs):
        tag = Tag(**kwargs)
        self.add_child(tag)

    def xml_control(self):
        control_dict = self.control
        control_dict['ref'] = self.get_xpath()
        control_dict['mediatype'] = self._get_media_type()
        result = node(
            u"upload",
            *self.xml_label_and_hint(),
            **control_dict
            )

        for osm_tag in self.children:
            result.appendChild(osm_tag.xml())

        return result

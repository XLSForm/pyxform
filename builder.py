from survey_element import SurveyElement
from question import Question, InputQuestion, UploadQuestion, MultipleChoiceQuestion
from section import Section, RepeatingSection, GroupedSection
from survey import Survey
import utils
from pyxform.xls2json import ExcelReader

class SurveyElementBuilder(object):
    # we use this CLASSES dict to create questions from dictionaries
    QUESTION_CLASSES = {
        u"" : Question,
        u"input" : InputQuestion,
        u"select" : MultipleChoiceQuestion,
        u"select1" : MultipleChoiceQuestion,
        u"upload" : UploadQuestion,
        }

    SECTION_CLASSES = {
        u"group" : GroupedSection,
        u"repeat" : RepeatingSection,
        u"survey" : Survey,
        }

    def _get_question_class(self, question_type_str):
        if question_type_str not in Question.TYPES:
            raise Exception("Unknown question type", question_type_str)
        question_type = Question.TYPES[question_type_str]
        control_dict = question_type.get(Question.CONTROL, {})
        control_tag = control_dict.get(u"tag", u"")
        return self.QUESTION_CLASSES[control_tag]

    def _create_question_from_dict(self, d):
        """
        This function returns None for unrecognized types.
        """
        question_type_str = d[Question.TYPE]
        # hack job right here to get this to work
        if question_type_str.endswith(u" or specify other"):
            d_copy = d.copy()
            question_type_str = question_type_str[:len(question_type_str)-len(u" or specify other")]
            d_copy[Question.TYPE] = question_type_str
            # This is dangerous because we need translations
            d_copy[u"choices"].append({
                    u"name" : u"other",
                    u"label" : dict(
                        [(lang, u"Other") for lang in d[Question.LABEL].keys()]
                        )
                    })
            return [self._create_question_from_dict(d_copy),
                    self._create_specify_other_question_from_dict(d_copy)]
        question_class = self._get_question_class(question_type_str)
        if question_class: return question_class(**d)
        return []

    def _create_specify_other_question_from_dict(self, d):
        kwargs = {
            Question.TYPE : u"text",
            Question.NAME : u"%s_other" % d[Question.NAME],
            Question.LABEL : d[Question.LABEL],
            Question.BIND : {u"relevant" : u"selected(../%s, 'other')" % d[Question.NAME]}
            }
        return InputQuestion(**kwargs)

    def _create_section_from_dict(self, d):
        kwargs = d.copy()
        children = kwargs.pop(Section.CHILDREN)
        section_class = self.SECTION_CLASSES[kwargs[Section.TYPE]]
        result = section_class(**kwargs)
        for child in children:
            survey_element = self.create_survey_element_from_dict(child)
            if survey_element: result.add_child(survey_element)
        return result

    def _create_table_from_dict(self, d):
        kwargs = d.copy()
        keys_to_delete = [u"type", u"children", u"columns"]
        for key in keys_to_delete: del kwargs[key]
        result = GroupedSection(**kwargs)

        for column in d[u"columns"]:
            # create a new group for each column
            try:
                kwargs = dict([(k, column[k]) for k in [Section.NAME, Section.LABEL]])
            except KeyError:
                raise Exception("Column is missing name or label", column)
            g = GroupedSection(**kwargs)
            for child in d[SurveyElement.CHILDREN]:
                copy = child.copy()
                try:
                    self._add_column_label_to_question_label(column, copy)
                except TypeError:
                    # there's no '%s' substitution to fill
                    pass
                g.add_child(self.create_survey_element_from_dict(copy))
            result.add_child(g)
        return result

    def _add_column_label_to_question_label(self, column, question):
        new_label = {}
        for lang in column[Section.LABEL].keys():
            new_label[lang] = question[Question.LABEL][lang] % column[Section.LABEL][lang]                
        question[Question.LABEL] = new_label

    def create_survey_element_from_dict(self, d):
        if d[SurveyElement.TYPE] in self.SECTION_CLASSES:
            return self._create_section_from_dict(d)
        elif d[SurveyElement.TYPE]==u"table":
            return self._create_table_from_dict(d)
        elif d[SurveyElement.TYPE]==u"include":
            excel_reader = ExcelReader(d[SurveyElement.NAME])
            include_dict = excel_reader.to_dict()
            assert include_dict[SurveyElement.TYPE]==u"survey" # this would be better placed in a test of xls2json
            include_dict[SurveyElement.TYPE] = u"group"
            for key in d.keys():
                if key not in [SurveyElement.TYPE, SurveyElement.NAME]:
                    assert key not in include_dict
                    include_dict[key] = d[key]
            return create_survey_element_from_dict(include_dict)
        else:
            return self._create_question_from_dict(d)

def create_survey_element_from_dict(d):
    builder = SurveyElementBuilder()
    return builder.create_survey_element_from_dict(d)

def create_survey_element_from_json(str_or_path):
    d = utils.get_pyobj_from_json(str_or_path)
    return create_survey_element_from_dict(d)

from survey_element import SurveyElement
from question import Question, InputQuestion, UploadQuestion, MultipleChoiceQuestion
from section import Section, RepeatingSection, GroupedSection
from survey import Survey
import utils
from xls2json import ExcelReader

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

    def _create_loop_from_dict(self, d):
        result = []

        # columns is a left over from when this was
        # create_table_from_dict, I will need to clean this up
        for column in d[u"columns"]:
            for child in d[SurveyElement.CHILDREN]:
                question_dict = self._create_question_dict_from_template_and_info(child, column)
                question = self.create_survey_element_from_dict(question_dict)
                result.append(question)
        return result

    def _create_question_dict_from_template_and_info(self, question_template, info):
        info_by_lang = dict(
            [(lang, {u"name" : info[u"name"], u"label" : info[u"label"][lang]}) for lang in info[u"label"].keys()]
            )

        template_copy = question_template.copy()
        for key in template_copy.keys():
            if type(template_copy[key])==unicode:
                template_copy[key] = template_copy[key] % info
            elif type(template_copy[key])==dict:
                template_copy[key] = template_copy[key].copy()
                for key2 in template_copy[key].keys():
                    template_copy[key][key2] = template_copy[key][key2] % info_by_lang.get(key2, info)
        return template_copy

    def _create_table_from_dict(self, d):
        try:
            kwargs = dict([(k, d[k]) for k in [Section.NAME, Section.LABEL]])
        except KeyError:
            raise Exception("This table is missing either a name or a label.", d)
        result = GroupedSection(**kwargs)
        for column in d[u"columns"]:
            # create a new group for each column
            try:
                kwargs = dict([(k, column[k]) for k in [Section.NAME, Section.LABEL]])
            except KeyError:
                raise Exception("Column is missing name or label", column)
            g = GroupedSection(**kwargs)
            for child in d[SurveyElement.CHILDREN]:
                g.add_child(self.create_survey_element_from_dict(child))
            result.add_child(g)
        return result

    def create_survey_element_from_dict(self, d):
        if d[SurveyElement.TYPE] in self.SECTION_CLASSES:
            return self._create_section_from_dict(d)
        elif d[SurveyElement.TYPE]==u"loop":
            return self._create_loop_from_dict(d)
        elif d[SurveyElement.TYPE]==u"include":
            excel_reader = ExcelReader(d[SurveyElement.NAME])
            include_dict = excel_reader.to_dict()
            full_survey = create_survey_element_from_dict(include_dict)
            return full_survey.get_children()
        elif d[SurveyElement.TYPE]==u"table":
            return self._create_table_from_dict(d)
        else:
            return self._create_question_from_dict(d)

def create_survey_element_from_dict(d):
    builder = SurveyElementBuilder()
    return builder.create_survey_element_from_dict(d)

def create_survey_element_from_json(str_or_path):
    d = utils.get_pyobj_from_json(str_or_path)
    return create_survey_element_from_dict(d)

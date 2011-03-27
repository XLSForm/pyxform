from survey_element import SurveyElement
from question import Question, InputQuestion, UploadQuestion, MultipleChoiceQuestion
from section import Section, RepeatingSection, GroupedSection
from survey import Survey
import utils
from xls2json import ExcelReader
from question_type_dictionary import DEFAULT_QUESTION_TYPE_DICTIONARY

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

    def __init__(self, **kwargs):
        self._question_type_dictionary = kwargs.get(
            u"question_type_dictionary",
            DEFAULT_QUESTION_TYPE_DICTIONARY
            )

    def _get_question_class(self, question_type_str):
        question_type = self._question_type_dictionary.get_definition(question_type_str)
        control_dict = question_type.get(Question.CONTROL, {})
        control_tag = control_dict.get(u"tag", u"")
        return self.QUESTION_CLASSES[control_tag]

    def _create_question_from_dict(self, d):
        """
        This function returns None for unrecognized types.
        """
        question_type_str = d[Question.TYPE]
        d_copy = d.copy()

        if question_type_str.startswith(u"select all that apply"):
            self._add_none_option_to_select_all_that_apply(d_copy)

        # hack job right here to get this to work
        if question_type_str.endswith(u" or specify other"):
            question_type_str = question_type_str[:len(question_type_str)-len(u" or specify other")]
            d_copy[Question.TYPE] = question_type_str
            self._add_other_option_to_multiple_choice_question(d_copy)
            return [self._create_question_from_dict(d_copy),
                    self._create_specify_other_question_from_dict(d_copy)]
        question_class = self._get_question_class(question_type_str)
        if question_class: return question_class(**d_copy)
        return []

    def _add_other_option_to_multiple_choice_question(self, d):
        # ideally, we'd just be pulling from children
        choice_list = d.get(u"choices", d.get(u"children", []))
        assert len(choice_list)>0, "There should be choices for this question."
        other_choice = {
            u"name" : u"other",
            u"label" : u"Other",
            }
        if other_choice not in choice_list:
            choice_list.append(other_choice)

    def _add_none_option_to_select_all_that_apply(self, d_copy):
        choice_list = d_copy.get(u"choices", d_copy.get(u"children", []))
        assert len(choice_list)>0, "There should be choices for this question."
        none_choice = {
            u"name" : u"none",
            u"label" : u"None",
            }
        if none_choice not in choice_list:
            choice_list.append(none_choice)
            none_constraint = u"(.='none' or not(selected(., 'none')))"
            if u"bind" not in d_copy: d_copy[u"bind"] = {}
            if u"constraint" in d_copy[u"bind"]:
                d_copy[u"bind"][u"constraint"] += " and " + none_constraint
            else:
                d_copy[u"bind"][u"constraint"] = none_constraint

    def _label_hack(self, label_to_repeat, question_label):
        if type(question_label)==unicode:
            return label_to_repeat
        if type(question_label)==dict:
            return dict([(lang, label_to_repeat) for lang in question_label.keys()])
        else:
            raise Exception("Question label is expected to be unicode or dict",
                            question_label)

    def _create_specify_other_question_from_dict(self, d):
        kwargs = {
            Question.TYPE : u"text",
            Question.NAME : u"%s_other" % d[Question.NAME],
            Question.LABEL : self._label_hack("Specify other.", d[Question.LABEL]),
            Question.BIND : {u"relevant" : u"selected(../%s, 'other')" % d[Question.NAME]},
            }
        return InputQuestion(**kwargs)

    def _create_section_from_dict(self, d):
        d_copy = d.copy()
        children = d_copy.pop(Section.CHILDREN)
        section_class = self.SECTION_CLASSES[d_copy[Section.TYPE]]
        result = section_class(**d_copy)
        for child in children:
            survey_element = self.create_survey_element_from_dict(child)
            if survey_element: result.add_child(survey_element)
        return result

    def _create_loop_from_dict(self, d):
        d_copy = d.copy()
        d_copy.pop(u"children", "")
        d_copy.pop(u"columns", "")
        result = GroupedSection(**d_copy)

        # columns is a left over from when this was
        # create_table_from_dict, I will need to clean this up
        for loop_item in d[u"columns"]:
            kwargs = {
                Section.NAME : loop_item.get(Section.NAME, u""),
                Section.LABEL : loop_item.get(Section.LABEL, u""),
                }
            # if this is a none option for a select all that apply
            # question then we should skip adding it to the result
            if kwargs[Section.NAME]=="none": continue

            column = GroupedSection(**kwargs)
            for child in d[SurveyElement.CHILDREN]:
                question_dict = self._create_question_dict_from_template_and_info(child, loop_item)
                question = self.create_survey_element_from_dict(question_dict)
                column.add_child(question)
            result.add_child(column)
        if result.get_name()!=u"": return result
        return result.get_children()

    def _create_question_dict_from_template_and_info(self, question_template, info):
        # if the label in info has multiple languages setup a
        # dictionary by language to do substitutions.
        if type(info[u"label"])==dict:
            info_by_lang = dict(
                [(lang, {u"name" : info[u"name"], u"label" : info[u"label"][lang]}) for lang in info[u"label"].keys()]
                )

        result = question_template.copy()
        for key in result.keys():
            if type(result[key])==unicode:
                result[key] = result[key] % info
            elif type(result[key])==dict:
                result[key] = result[key].copy()
                for key2 in result[key].keys():
                    if type(info[u"label"])==dict:
                        result[key][key2] = result[key][key2] % info_by_lang.get(key2, info)
                    else:
                        result[key][key2] = result[key][key2] % info
        return result

    def create_survey_element_from_dict(self, d):
        if d[SurveyElement.TYPE] in self.SECTION_CLASSES:
            return self._create_section_from_dict(d)
        elif d[SurveyElement.TYPE]==u"loop":
            return self._create_loop_from_dict(d)
        elif d[SurveyElement.TYPE]==u"include":
            path = d[SurveyElement.NAME]
            if path.endswith(".xls"):
                full_survey = create_survey_from_xls(path)
                return full_survey.get_children()
            elif path.endswith(".json"):
                full_survey = create_survey_element_from_json(path)
                return full_survey.get_children()
        else:
            return self._create_question_from_dict(d)

def create_survey_element_from_dict(d):
    builder = SurveyElementBuilder()
    return builder.create_survey_element_from_dict(d)

def create_survey_element_from_json(str_or_path):
    d = utils.get_pyobj_from_json(str_or_path)
    return create_survey_element_from_dict(d)

def create_survey_from_xls(path):
    # Interestingly enough this behaves differently than a json dump
    # and create survey element from json. This is because to
    # questions that share the same choice list cannot share the same
    # choice list in json. This is definitely something to think
    # about.
    excel_reader = ExcelReader(path)
    d = excel_reader.to_dict()
    return create_survey_element_from_dict(d)

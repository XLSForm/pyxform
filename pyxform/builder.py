from survey_element import SurveyElement
from question import Question, InputQuestion, UploadQuestion, MultipleChoiceQuestion
from section import Section, RepeatingSection, GroupedSection
from survey import Survey
import utils
from xls2json import SurveyReader
from question_type_dictionary import DEFAULT_QUESTION_TYPE_DICTIONARY, \
     QuestionTypeDictionary
import os, glob

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
        self.set_sections(
            kwargs.get(u"sections", {})
            )
        self.set_question_type_dictionary(
            kwargs.get(u"question_type_dictionary")
            )

    def set_sections(self, sections):
        """
        sections is a dict of python objects, a key in this dict is
        the name of the section and the value is a dict that can be
        used to create a whole survey.
        """
        assert type(sections)==dict
        self._sections = sections

    def set_question_type_dictionary(self, question_type_dictionary):
        if type(question_type_dictionary)==QuestionTypeDictionary:
            self._question_type_dictionary = question_type_dictionary
        else:
            self._question_type_dictionary = DEFAULT_QUESTION_TYPE_DICTIONARY

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
        # todo: clean up this spaghetti code
        d_copy[u"question_type_dictionary"] = self._question_type_dictionary
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

    def _create_specify_other_question_from_dict(self, d):
        kwargs = {
            Question.TYPE : u"text",
            Question.NAME : u"%s_other" % d[Question.NAME],
            Question.LABEL : u"Specify other.",
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
            section_name = d[SurveyElement.NAME]
            if section_name not in self._sections:
                raise Exception("This section has not been included.",
                                section_name, self._sections.keys())
            d = self._sections[section_name]
            full_survey = self.create_survey_element_from_dict(d)
            return full_survey.get_children()
        else:
            return self._create_question_from_dict(d)

    def create_survey_element_from_json(self, str_or_path):
        d = utils.get_pyobj_from_json(str_or_path)
        return self.create_survey_element_from_dict(d)


def create_survey_element_from_dict(d, sections={}):
    builder = SurveyElementBuilder()
    builder.set_sections(sections)
    return builder.create_survey_element_from_dict(d)

def create_survey_element_from_json(str_or_path):
    d = utils.get_pyobj_from_json(str_or_path)
    return create_survey_element_from_dict(d)

def create_survey_from_xls(path):
    excel_reader = SurveyReader(path)
    d = excel_reader.to_dict()
    return create_survey_element_from_dict(d)

def render_survey_package(survey_package):
    children = survey_package.get(u'survey', [])
    name = unicode(survey_package.get(u'name'))
    id_string = survey_package.get(u'id_string')
    #question_types don't work yet
    question_types = survey_package.get(u'question_types')
    survey = Survey(id_string=id_string, name=name)
    builder = SurveyElementBuilder()
    for child in children:
        survey.add_child(create_survey_element_from_dict(child))
    return survey

def create_survey(name, main_section, sections={},
    id_string=None, question_type_dictionary=None
    ):
    builder = SurveyElementBuilder()
    builder.set_sections(sections)
    builder.set_question_type_dictionary(question_type_dictionary)
    survey = builder.create_survey_element_from_dict({
        'type': 'survey',
        'children': main_section,
        'name': unicode(name)
    })
    survey.set_id_string(id_string)
    return survey

def section_name(path_or_file_name):
    directory, filename = os.path.split(path_or_file_name)
    section_name, extension = os.path.splitext(filename)
    return section_name

def create_survey_from_path(path):
    directory, file_name = os.path.split(path)
    sections = {}
    xls_files = glob.glob(os.path.join(directory, "*.xls"))
    for xls_file_path in xls_files:
        name = section_name(xls_file_path)
        excel_reader = SurveyReader(xls_file_path)
        sections[name] = excel_reader.to_dict()
    json_files = glob.glob(os.path.join(directory, "*.json"))
    for json_file_path in json_files:
        name = section_name(json_file_path)
        sections[name] = utils.get_pyobj_from_json(json_file_path)
    kwargs = {
        "name_of_main_section" : section_name(file_name),
        "sections" : sections,
        }
    return create_survey(**kwargs)

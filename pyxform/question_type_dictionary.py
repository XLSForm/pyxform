from xls2json import QuestionTypesReader
import os


class QuestionTypeDictionary(dict):
    """
    A dictionary parsed from an xls file that defines question types.
    """
    def __init__(self, file_name="base"):
        # Right now we're using an excel file to describe question
        # types we will use in creating XForms, we'll switch over to
        # json soon.
        self._name = file_name
        path_to_this_file = os.path.abspath(__file__)
        path_to_this_dir = os.path.dirname(path_to_this_file)
        path_to_question_types = os.path.join(
            path_to_this_dir,
            "question_types",
            "%s.xls" % file_name
            )
        excel_reader = QuestionTypesReader(path_to_question_types)
        for k, v in excel_reader.to_json_dict().iteritems():
            self[k] = v

    def get_definition(self, question_type_str):
        return self.get(question_type_str, {})

DEFAULT_QUESTION_TYPE_DICTIONARY = QuestionTypeDictionary("all")
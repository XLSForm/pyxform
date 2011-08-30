import os

def path_to_text_fixture(filename):
    directory = os.path.dirname(__file__)
    return os.path.join(directory, "example_xls", filename)


from pyxform.builder import create_survey_from_path
from pyxform import file_utils
from pyxform.xls2json import SurveyReader

def create_survey_from_fixture(fixture_name, filetype="xls"):
    if filetype == "xls":
        fixture_path = path_to_text_fixture("%s.xls" % fixture_name)
        return create_survey_from_path(fixture_path)
    elif filetype == "csv":
        fixture_path = path_to_text_fixture(fixture_name)
        return create_survey_from_path(fixture_path)

import os

def path_to_text_fixture(filename):
    directory = os.path.dirname(__file__)
    return os.path.join(directory, "example_xls", filename)


from pyxform.builder import create_survey
from pyxform import file_utils

def create_survey_from_fixture(fixture_name, filetype="xls"):
    if filetype == "xls":
        fixture_path = path_to_text_fixture("%s.xls" % fixture_name)
        survey_dict = file_utils.load_xls_to_pkg_dict(fixture_path)
        return create_survey(**survey_dict)
    elif filetype == "csv":
        # fixture_path does not include the full file name
        fixture_path = path_to_text_fixture(fixture_name)
        survey_dict = file_utils.load_csv_to_dict(fixture_path)
        return create_survey(**survey_dict)

# def absolute_path(f, file_name):
#     directory = os.path.dirname(f)
#     return os.path.join(directory, file_name)

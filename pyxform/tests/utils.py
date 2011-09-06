import os

def path_to_text_fixture(filename):
    directory = os.path.dirname(__file__)
    return os.path.join(directory, "example_xls", filename)


from pyxform.builder import create_survey_from_path
from pyxform.xls2json import SurveyReader
from pyxform import file_utils
from pyxform.builder import create_survey

def create_survey_from_fixture(fixture_name, filetype="xls", include_directory=False):
    fixture_path = path_to_text_fixture("%s.%s" % (fixture_name, filetype))
    noop, section_dict = file_utils.load_file_to_dict(fixture_path)
    pkg = { u'title': fixture_name,
             u'main_section': section_dict }
    if include_directory:
        directory, noop = os.path.split(fixture_path)
        pkg[u'sections'] = file_utils.collect_compatible_files_in_directory(directory)
    return create_survey(**pkg)
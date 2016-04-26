import os
from pyxform import file_utils
from pyxform.builder import create_survey, create_survey_from_path

def path_to_text_fixture(filename):
    directory = os.path.dirname(__file__)
    return os.path.join(directory, "example_xls", filename)


def build_survey(filename):
    path = path_to_text_fixture(filename)
    return create_survey_from_path(path)


def create_survey_from_fixture(fixture_name, filetype="xls", include_directory=False):
    fixture_path = path_to_text_fixture("%s.%s" % (fixture_name, filetype))
    noop, section_dict = file_utils.load_file_to_dict(fixture_path)
    pkg = {u'main_section': section_dict}
    if include_directory:
        directory, noop = os.path.split(fixture_path)
        pkg[u'sections'] = file_utils.collect_compatible_files_in_directory(directory)
    return create_survey(**pkg)

import os

def path_to_text_fixture(filename):
    directory = os.path.dirname(__file__)
    return os.path.join(directory, "example_xls", filename)


from pyxform.builder import create_survey
from pyxform import file_utils

def create_survey_from_fixture(fixture_name, filetype="xls", include_directory=False):
    # I think we're approaching a clean way to do this...
    fixture_path = path_to_text_fixture("%s.%s" % (fixture_name, filetype))
    if not include_directory:
        name, section_dict = file_utils.load_file_to_dict(fixture_path)
        return create_survey(**{
            u'title': name,
            u'name_of_main_section': name,
            u'sections': {
                name: section_dict
                }
            })
    else:
        directory, file_name = os.path.split(fixture_path)
        sections = file_utils.collect_compatible_files_in_directory(directory)
        return create_survey(**{
            u'title': fixture_name,
            u'name_of_main_section': fixture_name,
            u'sections': sections
        })

# def absolute_path(f, file_name):
#     directory = os.path.dirname(f)
#     return os.path.join(directory, file_name)

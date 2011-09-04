import os
import glob
from xls2json import SurveyReader
import utils

def _section_name(path_or_file_name):
    directory, filename = os.path.split(path_or_file_name)
    _section_name, extension = os.path.splitext(filename)
    return _section_name

def load_file_to_dict(path):
    if path.endswith(".xls"):
        name = _section_name(path)
        excel_reader = SurveyReader(path)
        return (name, excel_reader.to_dict())
    elif path.endswith(".json"):
        name = _section_name(path)
        return (name, utils.get_pyobj_from_json(path))

def load_xls_to_pkg_dict(path, include_directory=True):
    if not include_directory:
        main_section_name, section = load_file_to_dict(path)
        sections = {main_section_name: section}
    else:
        directory, file_name = os.path.split(path)
        main_section_name = _section_name(file_name)
        sections = collect_compatible_files_in_directory(directory)
    return {
        "title": main_section_name,
        "name_of_main_section": main_section_name,
        "sections": sections,
        }

def collect_compatible_files_in_directory(directory):
    sections = {}
    available_files = glob.glob(os.path.join(directory, "*.xls")) + \
                        glob.glob(os.path.join(directory, "*.json"))
    return dict([load_file_to_dict(f) for f in available_files])

def load_csv_to_dict(path):
    # Note, this does not include sections
    section_path = _section_name(path)
    # sections = {
    #     section_path: SurveyReader(path, filetype="csv").to_dict()
    # }
    # return {
    #     "title": section_path,
    #     "name_of_main_section": section_path,
    #     "sections": sections,
    #     }

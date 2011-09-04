import os
import glob
from xls2json import SurveyReader
import utils

def _section_name(path_or_file_name):
    directory, filename = os.path.split(path_or_file_name)
    _section_name, extension = os.path.splitext(filename)
    return _section_name

def load_xls_to_dict(path, include_directory=True):
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
    xls_files = glob.glob(os.path.join(directory, "*.xls"))
    for xls_file_path in xls_files:
        name = _section_name(xls_file_path)
        excel_reader = SurveyReader(xls_file_path)
        sections[name] = excel_reader.to_dict()
    json_files = glob.glob(os.path.join(directory, "*.json"))
    for json_file_path in json_files:
        name = _section_name(json_file_path)
        sections[name] = utils.get_pyobj_from_json(json_file_path)
    return sections

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

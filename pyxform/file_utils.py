import os
import glob
from xls2json import SurveyReader
import utils

def load_xls_to_dict(path):
    def section_name(path_or_file_name):
        directory, filename = os.path.split(path_or_file_name)
        section_name, extension = os.path.splitext(filename)
        return section_name
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
    return {
        "title": section_name(file_name),
        "name_of_main_section": section_name(file_name),
        "sections": sections,
        }
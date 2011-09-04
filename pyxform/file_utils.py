import os
import glob
import utils

from xls2json import SurveyReader

def _section_name(path_or_file_name):
    directory, filename = os.path.split(path_or_file_name)
    section_name, extension = os.path.splitext(filename)
    return section_name

def load_file_to_dict(path):
    if path.endswith(".xls") or path.endswith(".csv"):
        name = _section_name(path)
        excel_reader = SurveyReader(path)
        return (name, excel_reader.to_dict())
    elif path.endswith(".json"):
        name = _section_name(path)
        return (name, utils.get_pyobj_from_json(path))

def collect_compatible_files_in_directory(directory):
    sections = {}
    available_files = glob.glob(os.path.join(directory, "*.xls")) + \
                        glob.glob(os.path.join(directory, "*.json"))
    return dict([load_file_to_dict(f) for f in available_files])

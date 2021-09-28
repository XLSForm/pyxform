# -*- coding: utf-8 -*-
"""
The tests utils module functionality.
"""
import configparser
import os
import textwrap
from typing import TYPE_CHECKING
from pyxform import file_utils
from pyxform.builder import create_survey, create_survey_from_path
from tests import example_xls


if TYPE_CHECKING:
    from typing import Tuple


def path_to_text_fixture(filename):
    return os.path.join(example_xls.PATH, filename)


def build_survey(filename):
    path = path_to_text_fixture(filename)
    return create_survey_from_path(path)


def create_survey_from_fixture(fixture_name, filetype="xls", include_directory=False):
    fixture_path = path_to_text_fixture("%s.%s" % (fixture_name, filetype))
    noop, section_dict = file_utils.load_file_to_dict(fixture_path)
    pkg = {"main_section": section_dict}
    if include_directory:
        directory, noop = os.path.split(fixture_path)
        pkg["sections"] = file_utils.collect_compatible_files_in_directory(directory)
    return create_survey(**pkg)


def prep_class_config(cls, test_dir="tests"):
    cls.config = configparser.ConfigParser()
    here = os.path.dirname(__file__)
    root = os.path.dirname(here)
    strings = os.path.join(root, test_dir, "fixtures", "strings.ini")
    cls.config.read(strings)
    cls.cls_name = cls.__name__


def prep_for_xml_contains(text: str) -> "Tuple[str]":
    """Prep string for finding an exact match to formatted XML text."""
    # noinspection PyRedundantParentheses
    return (textwrap.indent(textwrap.dedent(text), "    "),)

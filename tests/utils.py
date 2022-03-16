# -*- coding: utf-8 -*-
"""
The tests utils module functionality.
"""
import configparser
import os
import shutil
import tempfile
import textwrap
from contextlib import contextmanager
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


@contextmanager
def get_temp_file():
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    try:
        yield temp_file.name
    finally:
        temp_file.close()
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)


@contextmanager
def get_temp_dir():
    temp_dir_prefix = "pyxform_tmp_"
    if os.name == "nt":
        cleanup_pyxform_temp_files(prefix=temp_dir_prefix)

    temp_dir = tempfile.mkdtemp(prefix=temp_dir_prefix)
    try:
        yield temp_dir
    finally:
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except PermissionError:
            truncate_temp_files(temp_dir=temp_dir)


def truncate_temp_files(temp_dir):
    """
    Truncate files in a folder, recursing into directories.
    """
    # If we can't delete, at least the files can be truncated,
    # so that they don't take up disk space until next cleanup.
    # Seems to be a Windows-specific error for newly-created files.
    temp_root = tempfile.gettempdir()
    if os.path.exists(temp_dir):
        for f in os.scandir(temp_dir):
            if os.path.isdir(f.path):
                truncate_temp_files(f.path)
            else:
                # Check still in temp directory
                if f.path.startswith(temp_root):
                    with open(f.path, mode="w") as _:
                        pass


def cleanup_pyxform_temp_files(prefix: str):
    """
    Try to clean up temp pyxform files from previous test runs.
    """
    temp_root = tempfile.gettempdir()
    if os.path.exists(temp_root):
        for f in os.scandir(temp_root):
            if os.path.isdir(f.path):
                if f.name.startswith(prefix) and f.path.startswith(temp_root):
                    try:
                        shutil.rmtree(f.path)
                    except PermissionError:
                        pass

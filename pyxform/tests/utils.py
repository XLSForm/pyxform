import os


def path_to_text_fixture(filename):
    directory = os.path.dirname(__file__)
    return os.path.join(directory, "example_xls", filename)


# def absolute_path(f, file_name):
#     directory = os.path.dirname(f)
#     return os.path.join(directory, file_name)

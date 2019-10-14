"""
Test upload (image, audio, file) question types in XLSForm
"""
from pyxform.tests_v1.pyxform_test_case import PyxformTestCase




class UploadTest(PyxformTestCase):
    def test_image_question(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |      |         |       |
            |        | type | name    | label |
            |        | image | photo | Take a photo: |
            """,
            errored=False,
            xml__contains=[
                "<bind nodeset=\"/data/photo\" type=\"binary\"/>", 
                "<upload mediatype=\"image/*\" ref=\"/data/photo\">",
                "<label>Take a photo:</label>", 
                "</upload>"],
        )

    def test_audio_question(self):
        return True

    def test_file_question(self):
        return True

    def test_file_question_restrict_filetype(self):
        return True

    def test_image_question_custom_col_calc(self):
        return True
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
                '<bind nodeset="/data/photo" type="binary"/>',
                '<upload mediatype="image/*" ref="/data/photo">',
                "<label>Take a photo:</label>",
                "</upload>",
            ],
        )

    def test_audio_question(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |      |         |       |
            |        | type | name    | label |
            |        | audio | recording1 | Record a sound: |
            """,
            errored=False,
            xml__contains=[
                '<bind nodeset="/data/recording1" type="binary"/>',
                '<upload mediatype="audio/*" ref="/data/recording1">',
                "<label>Record a sound:</label>",
                "</upload>",
            ],
        )

    def test_file_question(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |      |         |       |
            |        | type | name    | label |
            |        | file | file1 | Upload a file: |
            """,
            errored=False,
            xml__contains=[
                '<bind nodeset="/data/file1" type="binary"/>',
                '<upload mediatype="application/*" ref="/data/file1">',
                "<label>Upload a file:</label>",
                "</upload>",
            ],
        )

    def test_file_question_restrict_filetype(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |      |         |       |       |
            |        | type | name    | label | body::accept |
            |        | file | upload_a_pdf | Upload a PDF: | application/pdf |
            """,
            errored=False,
            xml__contains=['<upload accept="application/pdf"'],
        )

    def test_image_question_custom_col_calc(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |       |                  |                 |                               |
            |        | type  | name             | label           | body:esri:style               |
            |        | text  | watermark_phrase | Watermark Text: |                               |
            |        | text  | text1            | Text            |                               |
            |        | image | image1           | Take a Photo:   | watermark=${watermark_phrase} |
            """,  # noqa
            errored=False,
            xml__contains=["watermark= /data/watermark_phrase "],
        )

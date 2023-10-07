# -*- coding: utf-8 -*-
"""
Test image max-pixels and app parameters.
"""
from tests.pyxform_test_case import PyxformTestCase


class TestImageAppParameter(PyxformTestCase):
    def test_adding_valid_android_package_name_in_image_with_supported_appearances(self):
        appearances = ("", "annotate")
        md = """
        | survey |        |          |       |                                     |            |
        |        | type   | name     | label | parameters                          | appearance |
        |        | image  | my_image | Image | app=com.jeyluta.timestampcamerafree | {case}     |
        """
        for case in appearances:
            with self.subTest(msg=case):
                self.assertPyxformXform(
                    name="data",
                    md=md.format(case=case),
                    xml__xpath_match=[
                        "/h:html/h:body/x:upload[@intent='com.jeyluta.timestampcamerafree' and @mediatype='image/*' and @ref='/data/my_image']"
                    ],
                )

    def test_throwing_error_when_invalid_android_package_name_is_used_with_supported_appearances(
        self,
    ):
        appearances = ("", "annotate")
        md = """
        | survey |        |          |       |                 |            |
        |        | type   | name     | label | parameters      | appearance |
        |        | image  | my_image | Image | app=something   | {case}     |
        """
        for case in appearances:
            with self.subTest(msg=case):
                self.assertPyxformXform(
                    name="data",
                    errored=True,
                    error__contains="[row : 2] Invalid Android package name - the package name must have at least one '.' separator.",
                    md=md.format(case=case),
                    xml__xpath_match=[
                        "/h:html/h:body/x:upload[not(@intent) and @mediatype='image/*' and @ref='/data/my_image']"
                    ],
                )

    def test_ignoring_invalid_android_package_name_is_used_with_not_supported_appearances(
        self,
    ):
        appearances = ("signature", "draw", "new-front")
        md = """
        | survey |        |          |       |                 |            |
        |        | type   | name     | label | parameters      | appearance |
        |        | image  | my_image | Image | app=something   | {case}     |
        """
        for case in appearances:
            with self.subTest(msg=case):
                self.assertPyxformXform(
                    name="data",
                    md=md.format(case=case),
                    xml__xpath_match=[
                        "/h:html/h:body/x:upload[not(@intent) and @mediatype='image/*' and @ref='/data/my_image']"
                    ],
                )

    def test_ignoring_android_package_name_in_image_with_not_supported_appearances(self):
        appearances = ("signature", "draw", "new-front")
        md = """
        | survey |        |          |       |                                     |            |
        |        | type   | name     | label | parameters                          | appearance |
        |        | image  | my_image | Image | app=com.jeyluta.timestampcamerafree | {case}     |
        """
        for case in appearances:
            with self.subTest(msg=case):
                self.assertPyxformXform(
                    name="data",
                    md=md.format(case=case),
                    xml__xpath_match=[
                        "/h:html/h:body/x:upload[not(@intent) and @mediatype='image/*' and @ref='/data/my_image']"
                    ],
                )

    def test_integer_max_pixels(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |                |
            |        | type   | name     | label | parameters     |
            |        | image  | my_image | Image | max-pixels=640 |
            """,
            xml__contains=[
                'xmlns:orx="http://openrosa.org/xforms"',
                '<bind nodeset="/data/my_image" type="binary" orx:max-pixels="640"/>',
            ],
        )

    def test_string_max_pixels(self):
        self.assertPyxformXform(
            name="data",
            errored=True,
            md="""
            | survey |        |          |       |                |
            |        | type   | name     | label | parameters     |
            |        | image  | my_image | Image | max-pixels=foo |
            """,
            error__contains=["Parameter max-pixels must have an integer value."],
        )

    def test_string_extra_params(self):
        self.assertPyxformXform(
            name="data",
            errored=True,
            md="""
            | survey |        |          |       |                        |
            |        | type   | name     | label | parameters             |
            |        | image  | my_image | Image | max-pixels=640 foo=bar |
            """,
            error__contains=[
                "Accepted parameters are 'app, max-pixels'. The following are invalid parameter(s): 'foo'."
            ],
        )

    def test_image_with_no_max_pixels_should_warn(self):
        warnings = []

        self.md_to_pyxform_survey(
            """
            | survey |       |            |         |
            |        | type  | name    | label   |
            |        | image | my_image   | Image   |
            |        | image | my_image_1 | Image 1 |
            """,
            warnings=warnings,
        )

        self.assertTrue(len(warnings) == 2)
        self.assertTrue("max-pixels" in warnings[0] and "max-pixels" in warnings[1])

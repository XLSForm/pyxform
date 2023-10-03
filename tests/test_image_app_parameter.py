# -*- coding: utf-8 -*-
"""
Test image app parameter.
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

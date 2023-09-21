# -*- coding: utf-8 -*-
"""
Test image app parameter.
"""
from tests.pyxform_test_case import PyxformTestCase


class ImageAppParameterTest(PyxformTestCase):
    def test_valid_android_package_name(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |                                     |
            |        | type   | name     | label | parameters                          |
            |        | image  | my_image | Image | app=com.jeyluta.timestampcamerafree |
            """,
            xml__xpath_match=[
                "/h:html/h:body/x:upload[@intent='com.jeyluta.timestampcamerafree' and @mediatype='image/*' and @ref='/data/my_image']"
            ],
        )

    def test_invalid_android_package_name(self):
        self.assertPyxformXform(
            name="data",
            errored=True,
            md="""
            | survey |        |          |       |               |
            |        | type   | name     | label | parameters    |
            |        | image  | my_image | Image | app=something |
            """,
            error__contains=["Invalid Android package name format"],
        )

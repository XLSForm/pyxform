"""
Test image max-pixels and app parameters.
"""

from tests.pyxform_test_case import PyxformTestCase


class TestImageParameters(PyxformTestCase):
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
        parameters = ("app=something", "app=_")
        md = """
           | survey |        |          |       |              |              |
           |        | type   | name     | label | parameters   | appearance   |
           |        | image  | my_image | Image | {parameter}  | {appearance} |
           """
        for appearance in appearances:
            for parameter in parameters:
                with self.subTest(msg=f"{appearance} - {parameter}"):
                    self.assertPyxformXform(
                        name="data",
                        errored=True,
                        error__contains=[
                            "[row : 2] Parameter 'app' has an invalid Android package name - the package name must have at least one '.' separator."
                        ],
                        md=md.format(parameter=parameter, appearance=appearance),
                        xml__xpath_match=[
                            "/h:html/h:body/x:upload[not(@intent) and @mediatype='image/*' and @ref='/data/my_image']"
                        ],
                    )

    def test_throwing_error_when_blank_android_package_name_is_used_with_supported_appearances(
        self,
    ):
        appearances = ("", "annotate")
        parameters = ("app=", "app= ")
        md = """
           | survey |        |          |       |              |              |
           |        | type   | name     | label | parameters   | appearance   |
           |        | image  | my_image | Image | {parameter}  | {appearance} |
           """
        for appearance in appearances:
            for parameter in parameters:
                with self.subTest(msg=f"{appearance} - {parameter}"):
                    self.assertPyxformXform(
                        name="data",
                        errored=True,
                        error__contains=[
                            "[row : 2] Parameter 'app' has an invalid Android package name - package name is missing."
                        ],
                        md=md.format(parameter=parameter, appearance=appearance),
                        xml__xpath_match=[
                            "/h:html/h:body/x:upload[not(@intent) and @mediatype='image/*' and @ref='/data/my_image']"
                        ],
                    )

    def test_ignoring_invalid_android_package_name_with_not_supported_appearances(
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
        self.assertPyxformXform(
            md="""
            | survey |       |            |         |
            |        | type  | name    | label   |
            |        | image | my_image   | Image   |
            |        | image | my_image_1 | Image 1 |
            """,
            warnings_count=2,
            warnings__contains=[
                "[row : 2] Use the max-pixels parameter to speed up submission sending and save storage space. Learn more: https://xlsform.org/#image",
                "[row : 3] Use the max-pixels parameter to speed up submission sending and save storage space. Learn more: https://xlsform.org/#image",
            ],
        )

    def test_max_pixels_and_app(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |                                                    |
            |        | type   | name     | label | parameters                                         |
            |        | image  | my_image | Image | max-pixels=640 app=com.jeyluta.timestampcamerafree |
            """,
            xml__contains=[
                'xmlns:orx="http://openrosa.org/xforms"',
                '<bind nodeset="/data/my_image" type="binary" orx:max-pixels="640"/>',
            ],
            xml__xpath_match=[
                "/h:html/h:body/x:upload[@intent='com.jeyluta.timestampcamerafree' and @mediatype='image/*' and @ref='/data/my_image']"
            ],
        )

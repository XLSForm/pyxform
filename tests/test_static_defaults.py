from tests.pyxform_test_case import PyxformTestCase

class StaticDefaultTests(PyxformTestCase):
    def test_static_defaults(self):
        self.assertPyxformXform(
            name="static",
            md="""
            | survey |              |          |       |                   |
            |        | type         | name     | label | default           |
            |        | integer      | numba    | Foo   | foo               |
            |        | begin repeat | repeat   |       |                   |
            |        | integer      | bar      | Bar   | 12                |
            |        | end repeat   | repeat   |       |                   |
            """,
            model__contains=["<numba>foo</numba>", "<bar>12</bar>"],
            model__excludes=["setvalue", "<numba />"],
        )

    def test_static_image_defaults(self):
        self.assertPyxformXform(
            name="static_image",
            md="""
            | survey |        |          |       |                |                        |
            |        | type   | name     | label | parameters     | default                |
            |        | image  | my_image | Image | max-pixels=640 | my_default_image.jpg   |
            |        | text   | my_descr | descr |                | no description provied |
            """,
            model__contains=[
                # image needed NS and question typing still exist!
                'xmlns:orx="http://openrosa.org/xforms"',
                '<bind nodeset="/static_image/my_image" type="binary" orx:max-pixels="640"/>',
                # image default appears
                "<my_image>jr://images/my_default_image.jpg</my_image>",
                # other defaults appear
                "<my_descr>no description provied</my_descr>",
            ],
            model__excludes=[
                "setvalue",
                "<my_image></my_image>",
                "<my_descr></my_descr>",
            ],
        )

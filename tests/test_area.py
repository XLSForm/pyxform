"""
AreaTest - test enclosed-area(geo_shape) calculation.
"""
from tests.pyxform_test_case import PyxformTestCase


class AreaTest(PyxformTestCase):
    """
    AreaTest - test enclosed-area(geo_shape) calculation.
    """

    def test_area(self):
        d = (
            "38.253094215699576 21.756382658677467;38.25021274773806 21.756382658677467;"
            "38.25007793942195 21.763892843919166;38.25290886154963 21.763935759263404;"
            "38.25146813817506 21.758421137528785"
        )
        self.assertPyxformXform(
            name="area",
            md=f"""
            | survey |           |           |               |                               |         |
            |        | type      | name      | label         | calculation                   | default |
            |        | geoshape  | geoshape1 | Draw shape... |                               | {d}     |
            |        | calculate | result    |               | enclosed-area(${{geoshape1}}) |         |
            """,
            xml__xpath_match=[
                "/h:html/h:head/x:model/x:bind[@calculate='enclosed-area( /area/geoshape1 )' "
                + "  and @nodeset='/area/result' and @type='string']",
                "/h:html/h:head/x:model/x:instance/x:area[x:geoshape1]",
            ],
        )

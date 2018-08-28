from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class TestLoop(PyxformTestCase):
    def test_loop(self):
        self.assertPyxformXform(
            name="test_loop",
            md="""
                | survey |              |           |                |        |
                |        |     type     |    name   | bind:relevant  | label  |
                |        | begin repeat | for-block |                | Oh HAI |
                |        | string       | input     | (${done}='no') | HI HI  |
                |        | string       | done      |                | DONE?  |
                |        | end repeat   |           |                |        |
                """,
            instance__contains=[
                '<for-block jr:template="">',
                '</for-block>',
                ],
            model__contains=[
                """<bind nodeset="/test_loop/for-block/input" """
                """relevant="( ../done ='no')" """
                """type="string"/>"""
                ],
            xml__contains=[
                '<group ref="/test_loop/for-block">',
                '<label>Oh HAI</label>',
                '</group>',
            ],
        )

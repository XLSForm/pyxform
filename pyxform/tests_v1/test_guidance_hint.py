from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class GuidanceHintTest(PyxformTestCase):
    def test_single_language_guidance(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |           |                              |
            |        | type   |   name   | label | hint      | guidance_hint                |
            |        | string |   name   | Name  | your name | as shown on birth certificate|
            """,
            xml__contains=[
                '<hint>your name</hint>',
                '<hint form="guidance">as shown on birth certificate</hint>'],
        )

    def test_multi_language_guidance(self):
        self.assertPyxformXform(
            name="data",
            md="""
            | survey |        |          |       |           |                              |                                     |
            |        | type   |   name   | label | hint      | guidance_hint::English (en)  | guidance_hint::French (fr)          |
            |        | string |   name   | Name  | your name | as shown on birth certificate| comme sur le certificat de naissance|
            """,
            xml__contains=[
                '<translation lang="French (fr)">',
                '<value>comme sur le certificat de naissance</value>',
                '<translation lang="English (en)">',
                '<value>as shown on birth certificate</value>',
                '<guidance_hint form=\"guidance\" ref=\"jr:itext(\'/data/name:guidance_hint\')\"/>'],
        )

    def test_guidance_hint_only(self):
        self.assertPyxformXform(
            name="data",
            errored=True,
            md="""
            | survey |        |          |                              |
            |        | type   |   name   | guidance_hint                |
            |        | string |   name   | as shown on birth certificate|
            """,
            error__contains=[
                'The survey element named \'name\' has no label or hint.'],
        )
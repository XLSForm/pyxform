from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class AuditTest(PyxformTestCase):
    def test_audit(self):
        self.assertPyxformXform(
            name="meta_audit",
            md="""
            | survey |        |          |       |                     |
            |        | type   |   name   | label | parameters          |
            |        | audit  |   audit  |       |                     |
            """,
            xml__contains=[
                '<meta>',
                '<audit/>',
                '</meta>', 
                '<bind nodeset="/meta_audit/meta/audit" type="binary"/>'],
        )
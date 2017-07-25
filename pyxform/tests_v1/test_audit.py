from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class AuditTest(PyxformTestCase):
    def test_audit(self):
        self.assertPyxformXform(
            name="meta_audit",
            md="""
            | survey |        |          |       |
            |        | type   |   name   | label |
            |        | audit  |   audit  |       |
            """,
            xml__contains=[
                '<meta>',
                '<audit/>',
                '</meta>',
                '<bind nodeset="/meta_audit/meta/audit" type="binary"/>'],
        )

    def test_audit_random_name(self):
        self.assertPyxformXform(
            name="meta_audit",
            md="""
            | survey |        |          |       |
            |        | type   |   name   | label |
            |        | audit  |   bobby  |       |
            """,
            errored=True,
            error__contains=['Audits must always be named \'audit.\''],
        )

    def test_audit_blank_name(self):
        self.assertPyxformXform(
            name="meta_audit",
            md="""
            | survey |        |          |       |
            |        | type   |   name   | label |
            |        | audit  |          |       |
            """,
            xml__contains=[
                '<meta>',
                '<audit/>',
                '</meta>',
                '<bind nodeset="/meta_audit/meta/audit" type="binary"/>'],
        )
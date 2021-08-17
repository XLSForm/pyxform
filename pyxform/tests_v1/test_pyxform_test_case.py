from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class TestPyxformTestCaseXmlXpath(PyxformTestCase):
    md = """
    | survey |        |         |                |                                                         |
    |        | type   | name    | label          | required                                                |
    |        | text   | Part_ID | Participant ID | pulldata('ID', 'ParticipantID', 'ParticipantIDValue',.) |
    """

    def test_xml__xpath_exact__singular(self):
        """Should find exact results when single node returned by XPath."""
        node = """<instance id="ID" src="jr://file-csv/ID.csv"/>"""
        self.assertPyxformXform(
            md=self.md,
            xml__xpath_exact=[(".//instance[@id='ID']", [node])],
            run_odk_validate=False,
        )
        with self.assertRaises(self.failureException):
            self.assertPyxformXform(
                md=self.md,
                xml__xpath_exact=[(".//instance[@id='ID']", ["bananas"])],
                run_odk_validate=False,
            )

    def test_xml__xpath_count__singular(self):
        """Should find expected count when single node returned by XPath."""
        self.assertPyxformXform(
            md=self.md,
            xml__xpath_count=[(".//instance[@id='ID']", 1)],
            run_odk_validate=False,
        )
        with self.assertRaises(self.failureException):
            self.assertPyxformXform(
                md=self.md,
                xml__xpath_count=[(".//instance[@id='ID']", 2)],
                run_odk_validate=False,
            )

    def test_xml__xpath_exact__multiple(self):
        """Should find exact results when multiple nodes returned by XPath."""
        node1 = (
            """<bind nodeset="/pyxform_autotestname/Part_ID" """
            """required="pulldata('ID', 'ParticipantID', 'ParticipantIDValue',.)" """
            """type="string"/>"""
        )
        # The "jr" usage here implicitly tests namespace handling.
        node2 = (
            """<bind jr:preload="uid" nodeset="/pyxform_autotestname/meta/instanceID" """
            """readonly="true()" type="string"/>"""
        )
        self.assertPyxformXform(
            md=self.md,
            xml__xpath_exact=[(".//bind", [node1, node2])],
            run_odk_validate=False,
        )
        with self.assertRaises(self.failureException):
            self.assertPyxformXform(
                md=self.md,
                xml__xpath_exact=[(".//bind", [node2, node1])],
                run_odk_validate=False,
            )

    def test_xml__xpath_count__multiple(self):
        """Should find expected count when multiple nodes returned by XPath."""
        self.assertPyxformXform(
            md=self.md, xml__xpath_count=[(".//bind", 2)], run_odk_validate=False,
        )
        with self.assertRaises(self.failureException):
            self.assertPyxformXform(
                md=self.md, xml__xpath_count=[(".//bind", 1)], run_odk_validate=False,
            )

    def test_xml__xpath_exact__singular_nested(self):
        """Should find exact results when single node returned by XPath."""
        node = (
            """<h:body>\n"""
            """    <input ref="/pyxform_autotestname/Part_ID">\n"""
            """      <label>Participant ID</label>\n"""
            """    </input>\n"""
            """  </h:body>"""
        )
        self.assertPyxformXform(
            md=self.md,
            xml__xpath_exact=[(".//h:body", [node])],
            run_odk_validate=False,
        )

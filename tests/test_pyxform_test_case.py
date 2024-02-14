import unittest
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tests.pyxform_test_case import PyxformTestCase

if TYPE_CHECKING:
    from typing import Set


@dataclass
class CaseData:
    xpath: str
    exact: "Set[str]"
    count: int

    @property
    def ctuple(self):
        return (self.xpath, self.count)

    @property
    def etuple(self):
        return (self.xpath, self.exact)


class TestPyxformTestCaseXmlXpath(PyxformTestCase):
    # Test form used by the below cases.
    md = """
    | survey |        |         |                |                                                         |
    |        | type   | name    | label          | required                                                |
    |        | text   | Part_ID | Participant ID | pulldata('ID', 'ParticipantID', 'ParticipantIDValue',.) |
    |        | text   | Initial | Initials       |                                                         |
    """
    # Suite 1: one expected match result.
    # s1c1: element in default namespace.
    s1c1 = CaseData(
        xpath=".//x:instance[@id='ID']",
        exact={'<instance id="ID" src="jr://file-csv/ID.csv"/>'},
        count=1,
    )
    # s1c2: mix of namespaces
    s1c2 = CaseData(
        xpath=".//h:body/x:input[@ref='/test_name/Part_ID']/x:label",
        exact={"<label>Participant ID</label>"},
        count=1,
    )
    # s1c3: multi-element match result.
    s1c3 = CaseData(
        xpath=".//h:body",
        exact={
            (
                """<h:body>\n"""
                """    <input ref="/test_name/Part_ID">\n"""
                """      <label>Participant ID</label>\n"""
                """    </input>\n"""
                """    <input ref="/test_name/Initial">\n"""
                """      <label>Initials</label>\n"""
                """    </input>\n"""
                """  </h:body>"""
            )
        },
        count=1,
    )
    # s1c4: attribute selector with compound expression (not available in elementree).
    s1c4 = CaseData(
        xpath=".//x:bind[@type='string' and @jr:preload='uid']",
        exact={
            (
                """<bind nodeset="/test_name/meta/instanceID" """
                """readonly="true()" type="string" jr:preload="uid"/>"""
            )
        },
        count=1,
    )
    # s1c5: namespaced attribute selector.
    s1c5 = CaseData(
        xpath=".//x:bind[@type='string' and @jr:preload='uid']/@nodeset",
        exact={"/test_name/meta/instanceID"},
        count=1,
    )
    # Convenience combinations of the above data for Suite 1 tests.
    suite1 = (s1c1, s1c2, s1c3, s1c4, s1c5)
    suite1_counts = tuple(c.ctuple for c in suite1)
    suite1_exacts = tuple(c.etuple for c in suite1)
    suite1_xpaths = tuple(c.xpath for c in suite1)

    # Suite 2: multiple expected match results.
    # s2c1: element in default namespace.
    s2c1 = CaseData(
        xpath=".//x:bind",
        exact={
            (
                """<bind nodeset="/test_name/Part_ID" """
                """required="pulldata('ID', 'ParticipantID', 'ParticipantIDValue',.)" """
                """type="string"/>"""
            ),
            (
                """<bind nodeset="/test_name/meta/instanceID" """
                """readonly="true()" type="string" jr:preload="uid"/>"""
            ),
            ("""<bind nodeset="/test_name/Initial" type="string"/>"""),
        },
        count=3,
    )
    # s2c2: results with nesting and mix of namespaces.
    s2c2 = CaseData(
        xpath=".//x:instance",
        exact={
            (
                """<instance>\n"""
                """        <test_name id="test_id">\n"""
                """          <Part_ID/>\n"""
                """          <Initial/>\n"""
                """          <meta>\n"""
                """            <instanceID/>\n"""
                """          </meta>\n"""
                """        </test_name>\n"""
                """      </instance>"""
            ),
            ("""<instance id="ID" src="jr://file-csv/ID.csv"/>"""),
        },
        count=2,
    )
    # s2c3: nested element.
    s2c3 = CaseData(
        xpath=".//x:input/x:label",
        exact={
            ("""<label>Participant ID</label>"""),
            ("""<label>Initials</label>"""),
        },
        count=2,
    )
    # Convenience combinations of the above data for Suite 2 tests.
    suite2 = (s2c1, s2c2, s2c3)
    suite2_counts = tuple(c.ctuple for c in suite2)
    suite2_exacts = tuple(c.etuple for c in suite2)
    suite2_xpaths = tuple(c.xpath for c in suite2)

    # Suite 3: other misc cases.
    # s3c1: XPath with no expected matches.
    s3c1 = CaseData(xpath=".//x:unknown_element", exact=set(), count=0)

    def test_xml__1_xpath_1_match_pass__xpath_exact(self):
        """Should pass when exact match found for one XPath."""
        self.assertPyxformXform(
            md=self.md,
            xml__xpath_exact=[self.s1c1.etuple],
            run_odk_validate=False,
        )

    def test_xml__1_xpath_1_match_pass__xpath_count(self):
        """Should pass when count match found for one XPath."""
        self.assertPyxformXform(
            md=self.md,
            xml__xpath_count=[self.s1c1.ctuple],
            run_odk_validate=False,
        )

    def test_xml__1_xpath_1_match_pass__xpath_match(self):
        """Should pass for one XPath with single match."""
        self.assertPyxformXform(
            md=self.md,
            xml__xpath_match=[self.s1c1.xpath],
            run_odk_validate=False,
        )

    def test_xml__1_xpath_1_match_fail__xpath_exact(self):
        """Should fail when exact match not found for one XPath."""
        with self.assertRaises(self.failureException):
            self.assertPyxformXform(
                md=self.md,
                xml__xpath_exact=[(self.s1c1.xpath, {"bananas"})],
                run_odk_validate=False,
            )

    def test_xml__1_xpath_1_match_fail__xpath_count(self):
        """Should fail when count match not found for one XPath."""
        with self.assertRaises(self.failureException):
            self.assertPyxformXform(
                md=self.md,
                xml__xpath_count=[(self.s1c1.xpath, 5)],
                run_odk_validate=False,
            )

    def test_xml__1_xpath_0_match_fail__xpath_match(self):
        """Should fail when no match not found for one XPath."""
        with self.assertRaises(self.failureException):
            self.assertPyxformXform(
                md=self.md,
                xml__xpath_match=[self.s3c1.xpath],
                run_odk_validate=False,
            )

    def test_xml__n_xpath_1_match_pass__xpath_exact(self):
        """Should pass when exact match found for multiple XPaths."""
        self.assertPyxformXform(
            md=self.md,
            xml__xpath_exact=self.suite1_exacts,
            run_odk_validate=False,
        )

    def test_xml__n_xpath_1_match_pass__xpath_count(self):
        """Should pass when count match found for multiple XPaths."""
        self.assertPyxformXform(
            md=self.md,
            xml__xpath_count=self.suite1_counts,
            run_odk_validate=False,
        )

    def test_xml__n_xpath_1_match_pass__xpath_match(self):
        """Should pass for multiple XPaths with single match each."""
        self.assertPyxformXform(
            md=self.md,
            xml__xpath_match=self.suite1_xpaths,
            run_odk_validate=False,
        )

    def test_xml__n_xpath_1_match_fail__xpath_exact(self):
        """Should fail when exact match not found for one XPath, among other passes."""
        with self.assertRaises(self.failureException):
            self.assertPyxformXform(
                md=self.md,
                xml__xpath_exact=[*self.suite1_exacts, (self.s1c1.xpath, {"bananas"})],
                run_odk_validate=False,
            )

    def test_xml__n_xpath_1_match_fail__xpath_count(self):
        """Should fail when count match not found for one XPath, among other passes."""
        with self.assertRaises(self.failureException):
            self.assertPyxformXform(
                md=self.md,
                xml__xpath_count=[*self.suite1_counts, (self.s1c1.xpath, 5)],
                run_odk_validate=False,
            )

    def test_xml__n_xpath_1_match_fail__xpath_match(self):
        """Should fail when a match not found for one XPath, among other passes."""
        with self.assertRaises(self.failureException):
            self.assertPyxformXform(
                md=self.md,
                xml__xpath_match=[*self.suite1_xpaths, self.s3c1.xpath],
                run_odk_validate=False,
            )

    def test_xml__1_xpath_n_match_pass__xpath_exact(self):
        """Should pass when exact matches found for one XPath."""
        self.assertPyxformXform(
            md=self.md,
            xml__xpath_exact=[self.s2c3.etuple],
            run_odk_validate=False,
        )

    def test_xml__1_xpath_n_match_pass__xpath_count(self):
        """Should pass when count matches found for one XPath."""
        self.assertPyxformXform(
            md=self.md,
            xml__xpath_count=[self.s2c3.ctuple],
            run_odk_validate=False,
        )

    @unittest.skip("Scenario '1_xpath_n_match' NA for xpath_match: expects 1 match only.")
    def test_xml__1_xpath_n_match_pass__xpath_match(self):
        pass  # Test case included to document that there's no way to pass this scenario.

    def test_xml__1_xpath_n_match_fail__xpath_exact(self):
        """Should fail when exact matches not found for one XPath."""
        with self.assertRaises(self.failureException):
            self.assertPyxformXform(
                md=self.md,
                xml__xpath_exact=[(self.s2c3.xpath, {"bananas", "eggs"})],
                run_odk_validate=False,
            )

    def test_xml__1_xpath_n_match_fail__xpath_count(self):
        """Should fail when count matches not found for one XPath."""
        with self.assertRaises(self.failureException):
            self.assertPyxformXform(
                md=self.md,
                xml__xpath_count=[(self.s2c3.xpath, 5)],
                run_odk_validate=False,
            )

    def test_xml__1_xpath_n_match_fail__xpath_match(self):
        """Should fail for one XPath with multiple matches."""
        with self.assertRaises(self.failureException):
            self.assertPyxformXform(
                md=self.md,
                xml__xpath_match=[self.s2c3.xpath],
                run_odk_validate=False,
            )

    def test_xml__n_xpath_n_match_pass__xpath_exact(self):
        """Should pass when exact matches found for multiple XPaths."""
        self.assertPyxformXform(
            md=self.md,
            xml__xpath_exact=self.suite2_exacts,
            run_odk_validate=False,
        )

    def test_xml__n_xpath_n_match_pass__xpath_count(self):
        """Should pass when count matches found for multiple XPaths."""
        self.assertPyxformXform(
            md=self.md,
            xml__xpath_count=self.suite2_counts,
            run_odk_validate=False,
        )

    @unittest.skip("Scenario 'n_xpath_n_match' NA for xpath_match: expects 1 match only.")
    def test_xml__n_xpath_n_match_pass__xpath_match(self):
        pass  # Test case included to document that there's no way to pass this scenario.

    def test_xml__n_xpath_n_match_fail__xpath_exact(self):
        """Should fail when exact matches not found for one XPath, among other passes."""
        with self.assertRaises(self.failureException):
            self.assertPyxformXform(
                md=self.md,
                xml__xpath_exact=[
                    *self.suite2_exacts,
                    (self.s2c3.xpath, {"bananas", "eggs"}),
                ],
                run_odk_validate=False,
            )

    def test_xml__n_xpath_n_match_fail__xpath_count(self):
        """Should fail when count matches not found for one XPath, among other passes."""
        with self.assertRaises(self.failureException):
            self.assertPyxformXform(
                md=self.md,
                xml__xpath_count=[*self.suite2_counts, (self.s2c3.xpath, 5)],
                run_odk_validate=False,
            )

    def test_xml__n_xpath_n_match_fail__xpath_match(self):
        """Should fail when many matches found for most XPaths, among 1 passing XPath."""
        with self.assertRaises(self.failureException):
            self.assertPyxformXform(
                md=self.md,
                xml__xpath_match=[*self.suite2_xpaths, self.s1c1.xpath],
                run_odk_validate=False,
            )

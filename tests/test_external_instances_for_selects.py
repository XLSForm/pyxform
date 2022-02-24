# -*- coding: utf-8 -*-
"""
Test external instance syntax

See also test_external_instances
"""
import os
from dataclasses import dataclass, field

from tests.pyxform_test_case import PyxformTestCase


@dataclass()
class XPathHelperSelectFromFile:
    """
    XPath expressions for translations-related assertions.
    """

    q_type: str
    q_name: str
    q_file: str
    file_id: str = field(init=False)

    def __post_init__(self):
        self.file_id = os.path.splitext(self.q_file)[0]

    def model_external_instance_and_bind(self):
        jr_path = "file"
        if self.q_file.endswith(".csv"):
            jr_path = "file-csv"
        return f"""
        /h:html/h:head/x:model[
          ./x:instance[
            @id='{self.file_id}'
            and @src='jr://{jr_path}/{self.q_file}'
          ]
          and ./x:bind[
            @nodeset='/test/{self.q_name}'
            and @type="string"
          ]
        ]
        """

    def body_itemset_nodeset_and_refs(self, value="name", label="label", nodeset_pred=""):
        """The body has an itemset node with expected nodeset and child ref attributes."""
        return rf"""
        /h:html/h:body/x:{self.q_type}[@ref='/test/{self.q_name}']
          /x:itemset[
            @nodeset="instance('{self.file_id}')/root/item{nodeset_pred}"
            and ./x:value[@ref='{value}']
            and ./x:label[@ref='{label}']
          ]
        """


class TestSelectFromFile(PyxformTestCase):
    """
    Select one/multiple question types that use data in external files.

    Original spec in https://github.com/XLSForm/pyxform/issues/30
    """

    def setUp(self) -> None:
        self.xp_city_csv = XPathHelperSelectFromFile(
            q_type="select1", q_name="city", q_file="cities.csv"
        )
        self.xp_subs_csv = XPathHelperSelectFromFile(
            q_type="select", q_name="suburbs", q_file="suburbs.csv"
        )
        self.xp_city_xml = XPathHelperSelectFromFile(
            q_type="select1", q_name="city", q_file="cities.xml"
        )
        self.xp_subs_xml = XPathHelperSelectFromFile(
            q_type="select", q_name="suburbs", q_file="suburbs.xml"
        )
        self.xp_test_args = (
            (".csv", self.xp_city_csv, self.xp_subs_csv),
            (".xml", self.xp_city_xml, self.xp_subs_xml),
        )

    def test_no_params_no_filters(self):
        """Should find internal instace referencing the file, and itemset in the select."""
        # re: https://github.com/XLSForm/pyxform/issues/80
        md = """
        | survey |                                        |         |         |
        |        | type                                   | name    | label   |
        |        | select_one_from_file cities{ext}       | city    | City    |
        |        | select_multiple_from_file suburbs{ext} | suburbs | Suburbs |
        """
        for ext, xp_city, xp_subs in self.xp_test_args:
            with self.subTest(msg=ext):
                self.assertPyxformXform(
                    name="test",
                    md=md.format(ext=ext),
                    xml__xpath_match=[
                        xp_city.model_external_instance_and_bind(),
                        xp_subs.model_external_instance_and_bind(),
                        xp_city.body_itemset_nodeset_and_refs(),
                        xp_subs.body_itemset_nodeset_and_refs(),
                    ],
                    run_odk_validate=True,
                )

    def test_with_params_no_filters(self):
        """Should find that parameters value/label override the default itemset name/label."""
        md = """
        | survey |                                        |         |         |                      |
        |        | type                                   | name    | label   | parameters           |
        |        | select_one_from_file cities{ext}       | city    | City    | value=val, label=lbl |
        |        | select_multiple_from_file suburbs{ext} | suburbs | Suburbs | value=val, label=lbl |
        """
        for ext, xp_city, xp_subs in self.xp_test_args:
            with self.subTest(msg=ext):
                self.assertPyxformXform(
                    name="test",
                    md=md.format(ext=ext),
                    xml__xpath_match=[
                        xp_city.model_external_instance_and_bind(),
                        xp_subs.model_external_instance_and_bind(),
                        xp_city.body_itemset_nodeset_and_refs(value="val", label="lbl"),
                        xp_subs.body_itemset_nodeset_and_refs(value="val", label="lbl"),
                    ],
                    run_odk_validate=True,
                )

    def test_no_params_with_filters(self):
        """Should find that choice_filter adds a predicate to the itemset's instance ref"""
        md = """
        | survey |                                        |         |         |                |
        |        | type                                   | name    | label   | choice_filter  |
        |        | select_one_from_file cities{ext}       | city    | City    |                |
        |        | select_multiple_from_file suburbs{ext} | suburbs | Suburbs | city=${{city}} |
        """
        for ext, xp_city, xp_subs in self.xp_test_args:
            with self.subTest(msg=ext):
                self.assertPyxformXform(
                    name="test",
                    md=md.format(ext=ext),
                    xml__xpath_match=[
                        xp_city.model_external_instance_and_bind(),
                        xp_subs.model_external_instance_and_bind(),
                        xp_city.body_itemset_nodeset_and_refs(),
                        xp_subs.body_itemset_nodeset_and_refs(
                            nodeset_pred="[city= /test/city ]"
                        ),
                    ],
                    run_odk_validate=True,
                )

    def test_with_params_with_filters(self):
        """Should find upated value/label refs and predicate in itemset instance ref."""
        md = """
        | survey |                                        |         |         |                |                      |
        |        | type                                   | name    | label   | choice_filter  | parameters           |
        |        | select_one_from_file cities{ext}       | city    | City    |                | value=val, label=lbl |
        |        | select_multiple_from_file suburbs{ext} | suburbs | Suburbs | city=${{city}} | value=val, label=lbl |
        """
        for ext, xp_city, xp_subs in self.xp_test_args:
            with self.subTest(msg=ext):
                self.assertPyxformXform(
                    name="test",
                    md=md.format(ext=ext),
                    xml__xpath_match=[
                        xp_city.model_external_instance_and_bind(),
                        xp_subs.model_external_instance_and_bind(),
                        xp_city.body_itemset_nodeset_and_refs(value="val", label="lbl"),
                        xp_subs.body_itemset_nodeset_and_refs(
                            value="val", label="lbl", nodeset_pred="[city= /test/city ]"
                        ),
                    ],
                    run_odk_validate=True,
                )


class TestSelectOneExternal(PyxformTestCase):
    """
    select_one_external question type, where external_choices are converted to a CSV.
    """

    all_choices = """
      | choices |           |      |       |
      |         | list_name | name | label |
      |         | state     | nsw  | NSW   |
      |         | state     | vic  | VIC   |
      | external_choices |           |           |       |           |
      |                  | list_name | name      | state | city      |
      |                  | city      | Sydney    | nsw   |           |
      |                  | city      | Melbourne | vic   |           |
      |                  | suburb    | Balmain   | nsw   | sydney    |
      |                  | suburb    | Footscray | vic   | melbourne |
    """

    def test_no_params_no_filters(self):
        """Should find that Pyxform errors out, not a supported use case as per #488"""
        md = """
        | survey |                             |        |        |
        |        | type                        | name   | label  |
        |        | select_one state            | state  | State  |
        |        | select_one_external city    | city   | City   |
        |        | select_one_external suburbs | suburb | Suburb |
        """
        # TODO: catch this for a proper user-facing error message?
        with self.assertRaises(KeyError) as err:
            self.assertPyxformXform(
                name="test",
                md=md + self.all_choices,
            )
        self.assertIn("city", str(err.exception))

    def test_with_params_no_filters(self):
        """Should find that an error is returned since 'value' not a supported param."""
        md = """
        | survey |                            |        |        |                      |
        |        | type                       | name   | label  | parameters           |
        |        | select_one state           | state  | State  |                      |
        |        | select_one_external city   | city   | City   | value=val, label=lbl |
        |        | select_one_external suburb | suburb | Suburb | value=val, label=lbl |
        """
        err = (
            "Accepted parameters are 'randomize, seed': 'value' is an invalid parameter."
        )
        self.assertPyxformXform(
            name="test", md=md + self.all_choices, errored=True, error__contains=[err]
        )

    def test_no_params_with_filters(self):
        """Should find that choice_filter generates input()s with refs to external itemsets"""
        md = """
        | survey |                            |        |        |                |
        |        | type                       | name   | label  | choice_filter  |
        |        | select_one state           | state  | State  |                |
        |        | select_one_external city   | city   | City   | state=${state} |
        |        | select_one_external suburb | suburb | Suburb | city=${city}   |
        """
        self.assertPyxformXform(
            name="test",
            md=md + self.all_choices,
            xml__xpath_match=[
                # No external instances generated, only bindings.
                """
                /h:html/h:head/x:model[
                  not(./x:instance[@id='city'])
                  and not(./x:instance[@id='suburb'])
                  and ./x:bind[@nodeset='/test/state' and @type='string']
                  and ./x:bind[@nodeset='/test/city' and @type='string']
                  and ./x:bind[@nodeset='/test/suburb' and @type='string']
                ]
                """,
                # select_one generates internal select.
                """
                /h:html/h:body/x:select1[
                  @ref='/test/state'
                  and ./x:item/x:value[text()='nsw']
                  and ./x:item/x:label[text()='NSW']
                  and ./x:item/x:value[text()='vic']
                  and ./x:item/x:label[text()='VIC']
                ]
                """,
                # select_one_external generates input referencing itemsets.csv
                """
                /h:html/h:body[.
                  /x:input[
                    @ref='/test/city'
                    and @query="instance('city')/root/item[state= /test/state ]"
                    and ./x:label[text()='City']
                  ]
                  and ./x:input[
                    @ref='/test/suburb'
                    and @query="instance('suburb')/root/item[city= /test/city ]"
                    and ./x:label[text()='Suburb']
                  ]
                ]
                """,
            ],
            run_odk_validate=True,
        )

    def test_with_params_with_filters(self):
        """Should find that an error is returned since 'value' not a supported param."""
        md = """
        | survey |                            |        |        |                |                      |
        |        | type                       | name   | label  | choice_filter  | parameters           |
        |        | select_one state           | state  | State  |                |                      |
        |        | select_one_external city   | city   | City   | state=${state} | value=val, label=lbl |
        |        | select_one_external suburb | suburb | Suburb | city=${city}   | value=val, label=lbl |
        """
        err = (
            "Accepted parameters are 'randomize, seed': 'value' is an invalid parameter."
        )
        self.assertPyxformXform(
            name="test", md=md + self.all_choices, errored=True, error__contains=[err]
        )

    def test_list_name_not_in_external_choices_sheet_raises_error(self):
        md = """
        | survey |                             |        |        |                |
        |        | type                        | name   | label  | choice_filter  |
        |        | select_one state            | state  | State  |                |
        |        | select_one_external city    | city   | City   | state=${state} |
        |        | select_one_external suburby | suburb | Suburb | city=${city}   |
        """
        self.assertPyxformXform(
            md=md + self.all_choices,
            errored=True,
            error__contains=["List name not in external choices sheet: suburby"],
        )


class TestInvalidExternalFileInstances(PyxformTestCase):
    def test_external_other_extension_instances(self):
        # re: https://github.com/XLSForm/pyxform/issues/30
        self.assertPyxformXform(
            name="epdf",
            md="""
            | survey |                                              |                |                |
            |        | type                                         | name           | label          |
            |        | select_one_from_file cities.pdf              | city           | City           |
            |        | select_multiple_from_file neighbourhoods.pdf | neighbourhoods | Neighbourhoods |
            """,  # noqa
            errored=True,
            error_contains=["should be a choices sheet in this xlsform"],
        )

    def test_external_choices_sheet_included_instances(self):
        # re: https://github.com/XLSForm/pyxform/issues/30
        self.assertPyxformXform(
            name="epdf",
            md="""
            | survey |                                              |                |                |
            |        | type                                         | name           | label          |
            |        | select_one_from_file cities.pdf              | city           | City           |
            |        | select_multiple_from_file neighbourhoods.pdf | neighbourhoods | Neighbourhoods |

            | choices |
            |         | list name | name  | label |
            |         | fruits    | apple | Apple |
            """,  # noqa
            errored=True,
            error__contains=["List name not in choices sheet: cities.pdf"],
        )

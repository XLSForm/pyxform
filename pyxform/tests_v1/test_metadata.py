# -*- coding: utf-8 -*-
"""
Test language warnings.
"""
import os
import tempfile

from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class MetadataTest(PyxformTestCase):
    """
    Test metadata and related warnings.
    """

    def test_metadata_bindings(self):
        pass
        # we should assert this stuff is here for meta data fields
        # "subscriber id": {
        #     "bind": {
        #         "jr:preload": "property",
        #         "type": "string",
        #         "jr:preloadParams": "subscriberid",
        #     }
        # },
        #         <?xml version="1.0"?>
        # <h:html xmlns="http://www.w3.org/2002/xforms" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa" xmlns:odk="http://www.opendatakit.org/xforms" xmlns:orx="http://openrosa.org/xforms" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
        #   <h:head>
        #     <h:title>pyxform_autotesttitle</h:title>
        #     <model odk:xforms-version="1.0.0">
        #       <instance>
        #         <pyxform_autotestname id="pyxform_autotest_id_string">
        #           <simserial/>
        #           <simserial_test_output/>
        #           <subscriberid/>
        #           <subscriberid_test_output/>
        #           <deviceid/>
        #           <deviceid_test_output/>
        #           <YERPDERP/>
        #           <meta>
        #             <instanceID/>
        #           </meta>
        #         </pyxform_autotestname>
        #       </instance>
        #       <bind jr:preload="property" jr:preloadParams="simserial" nodeset="/pyxform_autotestname/simserial" type="string"/>
        #       <bind nodeset="/pyxform_autotestname/simserial_test_output" readonly="true()" type="string"/>
        #       <bind jr:preload="property" jr:preloadParams="subscriberid" nodeset="/pyxform_autotestname/subscriberid" type="string"/>
        #       <bind nodeset="/pyxform_autotestname/subscriberid_test_output" readonly="true()" type="string"/>
        #       <bind jr:preload="property" jr:preloadParams="deviceid" nodeset="/pyxform_autotestname/deviceid" type="string"/>
        #       <bind nodeset="/pyxform_autotestname/deviceid_test_output" readonly="true()" type="string"/>
        #       <bind nodeset="/pyxform_autotestname/YERPDERP" type="string"/>
        #       <bind jr:preload="uid" nodeset="/pyxform_autotestname/meta/instanceID" readonly="true()" type="string"/>
        #     </model>
        #   </h:head>
        #   <h:body>
        #     <input ref="/pyxform_autotestname/simserial_test_output">
        #       <label> simserial_test_output: <output value=" /pyxform_autotestname/simserial "/> </label></input>
        #     <input ref="/pyxform_autotestname/subscriberid_test_output">
        #       <label> subscriberid_test_output: <output value=" /pyxform_autotestname/subscriberid "/> </label></input>
        #     <input ref="/pyxform_autotestname/deviceid_test_output">
        #       <label> deviceid_test_output: <output value=" /pyxform_autotestname/deviceid "/> </label></input>
        #     <input ref="/pyxform_autotestname/YERPDERP">
        #       <label>yerp derp derp yerp derp</label>
        #     </input>
        #   </h:body>
        # </h:html>


    def test_simserial_deprecation_warning(self):
        warnings = []
        survey = self.md_to_pyxform_survey(
            """
            | survey |              |                          |                                            |
            |        | type         | name                     | label                                      |
            |        | simserial    | simserial                |                                            |
            |        | note         | simserial_test_output    | simserial_test_output: ${simserial}        |
            """,
            warnings = warnings
        )
        tmp = tempfile.NamedTemporaryFile(suffix=".xml", delete=False)
        tmp.close()
        survey.print_xform_to_file(tmp.name, warnings=warnings)        
        self.assertTrue(len(warnings) == 1)
        warning_expected = (
            "[row : 2] simserial is no longer supported on most devices. "
            "Only old versions of Collect on Android versions older than 11 still support it."
        )
        self.assertEqual(warning_expected, warnings[0])
        os.unlink(tmp.name)

    def test_subscriber_id_deprecation_warning(self):
        warnings = []
        survey = self.md_to_pyxform_survey(
            """
            | survey |              |                          |                                            |
            |        | type         | name                     | label                                      |
            |        | subscriberid | subscriberid             | sub id is not lable optional I guess       |
            |        | note         | subscriberid_test_output | subscriberid_test_output: ${subscriberid}  |
            """,
            warnings=warnings
        )
        tmp = tempfile.NamedTemporaryFile(suffix=".xml", delete=False)
        tmp.close()
        survey.print_xform_to_file(tmp.name, warnings=warnings)
        self.assertTrue(len(warnings) == 1)
        warning_expected = (
            "[row : 2] subscriberid is no longer supported on most devices. "
            "Only old versions of Collect on Android versions older than 11 still support it."
        )
        self.assertEqual(warning_expected, warnings[0])
        os.unlink(tmp.name)

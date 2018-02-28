from pyxform.tests_v1.pyxform_test_case import PyxformTestCase


class SettingsAutoSendDelete(PyxformTestCase):
    def test_settings_auto_send_true(self):

        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |              |           |           |
            |          | type         | name      | label     |
            |          | text         | name      | Name      |
            | settings |              |           |           |
            |          | auto_send    |           |           |
            |          | true         |           |           |
            """,
            debug=True,
            xml__contains=[
                '<submission method="form-data-post" orx:auto-send="true"/>'
            ],
        )

    def test_settings_auto_delete_true(self):

        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |              |           |           |
            |          | type         | name      | label     |
            |          | text         | name      | Name      |
            | settings |              |           |           |
            |          | auto_delete  |           |           |
            |          | true         |           |           |
            """,
            debug=True,
            xml__contains=[
                '<submission method="form-data-post" orx:auto-delete="true"/>'
            ],
        )

    def test_settings_auto_send_delete_false(self):

        self.assertPyxformXform(
            name="data",
            md="""
            | survey   |              |           |           |
            |          | type         | name      | label     |
            |          | text         | name      | Name      |
            | settings |              |           |           |
            |          | auto_delete  | auto_send |           |
            |          | false        | false     |           |
            """,
            debug=True,
            xml__contains=[
                '<submission method="form-data-post" orx:auto-delete="false" orx:auto-send="false"/>'
            ],
        )
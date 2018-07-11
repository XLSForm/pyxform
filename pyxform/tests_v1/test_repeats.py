from pyxform.tests_v1.pyxform_test_case import PyxformTestCase

# Verify that a repeat results in both a single repeat instance and a
# repeat template. This means clients always show one repeat and
# can optionally have a template.
class RepeatTests(PyxformTestCase):
    def test_repeat_first_instance(self):
        self.assertPyxformXform(
            md="""
            | Survey |              |         |               |
            |        | type         | name    | label         |
            |        | begin repeat | repeat  | My Repeat     |
            |        | integer      | age     | the age       |
            |        | end repeat   | repeat  |               |
            """,
            xml__contains=[
                """<repeat>
            <age/>
          </repeat>
          <repeat jr:template="">
            <age/>
          </repeat>
          """],
        )

    def test_repeat_first_instance_default(self):
        self.assertPyxformXform(
            md="""
            | Survey |              |         |               |         |
            |        | type         | name    | label         | default |
            |        | begin repeat | repeat  | My Repeat     |         |
            |        | integer      | age     | the age       | 23      |
            |        | end repeat   | repeat  |               |         |
            """,
            xml__contains=[
                """<repeat>
            <age>23</age>
          </repeat>
          <repeat jr:template="">
            <age>23</age>
          </repeat>
          """],
        )

    def test_repeat_first_instance_default_count(self):
        self.assertPyxformXform(
            debug=True,
            md="""
            | Survey |              |         |               |         |              |
            |        | type         | name    | label         | default | repeat_count |
            |        | begin repeat | repeat  | My Repeat     |         | 3            |
            |        | integer      | age     | the age       | 23      |              |
            |        | end repeat   | repeat  |               |         |              |
            """,
            xml__contains=[
                """<repeat>
            <age>23</age>
          </repeat>
          <repeat </age>
          </repeat>
          """],
        )

    def test_repeat_first_instance_group_default(self):
        self.assertPyxformXform(
            md="""
            | Survey |              |         |               |         |
            |        | type         | name    | label         | default |
            |        | begin repeat | repeat  | My Repeat     |         |
            |        | begin group  | group   | My group      |         |
            |        | integer      | age     | the age       | 23      |
            |        | end group    | group   |               |         |
            |        | end repeat   | repeat  |               |         |
            """,
            xml__contains=[
                """<repeat>
            <group>
              <age>23</age>
            </group>
          </repeat>
          <repeat jr:template="">
            <group>
              <age>23</age>
            </group>
          </repeat>
          """],
        )

    def test_nested_repeat_first_instance_defaults(self):
        self.assertPyxformXform(
            debug=True,
            md="""
            | Survey |              |         |               |         |
            |        | type         | name    | label         | default |
            |        | begin repeat | repeat  | My Repeat     |         |
            |        | begin repeat | repeat2 |               |         |
            |        | integer      | age     | the age       | 23      |
            |        | end repeat   | repeat2 |               |         |
            |        | end repeat   | repeat  |               |         |
            """,
            xml__contains=[
                """<repeat>
            <repeat2>
              <age>23</age>
            </repeat2>
            <repeat2 jr:template="">
              <age>23</age>
            </repeat2>
          </repeat>
          <repeat jr:template="">
            <repeat2>
              <age>23</age>
            </repeat2>
            <repeat2 jr:template="">
              <age>23</age>
            </repeat2>
          </repeat>
          """],
        )
"""
## Range control traceability

Each test should reference one (or more) requirements from these lists.

- Validation
  - RC001: parameter delimiters must be one or more spaces optionally with a comma, or semicolon.
  - RC002: parameter values must only be a known name.
  - RC003: parameter names may in lower case or in mixed case.
  - RC004: parameter names and values must be separated by a single equals sign.
  - RC005: parameter values must be numeric (or for 'tick_labelset', the choices).
  - RC006: appearance parameters are only valid with default, 'vertical' or 'no-ticks' appearance.
  - RC007: parameters may specify ranges that are positive, negative, ascending, or descending.
  - parameter 'step':
    - RS001: must not be zero.
    - RS002: must be less than or equal to abs(end - start).
  - parameter 'tick_interval':
    - RI001: must not be zero.
    - RI002: must be less than or equal to abs(end - start).
    - RI003: must be a multiple of 'step'.
  - parameter 'placeholder':
    - RP001: must be a multiple of 'step'.
    - RP002: must be between 'start' and 'end' inclusive.
  - parameter 'tick_labelset':
    - RL001: must match one 'list_name' from the choices sheet.
    - RL002: the referenced choice list must have one or more items.
    - RL003: choice list values must each be a multiple of 'step' or 'tick_interval'.
    - RL004: choice list values must each be between 'start' and 'end' inclusive.
    - RL005: with the 'no-ticks' appearance, choices must match 'start' and 'end' only.
- Behaviour
  - RB001: non-appearance parameters must be control attributes in the default xforms namespace.
  - RB002: appearance parameters must be control attributes in the 'odk' namespace.
  - RB003: the default data type must be 'integer'.
  - RB004: if the range has values that are decimals the data type must be 'decimal'.
"""

from pyxform.errors import ErrorCode

from tests.pyxform_test_case import PyxformTestCase
from tests.xpath_helpers.questions import xpq


class TestRangeParsing(PyxformTestCase):
    def test_parameter_delimiters__ok(self):
        """Should accept delimiters: space, comma, semicolon."""
        # RC001
        md = """
        | survey |
        | | type  | name | label | parameters        |
        | | range | q1   | Q1    | start=2{sep}end=9 |
        """
        cases = (" ", "  ", ",", ";", ", ", ", ", " , ", "; ", " ;", " ; ")
        for value in cases:
            with self.subTest(value):
                self.assertPyxformXform(
                    md=md.format(sep=value),
                    xml__xpath_match=[
                        xpq.body_range("q1", {"start": "2", "end": "9"}),
                    ],
                )

    def test_parameter_list__error(self):
        """Should raise an error for unknown parameters."""
        # RC002
        md = """
        | survey |
        | | type  | name | label | parameters     |
        | | range | q1   | Q1    | start=2 stop=9 |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[
                "Accepted parameters are 'end, placeholder, start, step, tick_interval, tick_labelset'. "
                "The following are invalid parameter(s): 'stop'."
            ],
        )

    def test_parameter_list__ok(self):
        """Should not raise an error for known parameters."""
        # RC002
        md = """
        | survey |
        | | type  | name | label | parameters                                                          |
        | | range | q1   | Q1    | start=2 end=9 step=1 tick_interval=2 placeholder=6 tick_labelset=c1 |

        | choices |
        | | list_name | name | label |
        | | c1        | 2    | N1    |
        | | c1        | 4    | N2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.body_range(
                    "q1",
                    {
                        "start": "2",
                        "end": "9",
                        "step": "1",
                        "odk:tick-interval": "2",
                        "odk:placeholder": "6",
                        "odk:tick-labelset": "c1",
                    },
                ),
            ],
        )

    def test_parameter_list__mixed_case__ok(self):
        """Should not raise an error for known parameters in mixed case."""
        # RC003
        md = """
        | survey |
        | | type  | name | label | parameters                                                          |
        | | range | q1   | Q1    | Start=2 eNd=9 SteP=1 TICK_interval=2 placeHOLDER=6 tick_LABELset=c1 |

        | choices |
        | | list_name | name | label |
        | | c1        | 2    | N1    |
        | | c1        | 4    | N2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.body_range(
                    "q1",
                    {
                        "start": "2",
                        "end": "9",
                        "step": "1",
                        "odk:tick-interval": "2",
                        "odk:placeholder": "6",
                        "odk:tick-labelset": "c1",
                    },
                ),
            ],
        )

    def test_parameter_delimiter_invalid__error(self):
        """Should raise an error for invalid delimiters."""
        # RC004
        md = """
        | survey |
        | | type  | name | label | parameters        |
        | | range | q1   | Q1    | start=2{sep}end=9 |
        """
        cases = (" . ", " & ", "-")
        for value in cases:
            with self.subTest(value):
                self.assertPyxformXform(
                    md=md.format(sep=value),
                    errored=True,
                    error__contains=[
                        "Expecting parameters to be in the form of 'parameter1=value parameter2=value'."
                    ],
                )

    def test_parameter_malformed__error(self):
        """Should raise an error if a parameter is malformed."""
        # RC004
        md = """
        | survey |
        | | type  | name | label | parameters    |
        | | range | q1   | Q1    | {name}{value} |
        """
        params = ("start", "end", "step", "tick_interval", "placeholder")
        cases = ("==1", "1", "==1")
        for name in params:
            for value in cases:
                with self.subTest((name, value)):
                    self.assertPyxformXform(
                        md=md.format(name=name, value=value),
                        errored=True,
                        error__contains=[
                            "Expecting parameters to be in the form of 'parameter1=value parameter2=value'."
                        ],
                    )

    def test_parameter_not_a_number__error(self):
        """Should raise an error if a numeric parameter has a non-numeric value."""
        # RC005
        md = """
        | survey |
        | | type  | name | label | parameters     |
        | | range | q1   | Q1    | {name}={value} |
        """
        params = ("start", "end", "step", "tick_interval", "placeholder")
        cases = ("", "one")
        for name in params:
            for value in cases:
                with self.subTest((name, value)):
                    self.assertPyxformXform(
                        md=md.format(name=name, value=value),
                        errored=True,
                        error__contains=[
                            ErrorCode.RANGE_001.value.format(row=2, name=name)
                        ],
                    )

    def test_parameter_not_a_number__ok(self):
        """Should not raise an error if a numeric parameter has a numeric value."""
        # RC005
        md = """
        | survey |
        | | type  | name | label | parameters |
        | | range | q1   | Q1    | {name}=1   |
        """
        # "end=1" is invalid but "end=2 step=1" is ok
        params = (
            ("start", {"start": "1"}),
            ("end=2 step", {"end": "2", "step": "1"}),
            ("step", {"step": "1"}),
            ("tick_interval", {"odk:tick-interval": "1"}),
            ("placeholder", {"odk:placeholder": "1"}),
        )
        for name, attrs in params:
            with self.subTest((name, attrs)):
                self.assertPyxformXform(
                    md=md.format(name=name),
                    xml__xpath_match=[
                        xpq.body_range("q1", attrs),
                    ],
                )

    def test_parameter_is_zero__error(self):
        """Should raise an error if the relevant ticks parameter is zero."""
        # RS001 RI001
        md = """
        | survey |
        | | type  | name | label | parameters |
        | | range | q1   | Q1    | {name}=0   |
        """
        params = ("step", "tick_interval")
        for name in params:
            with self.subTest(name):
                self.assertPyxformXform(
                    md=md.format(name=name),
                    errored=True,
                    error__contains=[ErrorCode.RANGE_002.value.format(row=2, name=name)],
                )

    def test_parameter_is_zero__ok(self):
        """Should not raise an error if the relevant ticks parameter is not zero."""
        # RS001 RI001
        md = """
        | survey |
        | | type  | name | label | parameters |
        | | range | q1   | Q1    | {name}=1   |
        """
        params = (("step", "step"), ("tick_interval", "odk:tick-interval"))
        for name, attr in params:
            with self.subTest((name, attr)):
                self.assertPyxformXform(
                    md=md.format(name=name),
                    xml__xpath_match=[
                        xpq.body_range("q1", {attr: "1"}),
                    ],
                )

    def test_parameter_greater_than_range__error(self):
        """Should raise an error if the relevant ticks parameter is larger than the range."""
        # RS002 RI002
        md = """
        | survey |
        | | type  | name | label | parameters               |
        | | range | q1   | Q1    | start=0 end=10 {name}=11 |
        """
        params = ("step", "tick_interval")
        for name in params:
            with self.subTest(name):
                self.assertPyxformXform(
                    md=md.format(name=name),
                    errored=True,
                    error__contains=[ErrorCode.RANGE_003.value.format(row=2, name=name)],
                )

    def test_parameter_greater_than_range__ok(self):
        """Should not raise an error if the relevant ticks parameter is not larger than the range."""
        # RS002 RI002
        md = """
        | survey |
        | | type  | name | label | parameters                    |
        | | range | q1   | Q1    | start=1 end=10 {name}={value} |
        """
        params = (("step", "step"), ("tick_interval", "odk:tick-interval"))
        cases = ("1", "2")
        for name, attr in params:
            for value in cases:
                with self.subTest((name, attr, value)):
                    self.assertPyxformXform(
                        md=md.format(name=name, value=value),
                        xml__xpath_match=[
                            xpq.body_range("q1", {attr: value}),
                        ],
                    )

    def test_tick_interval_not_a_multiple_of_step__error(self):
        """Should raise an error if the relevant ticks parameter is not a multiple of 'step'."""
        # RI003 RP001
        md = """
        | survey |
        | | type  | name | label | parameters                                  |
        | | range | q1   | Q1    | start=-3 end=3 step=2 tick_interval={value} |
        """
        cases = ("-3", "3", "-1", "1")
        for value in cases:
            with self.subTest(("tick_interval", value)):
                self.assertPyxformXform(
                    md=md.format(name="tick_interval", value=value),
                    errored=True,
                    error__contains=[
                        ErrorCode.RANGE_004.value.format(row=2, name="tick_interval")
                    ],
                )

    def test_tick_interval_not_a_multiple_of_step__error(self):
        """Should raise an error if the placeholder is not a multiple of 'step' starting at 'start'."""
        # RI003 RP001
        md = """
        | survey |
        | | type  | name | label | parameters                                  |
        | | range | q1   | Q1    | start=-3 end=3 step=2 placeholder={value} |
        """
        cases = ("-2", "2", "0")
        for value in cases:
            with self.subTest(("placeholder", value)):
                self.assertPyxformXform(
                    md=md.format(name="placeholder", value=value),
                    errored=True,
                    error__contains=[
                        ErrorCode.RANGE_004.value.format(row=2, name="placeholder")
                    ],
                )

    def test_parameter_not_a_multiple_of_step__ok(self):
        """Should not raise an error if the relevant ticks parameter is a multiple of 'step'."""
        # RI003 RP001
        md = """
        | survey |
        | | type  | name | label | parameters                           |
        | | range | q1   | Q1    | start=-1 end=1 step=1 {name}={value} |
        """
        params = (
            ("tick_interval", "odk:tick-interval"),
            ("placeholder", "odk:placeholder"),
        )
        cases = ("1", "-1")
        for name, attr in params:
            for value in cases:
                with self.subTest((name, attr, value)):
                    self.assertPyxformXform(
                        md=md.format(name=name, value=value),
                        xml__xpath_match=[
                            xpq.body_range(
                                "q1",
                                {"start": "-1", "end": "1", "step": "1", attr: value},
                            ),
                        ],
                    )

    def test_parameter_not_a_multiple_of_step_decimal__ok(self):
        """Should not raise an error if the relevant ticks parameter is a multiple of 'step'."""
        # RI003 RP001
        md = """
        | survey |
        | | type  | name | label | parameters                           |
        | | range | q1   | Q1    | start=-1 end=1 step=0.1 {name}={value} |
        """
        params = (
            ("tick_interval", "odk:tick-interval"),
            ("placeholder", "odk:placeholder"),
        )
        cases = ("0.6", "-0.6")
        for name, attr in params:
            for value in cases:
                with self.subTest((name, attr, value)):
                    self.assertPyxformXform(
                        md=md.format(name=name, value=value),
                        xml__xpath_match=[
                            xpq.body_range(
                                "q1",
                                {"start": "-1", "end": "1", "step": "0.1", attr: value},
                            ),
                        ],
                    )

    def test_placeholder_outside_range__error(self):
        """Should raise an error if the placeholder is outside the range."""
        # RP002
        md = """
        | survey |
        | | type  | name | label | parameters                               |
        | | range | q1   | Q1    | start=3 end=7 step=2 placeholder={value} |
        """
        cases = ("1", "9")
        for value in cases:
            with self.subTest(value):
                self.assertPyxformXform(
                    md=md.format(value=value),
                    errored=True,
                    error__contains=[
                        ErrorCode.RANGE_005.value.format(row=2, name="placeholder")
                    ],
                )

    def test_placeholder_outside_inverted_range__error(self):
        """Should raise an error if the placeholder is outside an inverted range."""
        # RP002
        md = """
        | survey |
        | | type  | name | label | parameters                               |
        | | range | q1   | Q1    | start=7 end=3 step=2 placeholder={value} |
        """
        cases = ("9", "1")
        for value in cases:
            with self.subTest(value):
                self.assertPyxformXform(
                    md=md.format(value=value),
                    errored=True,
                    error__contains=[
                        ErrorCode.RANGE_005.value.format(row=2, name="placeholder")
                    ],
                )

    def test_placeholder_inside_inverted_range__ok(self):
        """Should not raise an error if the placeholder is inside the range."""
        # RP002
        md = """
        | survey |
        | | type  | name | label | parameters                               |
        | | range | q1   | Q1    | start=7 end=3 step=2 placeholder={value} |
        """
        cases = ("7", "5", "3")
        for value in cases:
            with self.subTest(value):
                self.assertPyxformXform(
                    md=md.format(value=value),
                    xml__xpath_match=[
                        xpq.body_range(
                            "q1",
                            {
                                "start": "7",
                                "end": "3",
                                "step": "2",
                                "odk:placeholder": value,
                            },
                        ),
                    ],
                )

    def test_placeholder_inside_range__ok(self):
        """Should not raise an error if the placeholder is inside the range."""
        # RP002
        md = """
        | survey |
        | | type  | name | label | parameters                               |
        | | range | q1   | Q1    | start=1 end=7 step=2 placeholder={value} |
        """
        cases = ("1", "3", "5", "7")
        for value in cases:
            with self.subTest(value):
                self.assertPyxformXform(
                    md=md.format(value=value),
                    xml__xpath_match=[
                        xpq.body_range(
                            "q1",
                            {
                                "start": "1",
                                "end": "7",
                                "step": "2",
                                "odk:placeholder": value,
                            },
                        ),
                    ],
                )

    def test_tick_labelset_not_found__error(self):
        """Should raise an error if the tick_labelset choice list does not exist."""
        # RL001
        md = """
        | survey |
        | | type  | name | label | parameters       |
        | | range | q1   | Q1    | tick_labelset=c1 |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.RANGE_006.value.format(row=2)],
        )

    def test_tick_labelset_not_found__ok(self):
        """Should not raise an error if the tick_labelset choice list exists."""
        # RL001
        md = """
        | survey |
        | | type  | name | label | parameters       |
        | | range | q1   | Q1    | tick_labelset=c1 |

        | choices |
        | | list_name | name | label |
        | | c1        | 1    | N1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.body_range("q1", {"odk:tick-labelset": "c1"}),
            ],
        )

    def test_tick_labelset_empty__error(self):
        """Should raise an error if the tick_labelset choice list is empty."""
        # RL002
        # Not exactly possible to have an empty list but this shows what happens.
        md = """
        | survey |
        | | type  | name | label | parameters       |
        | | range | q1   | Q1    | tick_labelset=c1 |

        | choices |
        | | list_name | name | label |
        | | c1        |      | N1    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.NAMES_006.value.format(row=2)],
        )

    def test_tick_labelset_no_ticks_too_many_choices__error(self):
        """Should raise an error if the tick_labelset choices has >2 items with no-ticks."""
        # RL005
        md = """
        | survey |
        | | type  | name | label | parameters              | appearance |
        | | range | q1   | Q1    | step=1 tick_labelset=c1 | no-ticks   |

        | choices |
        | | list_name | name | label |
        | | c1        | 1    | N1    |
        | | c1        | 2    | N2    |
        | | c1        | 3    | N3    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.RANGE_007.value.format(row=2)],
        )

    def test_tick_labelset_no_ticks_too_many_choices__ok(self):
        """Should not raise an error if 2 choices with no-ticks are start/end."""
        # RL005
        md = """
        | survey |
        | | type  | name | label | parameters       | appearance |
        | | range | q1   | Q1    | tick_labelset=c1 | no-ticks   |

        | choices |
        | | list_name | name | label |
        | | c1        | 1    | N1    |
        | | c1        | 10   | N2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.body_range(
                    "q1", {"odk:tick-labelset": "c1", "appearance": "no-ticks"}
                ),
            ],
        )

    def test_tick_labelset_no_ticks_too_many_choices__no_duplicates__error(self):
        """Should raise an error for >2 choices with no-ticks when duplicates are not allowed."""
        # RL005
        md = """
        | survey |
        | | type  | name | label | parameters              | appearance |
        | | range | q1   | Q1    | step=1 tick_labelset=c1 | no-ticks   |

        | choices |
        | | list_name | name | label |
        | | c1        | 1    | N1    |
        | | c1        | 1    | N2    |
        | | c1        | 10   | N3    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.NAMES_007.value.format(row=3)],
        )

    def test_tick_labelset_no_ticks_too_many_choices__allow_duplicates__ok(self):
        """Should not raise an error for >2 choices with no-ticks when duplicates are allowed."""
        # RL005
        md = """
        | settings |
        | | allow_choice_duplicates |
        | | yes                     |

        | survey |
        | | type  | name | label | parameters              | appearance |
        | | range | q1   | Q1    | step=1 tick_labelset=c1 | no-ticks   |

        | choices |
        | | list_name | name | label |
        | | c1        | 1    | N1    |
        | | c1        | 1    | N2    |
        | | c1        | 10   | N3    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.body_range(
                    "q1", {"odk:tick-labelset": "c1", "appearance": "no-ticks"}
                ),
            ],
        )

    def test_tick_labelset_no_ticks_choices_not_start_end__error(self):
        """Should raise an error if the tick_labelset choices with no-ticks are not start/end."""
        # RL005
        md = """
        | survey |
        | | type  | name | label | parameters       | appearance |
        | | range | q1   | Q1    | tick_labelset=c1 | no-ticks   |

        | choices |
        | | list_name | name | label |
        | | c1        | 1    | N1    |
        | | c1        | 9    | N2    |
        """
        self.assertPyxformXform(
            md=md,
            errored=True,
            error__contains=[ErrorCode.RANGE_012.value.format(row=2)],
        )

    def test_parameters_not_compatible_with_appearance__error(self):
        """Should raise an error if the appearance parameters are not supported."""
        # RC006
        md = """
        | survey |
        | | type  | name | label | parameters     | appearance |
        | | range | q1   | Q1    | step=6 {param} | {value}    |

        | choices |
        | | list_name | name | label |
        | | c1        | 1    | N1    |
        """
        params = ("tick_interval=1", "placeholder=1", "tick_labelset=c1")
        cases = ("picker", "rating", "someting-new")
        for param in params:
            for value in cases:
                with self.subTest((param, value)):
                    self.assertPyxformXform(
                        md=md.format(param=param, value=value),
                        errored=True,
                        error__contains=[ErrorCode.RANGE_008.value.format(row=2)],
                    )

    def test_parameters_not_compatible_with_appearance__ok(self):
        """Should not raise an error if the appearance parameters are supported."""
        # RC006
        md = """
        | survey |
        | | type  | name | label | parameters     | appearance |
        | | range | q1   | Q1    | step=1 {param} | {value}    |

        | choices |
        | | list_name | name | label |
        | | c1        | 1    | N1    |
        | | c1        | 10   | N2    |
        """
        params = (
            ("tick_interval=2", {"odk:tick-interval": "2"}),
            ("placeholder=3", {"odk:placeholder": "3"}),
            ("tick_labelset=c1", {"odk:tick-labelset": "c1"}),
        )
        cases = ("", "vertical", "no-ticks")
        for param, attr in params:
            for value in cases:
                with self.subTest((param, attr, value)):
                    self.assertPyxformXform(
                        md=md.format(param=param, value=value),
                        xml__xpath_match=[
                            xpq.body_range("q1", attr),
                        ],
                    )

    def test_tick_labelset_choice_is_not_a_number__error(self):
        """Should raise an error if any tick_labelset choices are not numeric."""
        # RC005
        md = """
        | survey |
        | | type  | name | label | parameters       |
        | | range | q1   | Q1    | tick_labelset=c1 |

        | choices |
        | | list_name | name    | label |
        | | c1        | {value} | N1    |
        """
        cases = ("n1", "one", "1n", "infinity")
        for value in cases:
            with self.subTest(value):
                self.assertPyxformXform(
                    md=md.format(value=value),
                    errored=True,
                    error__contains=[ErrorCode.RANGE_009.value.format(row=2)],
                )

    def test_tick_labelset_choice_is_not_a_number__ok(self):
        """Should not raise an error if the tick_labelset choices are numeric."""
        # RC005
        md = """
        | survey |
        | | type  | name | label | parameters       |
        | | range | q1   | Q1    | tick_labelset=c1 |

        | choices |
        | | list_name | name    | label |
        | | c1        | {value} | N1    |
        """
        cases = ("1", "1.0")
        for value in cases:
            with self.subTest(value):
                self.assertPyxformXform(
                    md=md.format(value=value),
                    xml__xpath_match=[
                        xpq.model_instance_bind("q1", "int"),
                        xpq.body_range("q1", {"odk:tick-labelset": "c1"}),
                    ],
                )

    def test_tick_labelset_choice_outside_range__error(self):
        """Should raise an error if any tick_labelset choices are outside the range."""
        # RL004
        md = """
        | survey |
        | | type  | name | label | parameters                            |
        | | range | q1   | Q1    | start=3 end=7 step=2 tick_labelset=c1 |

        | choices |
        | | list_name | name    | label |
        | | c1        | {value} | N1    |
        """
        cases = ("1", "2")
        for value in cases:
            with self.subTest(value):
                self.assertPyxformXform(
                    md=md.format(value=value),
                    errored=True,
                    error__contains=[ErrorCode.RANGE_010.value.format(row=2)],
                )

    def test_tick_labelset_choice_outside_range__ok(self):
        """Should not raise an error if any tick_labelset choices are inside the range."""
        # RL004
        md = """
        | survey |
        | | type  | name | label | parameters                            |
        | | range | q1   | Q1    | start=0 end=7 step=1 tick_labelset=c1 |

        | choices |
        | | list_name | name    | label |
        | | c1        | {value} | N1    |
        """
        cases = ("1", "2")
        for value in cases:
            with self.subTest(value):
                self.assertPyxformXform(
                    md=md.format(value=value),
                    xml__xpath_match=[
                        xpq.body_range(
                            "q1",
                            {
                                "start": "0",
                                "end": "7",
                                "step": "1",
                                "odk:tick-labelset": "c1",
                            },
                        ),
                    ],
                )

    def test_tick_labelset_choice_not_a_multiple_of_tick__error(self):
        """Should raise an error if the relevant ticks parameter is not a multiple of 'step'."""
        # RL003
        md = """
        | survey |
        | | type  | name | label | parameters                              |
        | | range | q1   | Q1    | start=0 end=7 {name}=3 tick_labelset=c1 |

        | choices |
        | | list_name | name    | label |
        | | c1        | {value} | N1    |
        """
        params = ("step", "tick_interval")
        cases = ("2", "4")
        for name in params:
            for value in cases:
                with self.subTest((name, value)):
                    self.assertPyxformXform(
                        md=md.format(name=name, value=value),
                        errored=True,
                        error__contains=[
                            ErrorCode.RANGE_011.value.format(row=2, name=name)
                        ],
                    )

    def test_tick_labelset_choice_not_a_multiple_of_step__ok(self):
        """Should not raise an error if the relevant ticks parameter is a multiple of 'step'."""
        # RL003
        md = """
        | survey |
        | | type  | name | label | parameters                              |
        | | range | q1   | Q1    | start=0 end=7 {name}=1 tick_labelset=c1 |

        | choices |
        | | list_name | name | label |
        | | c1        | 1    | N1    |
        """
        params = ("step", "tick_interval")
        for name in params:
            with self.subTest(name):
                self.assertPyxformXform(
                    md=md.format(name=name),
                    xml__xpath_match=[
                        xpq.body_range(
                            "q1",
                            {
                                "start": "0",
                                "end": "7",
                                "step": "1",
                                "odk:tick-labelset": "c1",
                            },
                        ),
                    ],
                )

    def test_tick_labelset_choice_not_a_multiple_of_step__both__ok(self):
        """Should not raise an error if the choice is a multiple of 'step'."""
        # RL003
        md = """
        | survey |
        | | type  | name | label | parameters                                             |
        | | range | q1   | Q1    | start=1 end=12 step=2 tick_interval=4 tick_labelset=c1 |

        | choices |
        | | list_name | name    | label |
        | | c1        | 8       | N1    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.body_range(
                    "q1",
                    {
                        "start": "1",
                        "end": "12",
                        "step": "2",
                        "odk:tick-interval": "4",
                        "odk:tick-labelset": "c1",
                    },
                ),
            ],
        )

    def test_range_spec_patterns__ok(self):
        """Should not raise an error for valid positive/negative and/or asc/desc ranges."""
        # RC007
        md = """
        | survey |
        | | type  | name | label | parameters |
        | | range | q1   | Q1    | {params}   |
        """
        cases = (
            {"start": "-10", "end": "-1", "step": "1"},  # neg/asc
            {"start": "-10", "end": "-1", "step": "-1"},  # neg/empty
            {"start": "-1", "end": "-10", "step": "1"},  # neg/empty
            {"start": "-1", "end": "-10", "step": "-1"},  # neg/desc
            {"start": "1", "end": "10", "step": "1"},  # pos/asc
            {"start": "1", "end": "10", "step": "-1"},  # pos/empty
            {"start": "10", "end": "1", "step": "1"},  # pos/empty
            {"start": "10", "end": "1", "step": "-1"},  # pos/desc
        )
        for params in cases:
            with self.subTest(params):
                self.assertPyxformXform(
                    md=md.format(params=" ".join(f"{k}={v}" for k, v in params.items())),
                    xml__xpath_match=[xpq.body_range("q1", params)],
                )


class TestRangeOutput(PyxformTestCase):
    def test_defaults(self):
        """Should find that default values are output as attributes of the range control."""
        # RB001 RB003
        md = """
        | survey |
        | | type  | name | label | parameters |
        | | range | q1   | Q1    |            |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "int"),
                xpq.body_range("q1"),
            ],
        )

    def test_parameters__numeric__int(self):
        """Should find that user values are output as attributes of the range control."""
        # RB001 RB002 RB003
        md = """
        | survey |
        | | type  | name | label | parameters      |
        | | range | q1   | Q1    | start=3 end=13 step=2 tick_interval=2 placeholder=7 tick_labelset=c1 |

        | choices |
        | | list_name | name | label |
        | | c1        | 4  | N1    |
        | | c1        | 8  | N2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "int"),
                xpq.body_range(
                    "q1",
                    {
                        "start": "3",
                        "end": "13",
                        "step": "2",
                        "odk:tick-interval": "2",
                        "odk:placeholder": "7",
                        "odk:tick-labelset": "c1",
                    },
                ),
            ],
        )

    def test_parameters__numeric__decimal(self):
        """Should find that user values are output as attributes of the range control."""
        # RB001 RB002 RB004
        md = """
        | survey |
        | | type  | name | label | parameters                                                   |
        | | range | q1   | Q1    | start=0.5 end=5.0 step=0.5 tick_interval=1.5 placeholder=2.5 tick_labelset=c1 |

        | choices |
        | | list_name | name | label |
        | | c1        | 1.5  | N1    |
        | | c1        | 3.0  | N2    |
        """
        self.assertPyxformXform(
            md=md,
            xml__xpath_match=[
                xpq.model_instance_item("q1"),
                xpq.model_instance_bind("q1", "decimal"),
                xpq.body_range(
                    "q1",
                    {
                        "start": "0.5",
                        "end": "5.0",
                        "step": "0.5",
                        "odk:tick-interval": "1.5",
                        "odk:placeholder": "2.5",
                        "odk:tick-labelset": "c1",
                    },
                ),
            ],
        )

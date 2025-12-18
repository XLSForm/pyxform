from enum import Enum


class LexerCases(Enum):
    TEXT01 = ("Literal with just alpha characters.", "foo")
    TEXT02 = ("Literal with numeric characters.", "123")
    TEXT03 = ("Literal with alphanumeric characters.", "bar123")
    TEXT04 = (
        "Literal text containing URI; https://github.com/XLSForm/pyxform/issues/533",
        "https://my-site.com",
    )
    TEXT05 = ("Literal text containing brackets.", "(https://mysite.com)")
    TEXT06 = ("Literal text containing URI.", "go to https://mysite.com")
    TEXT07 = (
        "Literal text containing various non-operator symbols.",
        "Repeat after me: '~!@#$%^&()_",
    )
    TEXT08 = ("Literal text containing various non-operator symbols.", "not_func$")
    TEXT09 = ("Names that look like a math expression.", "f-g")
    TEXT10 = ("Names that look like a math expression.", "f-4")
    TEXT11 = ("Name that looks like a math expression, in a node ref.", "./f-4")

    DATETIME01 = ("Literal date.", "2022-03-14")
    DATETIME02 = ("Literal date, BCE.", "-2022-03-14")
    DATETIME03 = ("Literal time.", "01:02:55")
    DATETIME04 = ("Literal time, UTC.", "01:02:55Z")
    DATETIME05 = ("Literal time, UTC + 0.", "01:02:55+00:00")
    DATETIME06 = ("Literal time, UTC + 10.", "01:02:55+10:00")
    DATETIME07 = ("Literal time, UTC - 7.", "01:02:55-07:00")
    DATETIME08 = ("Literal datetime.", "2022-03-14T01:02:55")
    DATETIME09 = ("Literal datetime, UTC.", "2022-03-14T01:02:55Z")
    DATETIME10 = ("Literal datetime, UTC + 0.", "2022-03-14T01:02:55+00:00")
    DATETIME11 = ("Literal datetime, UTC + 10.", "2022-03-14T01:02:55+10:00")
    DATETIME12 = ("Literal datetime, UTC - 7.", "2022-03-14T01:02:55-07:00")

    GEO01 = ("Literal geopoint.", "32.7377112 -117.1288399 14 5.01")
    GEO02 = (
        "Literal geotrace.",
        "32.7377112 -117.1288399 14 5.01;32.7897897 -117.9876543 14 5.01",
    )
    GEO03 = (
        "Literal geoshape.",
        "32.7377112 -117.1288399 14 5.01;32.7897897 -117.9876543 14 5.01;32.1231231 -117.1145877 14 5.01",
    )

    DYNAMIC01 = ("Function call with no args.", "random()")
    DYNAMIC02 = ("Function with mixture of quotes.", """ends-with('mystr', "str")""")
    DYNAMIC03 = ("Function with node paths.", "ends-with(../t2, ./t4)")
    DYNAMIC04 = (
        "Namespaced function. Although jr:itext probably does nothing?",
        "jr:itext('/test/ref_text:label')",
    )
    DYNAMIC05 = (
        "Compound expression with functions, operators, numeric/string literals.",
        "if(../t2 = 'test', 1, 2) + 15 - int(1.2)",
    )
    DYNAMIC06 = (
        "Compound expression with a literal first.",
        "1 + decimal-date-time(now())",
    )
    DYNAMIC07 = (
        "Nested function calls.",
        """concat(if(../t1 = "this", 'go', "to"), "https://mysite.com")""",
    )
    DYNAMIC08 = ("Two constants in a math expression.", "7 - 4")
    DYNAMIC09 = ("Two constants in a math expression (mod).", "3 mod 3")
    DYNAMIC10 = ("Two constants in a math expression (div).", "5 div 5")
    DYNAMIC11 = ("3 or more constants in a math expression.", "2 + 3 * 4")
    DYNAMIC12 = ("3 or more constants in a math expression.", "5 div 5 - 5")
    DYNAMIC13 = ("Two constants, with a function call.", "random() + 2 * 5")
    DYNAMIC14 = ("Node path with operator and constant.", "./f - 4")
    DYNAMIC15 = ("Two node paths with operator.", "../t2 - ./t4")
    DYNAMIC16 = ("Complex math expression.", "1 + 2 - 3 * 4 div 5 mod 6")
    DYNAMIC17 = ("Function with date type result.", "concat('2022-03', '-14')")
    DYNAMIC18 = ("Pyxform reference.", "${ref_text}")
    DYNAMIC19 = ("Pyxform reference.", "${ref_int}")
    DYNAMIC20 = ("Pyxform reference, with last-saved.", """${last-saved#ref_text}""")
    DYNAMIC21 = (
        "Pyxform reference, with last-saved, inside a function.",
        "if(${last-saved#ref_int} = '', 0, ${last-saved#ref_int} + 1)",
    )

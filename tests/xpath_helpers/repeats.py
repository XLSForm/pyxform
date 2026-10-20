class XPathHelper:
    """XPath expressions for repeats assertions."""

    @staticmethod
    def model_instance(path: str) -> str:
        """Model instance assertion."""
        return f"""/h:html/h:head/x:model/x:instance/x:test_name{path}"""


xpr = XPathHelper()

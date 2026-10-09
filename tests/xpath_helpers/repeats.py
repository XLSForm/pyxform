class XPathHelper:
    """XPath expressions for repeats assertions."""

    @staticmethod
    def model_instance_pred(pred: str) -> str:
        """Model instance predicate assertion."""
        return f"""/h:html/h:head/x:model/x:instance/x:test_name[{pred}]"""


xpr = XPathHelper()

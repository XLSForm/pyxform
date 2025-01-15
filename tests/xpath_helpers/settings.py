class XPathHelper:
    """
    XPath expressions for settings assertions.
    """

    @staticmethod
    def form_title(value: str) -> str:
        """The form_title is set to this value."""
        return f"""
        /h:html/h:head/h:title[text()='{value}']
        """

    @staticmethod
    def form_id(value: str) -> str:
        """The form_id is set to this value."""
        return f"""
        /h:html/h:head/x:model/x:instance/x:test_name/@id[.='{value}']
        """

    @staticmethod
    def language_is_default(lang: str) -> str:
        """The language translation has itext and is marked as the default."""
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@default='true()' and @lang='{lang}']
        """

    @staticmethod
    def language_is_not_default(lang: str) -> str:
        """The language translation has itext and is not marked as the default."""
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[not(@default='true()') and @lang='{lang}']
        """

    @staticmethod
    def language_no_itext(lang: str) -> str:
        """The language translation has no itext."""
        return f"""
        /h:html/h:head/x:model/x:itext[not(descendant::x:translation[@lang='{lang}'])]
        """


xps = XPathHelper()

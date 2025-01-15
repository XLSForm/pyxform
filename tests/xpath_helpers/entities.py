class XPathHelper:
    """
    XPath expressions for entities assertions.
    """

    @staticmethod
    def model_instance_entity() -> str:
        """The base path to the expected entities nodeset."""
        return """
        /h:html/h:head/x:model/x:instance/x:test_name/x:meta/x:entity
        """

    @staticmethod
    def model_instance_dataset(value) -> str:
        """An entity dataset has this value."""
        return f"""
        /h:html/h:head/x:model/x:instance/x:test_name/x:meta/x:entity[@dataset='{value}']
        """

    @staticmethod
    def model_bind_label(value) -> str:
        """An entity binding label has this value, with expected properties."""
        return f"""
        /h:html/h:head/x:model/x:bind[
          @nodeset="/test_name/meta/entity/label"
          and @calculate="{value}"
          and @type="string"
          and @readonly="true()"
        ]
        """


xpe = XPathHelper()

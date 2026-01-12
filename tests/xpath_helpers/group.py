class XPathHelper:
    """
    XPath expressions for settings assertions.
    """

    @staticmethod
    def group_no_label(ref: str) -> str:
        """There is a @ref, and no inline label."""
        return f"""
        /h:html/h:body/x:group[
          @ref='{ref}'
          and count(@*) = 1
          and not(./x:label)
        ]
        """

    @staticmethod
    def group_no_label_appearance(ref: str, appearance: str) -> str:
        """There is a @ref and @appearance, and no inline label."""
        return f"""
        /h:html/h:body/x:group[
          @ref='{ref}'
          and @appearance='{appearance}'
          and count(@*) = 2
          and not(./x:label)
        ]
        """

    @staticmethod
    def group_label_no_translation(ref: str, label: str, path: str = "") -> str:
        """There is a @ref, and an inline label."""
        return f"""
        /h:html/h:body{path}/x:group[
          @ref='{ref}'
          and count(@*) = 1
          and ./x:label[
            not(@ref)
            and text()='{label}'
          ]
        ]
        """

    @staticmethod
    def group_label_translation(ref: str, path: str = "") -> str:
        """There is a @ref, and a translated label."""
        return f"""
        /h:html/h:body{path}/x:group[
          @ref='{ref}'
          and count(@*) = 1
          and ./x:label[
            @ref="jr:itext('{ref}:label')"
            and not(text())
          ]
        ]
        """

    @staticmethod
    def group_label_no_translation_appearance(
        ref: str, label: str, appearance: str
    ) -> str:
        """There is a @ref and @appearance, and an inline label."""
        return f"""
        /h:html/h:body/x:group[
          @ref='{ref}'
          and @appearance='{appearance}'
          and count(@*) = 2
          and ./x:label[
            not(@ref)
            and text()='{label}'
          ]
        ]
        """

    @staticmethod
    def group_label_translation_appearance(ref: str, appearance: str) -> str:
        """There is a @ref and @appearance, and a translated label."""
        return f"""
        /h:html/h:body/x:group[
          @ref='{ref}'
          and @appearance='{appearance}'
          and count(@*) = 2
          and ./x:label[
            @ref="jr:itext('{ref}:label')"
            and not(text())
          ]
        ]
        """


xpg = XPathHelper()

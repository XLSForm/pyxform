JR_PREFIXES = {
    "audio": "jr://audio/",
    "image": "jr://images/",
    "big-image": "jr://images/",
    "video": "jr://video/",
}


class XPathHelper:
    """
    XPath expressions for choices assertions.
    """

    @staticmethod
    def model_instance_choices_label(cname: str, choices: tuple[tuple[str, str], ...]):
        """Model instance has choices elements with name and label."""
        choices_xp = "\n              and ".join(
            (
                f"./x:item/x:name/text() = '{cv}' and ./x:item/x:label/text() = '{cl}'"
                for cv, cl in choices
            )
        )
        return rf"""
        /h:html/h:head/x:model/x:instance[@id='{cname}']/x:root[
          {choices_xp}
        ]
        """

    @staticmethod
    def model_instance_choices_itext(cname: str, choices: tuple[str, ...]):
        """Model instance has choices elements with name but no label."""
        choices_xp = "\n              and ".join(
            (
                f"""
                ./x:item/x:name/text() = '{cv}'
                  and not(./x:item/x:label)
                  and ./x:item/x:itextId = '{cname}-{idx}'
                """
                for idx, cv in enumerate(choices)
            )
        )
        return rf"""
        /h:html/h:head/x:model/x:instance[@id='{cname}']/x:root[
          {choices_xp}
        ]
        """

    @staticmethod
    def model_itext_no_text_by_id(lang, id_str):
        """Model itext does not have a text node. Lookup by reference."""
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[
          @lang='{lang}'
          and not(descendant::x:text[@id='{id_str}'])
        ]
        """

    @staticmethod
    def model_itext_choice_text_label_by_ref(qname, lang, cname, label):
        """Model itext has a text label and no other forms. Lookup by reference."""
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test_name/{qname}/{cname}:label']
          /x:value[not(@form) and text()='{label}']
        """

    @staticmethod
    def model_itext_choice_text_label_by_pos(lang, cname, choices: tuple[str, ...]):
        """Model itext has a text label and no other forms. Lookup by position."""
        choices_xp = "\n              and ".join(
            (
                f"""
                ./x:text[
                  @id='{cname}-{idx}'
                  and ./x:value[not(@form) and text()='{cl}']
                ]
                """
                for idx, cl in enumerate(choices)
            )
        )
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[
          @lang='{lang}' and
          {choices_xp}
        ]
        """

    @staticmethod
    def model_itext_choice_media_by_pos(
        lang, cname, choices: tuple[tuple[tuple[str, ...]]]
    ):
        """
        Model itext has a text label and no other forms. Lookup by position.

        Tuples: choices(choice((form, media), (form, media)), choice((form, media)))
        """
        choices_xp = "\n              and ".join(
            (
                f"""
                ./x:text[
                  @id='{cname}-{idx}'
                  and ./x:value[@form='{form}' and text()='{JR_PREFIXES[form]}{media}']
                ]
                """
                for idx, choice in enumerate(choices)
                for form, media in choice
                if form is not None
            )
        )
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[
          @lang='{lang}' and
          {choices_xp}
        ]
        """

    @staticmethod
    def model_no_itext_choice_media_by_pos(
        lang, cname, choices: tuple[tuple[tuple[str, ...]]]
    ):
        """
        Model itext has a text label and no other forms. Lookup by position.

        Tuples: choices(choice((form, media), (form, media)), choice((form, media)))
        """
        choices_xp = "\n              and ".join(
            (
                f"""
                ./x:text[
                  @id='{cname}-{idx}'
                  and not(descendant::x:value[@form='{form}' and text()='{JR_PREFIXES[form]}{media}'])
                ]
                """
                for idx, choice in enumerate(choices)
                for form, media in choice
                if form is not None
            )
        )
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[
          @lang='{lang}' and
          {choices_xp}
        ]
        """

    @staticmethod
    def body_itemset_references_itext(qtype: str, qname: str, cname: str) -> str:
        """The Choice list (itemset) references an itext entry and internal instance."""
        return f"""
        /h:html/h:body/x:{qtype}[@ref='/test_name/{qname}']
          /x:itemset[@nodeset="instance('{cname}')/root/item[{qname} != '']"
            and child::x:label[@ref='jr:itext(itextId)'] and child::x:value[@ref='name']]
        """


xpc = XPathHelper()

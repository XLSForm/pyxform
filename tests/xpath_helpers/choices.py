from typing import Tuple


class XPathHelper:
    """
    XPath expressions for choices assertions.
    """

    @staticmethod
    def model_instance_choices_label(cname: str, choices: Tuple[Tuple[str, str], ...]):
        """Model instance has choices elements with name and label."""
        choices_xp = "\n              and ".join(
            (
                f"./x:item/x:name/text() = '{cv}' and ./x:item/x:label/text() = '{cl}'"
                for cv, cl in choices
            )
        )
        return fr"""
        /h:html/h:head/x:model/x:instance[@id='{cname}']/x:root[
          {choices_xp}
        ]
        """

    @staticmethod
    def model_instance_choices_itext(cname: str, choices: Tuple[str, ...]):
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
        return fr"""
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
    def model_itext_choice_text_label_by_pos(lang, cname, choices: Tuple[str, ...]):
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
    def model_itext_choice_media_by_pos(lang, clist, pos, form, fname):
        """Model itext has a text label and no other forms. Lookup by position."""
        prefix = {
            "audio": "jr://audio/",
            "image": "jr://images/",
            "video": "jr://video/",
        }
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='{clist}-{pos}']
          /x:value[@form='{form}' and text()='{prefix[form]}{fname}']
        """


xpc = XPathHelper()

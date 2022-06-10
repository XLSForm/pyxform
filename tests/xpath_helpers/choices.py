from typing import Tuple


class XPathHelper:
    """
    XPath expressions for choices assertions.
    """

    @staticmethod
    def model_instance_choices(c_name: str, choices: Tuple[Tuple[str, str], ...]):
        """Model instance has choices elements with name and label."""
        choices_xp = "\n              and ".join(
            (
                f"./x:item/x:name/text() = '{cv}' and ./x:item/x:label/text() = '{cl}'"
                for cv, cl in choices
            )
        )
        return fr"""
        /h:html/h:head/x:model/x:instance[@id='{c_name}']/x:root[
          {choices_xp}
        ]
        """

    @staticmethod
    def model_instance_choices_nl(c_name: str, choices: Tuple[Tuple[str, str], ...]):
        """Model instance has choices elements with name but no label."""
        choices_xp = "\n              and ".join(
            (
                f"./x:item/x:name/text() = '{cv}' and not(./x:item/x:label)"
                for cv, cl in choices
            )
        )
        return fr"""
            /h:html/h:head/x:model/x:instance[@id='{c_name}']/x:root[
              {choices_xp}
            ]
            """

    @staticmethod
    def body_select1_itemset(q_name: str):
        """Body has a select1 with an itemset, and no inline items."""
        return fr"""
        /h:html/h:body/x:select1[
          @ref = '/test_name/{q_name}'
          and ./x:itemset
          and not(./x:item)
        ]
        """

    @staticmethod
    def body_odk_rank_itemset(q_name: str):
        """Body has a rank with an itemset, and no inline items."""
        return fr"""
        /h:html/h:body/odk:rank[
          @ref = '/test_name/{q_name}'
          and ./x:itemset
          and not(./x:item)
        ]
        """


xp = XPathHelper()

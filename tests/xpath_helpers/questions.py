class XPathHelper:
    """
    XPath expressions for choices assertions.
    """

    @staticmethod
    def model_instance_item(q_name: str):
        """Model instance contains the question item."""
        return fr"""
          /h:html/h:head/x:model/x:instance/x:test_name/x:{q_name}
        """

    @staticmethod
    def model_instance_bind(q_name: str, _type: str):
        """Model instance contains the question item."""
        return fr"""
          /h:html/h:head/x:model/x:bind[
            @nodeset='/test_name/{q_name}'
            and @type='{_type}'
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
    def body_group_select1_itemset(g_name: str, q_name: str):
        """Body has a select1 with an itemset, and no inline items."""
        return fr"""
        /h:html/h:body/x:group[@ref='/test_name/{g_name}']/x:select1[
          @ref = '/test_name/{g_name}/{q_name}'
          and ./x:itemset
          and not(./x:item)
        ]
        """

    @staticmethod
    def body_repeat_select1_itemset(r_name: str, q_name: str):
        """Body has a select1 with an itemset, and no inline items."""
        return fr"""
        /h:html/h:body/x:group[@ref='/test_name/{r_name}']
          /x:repeat[@nodeset='/test_name/{r_name}']
            /x:select1[
              @ref = '/test_name/{r_name}/{q_name}'
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

    @staticmethod
    def body_input_label_output_value(q_name: str):
        """Body has an input (note) with output reference in the label."""
        return fr"""
        /h:html/h:body/x:input[@ref='/test_name/{q_name}']/x:label/x:output/@value
        """


xpq = XPathHelper()

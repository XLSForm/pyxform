class XPathHelper:
    """
    XPath expressions for questions assertions.
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
    def model_itext_label(q_name: str, lang: str, q_label: str):
        """Model itext contains the question label."""
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test_name/{q_name}:label']
          /x:value[not(@form) and text()='{q_label}']
        """

    @staticmethod
    def model_itext_form(q_name: str, lang: str, form: str, fname: str):
        """Model itext contains an alternate form itext for the label or hint."""
        prefix = {
            "audio": ("label", "jr://audio/"),
            "image": ("label", "jr://images/"),
            "big-image": ("label", "jr://images/"),
            "video": ("label", "jr://video/"),
            "guidance": ("hint", ""),
        }
        return f"""
        /h:html/h:head/x:model/x:itext/x:translation[@lang='{lang}']
          /x:text[@id='/test_name/{q_name}:{prefix[form][0]}']
          /x:value[@form='{form}' and text()='{prefix[form][1]}{fname}']
        """

    @staticmethod
    def body_label_inline(q_type: str, q_name: str, q_label: str):
        """Body element contains the question label."""
        return f"""
        /h:html/h:body/x:{q_type}[@ref='/test_name/{q_name}']
          /x:label[not(@ref) and text()='{q_label}']
        """

    @staticmethod
    def body_label_itext(q_type: str, q_name: str):
        """Body element references itext for the question label."""
        return f"""
        /h:html/h:body/x:{q_type}[@ref='/test_name/{q_name}']
          /x:label[@ref="jr:itext('/test_name/{q_name}:label')" and not(text())]
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

class XPathHelper:
    """
    XPath expressions for entities assertions.
    """

    @staticmethod
    def model_entities_version(version: str):
        return f"""
        /h:html/h:head/x:model[@entities:entities-version='{version}']
        """

    @staticmethod
    def model_no_entities_version():
        return """
        /h:html/h:head/x:model/@*[
          not(
            namespace-uri()='http://www.opendatakit.org/xforms/entities'
            and local-name()='entities-version'
          )
        ]
        """

    @staticmethod
    def model_instance_meta(
        list_name: str,
        meta_path: str = "",
        repeat: bool = False,
        template: bool = False,
        create: bool = False,
        update: bool = False,
        label: bool = False,
    ) -> str:
        assertion = {True: "{0}", False: "not({0})"}
        repeat_asserts = ("not(./x:instanceID)",)
        template_asserts = ("@jr:template",)
        create_asserts = ("@create='1'",)
        update_asserts = (
            "@update='1'",
            "@baseVersion=''",
            "@branchId=''",
            "@trunkVersion=''",
        )
        label_asserts = ("./x:label",)
        return f"""
        /h:html/h:head/x:model/x:instance/x:test_name{meta_path}[
          {" and ".join(assertion[template].format(i) for i in template_asserts)}
        ]/x:meta[
          {" and ".join(assertion[repeat].format(i) for i in repeat_asserts)}
        ]/x:entity[
          @dataset='{list_name}'
          and @id=''
          and {" and ".join(assertion[create].format(i) for i in create_asserts)}
          and {" and ".join(assertion[update].format(i) for i in update_asserts)}
          and {" and ".join(assertion[label].format(i) for i in label_asserts)}
        ]
        """

    @staticmethod
    def model_setvalue_meta_id(meta_path: str = "", repeat: bool = False) -> str:
        new_repeat = ""
        if repeat:
            new_repeat = " odk-new-repeat"
        return f"""
        /h:html/h:head/x:model/x:setvalue[
          @ref='/test_name{meta_path}/meta/entity/@id'
          and @event='odk-instance-first-load{new_repeat}'
          and @type='string'
          and @readonly='true()'
          and @value='uuid()'
        ]
        """

    @staticmethod
    def model_no_setvalue_meta_id(meta_path: str = "") -> str:
        return f"""
        /h:html/h:head/x:model[
          not(./x:setvalue[@ref='/test_name{meta_path}/meta/entity/@id'])
        ]
        """

    @staticmethod
    def model_bind_question_saveto(qpath: str, saveto: str) -> str:
        return f"""
        /h:html/h:head/x:model/x:bind[
          @nodeset='/test_name{qpath}'
          and @entities:saveto='{saveto}'
        ]
        """

    @staticmethod
    def model_bind_meta_id(expression: str = "", meta_path: str = "") -> str:
        assertion = {True: "{0}", False: "not({0})"}
        expression_asserts = ("@calculate",)
        if expression:
            expression_asserts = (f"@calculate='{expression}'",)
        return f"""
        /h:html/h:head/x:model/x:bind[
          @nodeset='/test_name{meta_path}/meta/entity/@id'
          and {" and ".join(assertion[bool(expression)].format(i) for i in expression_asserts)}
          and @type='string'
          and @readonly='true()'
        ]
        """

    @staticmethod
    def model_bind_meta_create(expression: str, meta_path: str = "") -> str:
        return f"""
        /h:html/h:head/x:model/x:bind[
          @nodeset='/test_name{meta_path}/meta/entity/@create'
          and @calculate="{expression}"
          and @type='string'
          and @readonly='true()'
        ]
        """

    @staticmethod
    def model_bind_meta_update(expression: str, meta_path: str = "") -> str:
        return f"""
        /h:html/h:head/x:model/x:bind[
          @nodeset='/test_name{meta_path}/meta/entity/@update'
          and @calculate="{expression}"
          and @type='string'
          and @readonly='true()'
        ]
        """

    @staticmethod
    def model_bind_meta_baseversion(
        list_name: str, id_path: str, meta_path: str = ""
    ) -> str:
        return f"""
        /h:html/h:head/x:model/x:bind[
          @nodeset='/test_name{meta_path}/meta/entity/@baseVersion'
          and @calculate="instance('{list_name}')/root/item[name= {id_path} ]/__version"
          and @type='string'
          and @readonly='true()'
        ]
        """

    @staticmethod
    def model_bind_meta_trunkversion(
        list_name: str, id_path: str, meta_path: str = ""
    ) -> str:
        return f"""
        /h:html/h:head/x:model/x:bind[
          @nodeset='/test_name{meta_path}/meta/entity/@trunkVersion'
          and @calculate="instance('{list_name}')/root/item[name= {id_path} ]/__trunkVersion"
          and @type='string'
          and @readonly='true()'
        ]
        """

    @staticmethod
    def model_bind_meta_branchid(
        list_name: str, id_path: str, meta_path: str = ""
    ) -> str:
        return f"""
        /h:html/h:head/x:model/x:bind[
          @nodeset='/test_name{meta_path}/meta/entity/@branchId'
          and @calculate="instance('{list_name}')/root/item[name= {id_path} ]/__branchId"
          and @type='string'
          and @readonly='true()'
        ]
        """

    @staticmethod
    def model_bind_meta_label(value: str, meta_path: str = "") -> str:
        return f"""
        /h:html/h:head/x:model/x:bind[
          @nodeset="/test_name{meta_path}/meta/entity/label"
          and @calculate="{value}"
          and @type='string'
          and @readonly='true()'
        ]
        """

    @staticmethod
    def model_bind_meta_instanceid() -> str:
        return """
        /h:html/h:head/x:model/x:bind[
          @nodeset='/test_name/meta/instanceID'
          and @readonly='true()'
          and @type='string'
          and @jr:preload='uid'
        ]
        """


xpe = XPathHelper()

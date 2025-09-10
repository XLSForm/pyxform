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
    def model_instance_repeat(
        list_name: str,
        meta_path: str = "",
        template: bool = False,
        create: bool = False,
        update: bool = False,
    ) -> str:
        template_attrs = " not(@jr:template) "
        if template:
            template_attrs = " @jr:template='' "
        create_attrs = " "
        if create:
            create_attrs = " and @create='1' "
        update_attrs = " "
        if update:
            update_attrs = " and @update='1' and @baseVersion='' and @branchId='' and @trunkVersion='' "
        return f"""
        /h:html/h:head/x:model/x:instance/x:test_name{meta_path}[
          {template_attrs}
        ]/x:meta[not(./instanceID)]/x:entity[
          @dataset='{list_name}'
          and @id=''
          {create_attrs}
          {update_attrs}
        ]
        """

    @staticmethod
    def model_instance_dataset(value) -> str:
        """An entity dataset has this value."""
        return f"""
        /h:html/h:head/x:model/x:instance/x:test_name/x:meta/x:entity[@dataset='{value}']
        """

    @staticmethod
    def model_setvalue_meta_id(meta_path: str = "") -> str:
        return f"""
        /h:html/h:head/x:model/x:setvalue[
          @ref='/test_name{meta_path}/meta/entity/@id'
          and @event='odk-instance-first-load'
          and @type='string'
          and @readonly='true()'
          and @value='uuid()'
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
    def model_bind_meta_id(meta_path: str = "") -> str:
        return f"""
        /h:html/h:head/x:model/x:bind[
          @nodeset='/test_name{meta_path}/meta/entity/@id'
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

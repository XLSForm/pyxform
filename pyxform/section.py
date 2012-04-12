from question import SurveyElement
from utils import node
from errors import PyXFormError


class Section(SurveyElement):
    def validate(self):
        super(Section, self).validate()
        for element in self.children:
            element.validate()
        self._validate_uniqueness_of_element_names()

    # there's a stronger test of this when creating the xpath
    # dictionary for a survey.
    def _validate_uniqueness_of_element_names(self):
        element_slugs = []
        for element in self.children:
            if element.name in element_slugs:
                raise PyXFormError(
                    "There are two survey elements named '%s' in the section named '%s'." % (element.name, self.name)
                    )
            element_slugs.append(element.name)

    def xml_instance(self, **kwargs):
        """
        Creates an xml representation of the section
        """
        result = node(self.name, **kwargs)
        for child in self.children:
            result.appendChild(child.xml_instance())
        return result

    def xml_control(self):
        """
        Ideally, we'll have groups up and rolling soon, but for now
        let's just return a list of controls from all the children of
        this section.
        """
        return [e.xml_control() for e in self.children if e.xml_control() is not None]


class RepeatingSection(Section):
    def xml_control(self):
        """
        <group>
        <label>Fav Color</label>
        <repeat nodeset="fav-color">
          <select1 ref=".">
            <label ref="jr:itext('fav')" />
            <item><label ref="jr:itext('red')" /><value>red</value></item>
            <item><label ref="jr:itext('green')" /><value>green</value></item>
            <item><label ref="jr:itext('yellow')" /><value>yellow</value></item>
          </select1>
        </repeat>
        </group>
        """
        control_dict = self.control
        kwargs = {}
        if u"jr:count" in self and self[u"jr:count"] != "":
            kwargs = {u"jr:count" : self[u"jr:count"]}
        if u"appearance" in control_dict:
            repeat_node = node(
                u"repeat", nodeset=self.get_xpath(),
                appearance=control_dict[u"appearance"],
                **kwargs
                )
        else:
            repeat_node = node(u"repeat", nodeset=self.get_xpath(), **kwargs)
        for n in Section.xml_control(self):
            repeat_node.appendChild(n)

        label = self.xml_label()
        if label:
            return node(
                u"group", self.xml_label(), repeat_node,
                ref=self.get_xpath()
                )
        return node(u"group", repeat_node, ref=self.get_xpath())
    #I'm anal about matching function signatures when overriding a function, but there's no reason for kwargs to be an argument
    def xml_instance(self, **kwargs):
        kwargs = {"jr:template": ""} #It might make more sense to add this as a child on initialization
        return super(RepeatingSection, self).xml_instance(**kwargs)

class GroupedSection(Section):
#    I think this might be a better place for the table-list stuff, however it doesn't allow for as good of validation as putting it in xls2json
#    def __init__(self, **kwargs):
#        control = kwargs.get(u"control")
#        if control:
#            appearance = control.get(u"appearance")
#            if appearance is u"table-list":
#                print "HI"
#                control[u"appearance"] = "field-list"
#                kwargs["children"].insert(0, kwargs["children"][0])
#        super(GroupedSection, self).__init__(kwargs)
        
    def xml_control(self):
        control_dict = self.control
        xml_label = self.xml_label()

        if u"appearance" in control_dict and xml_label:
            group_node = node(
                u"group", xml_label, ref=self.get_xpath(),
                appearance=control_dict[u"appearance"]
                )
        elif u"appearance" in control_dict and not xml_label:
            group_node = node(
                u"group", ref=self.get_xpath(),
                appearance=control_dict[u"appearance"]
                )
        elif not u"appearance" in control_dict and xml_label:
            group_node = node(u"group", self.xml_label(), ref=self.get_xpath())
        else:
            group_node = node(u"group", ref=self.get_xpath())
        for n in Section.xml_control(self):
            group_node.appendChild(n)
        return group_node

    def to_json_dict(self):
        # This is quite hacky, might want to think about a smart way
        # to approach this problem.
        result = super(GroupedSection, self).to_json_dict()
        result[u"type"] = u"group"
        return result

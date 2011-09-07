from question import SurveyElement
from utils import node


class Section(SurveyElement):
    def validate(self):
        super(Section, self).validate()
        for element in self._children:
            element.validate()
        self._validate_uniqueness_of_element_names()

    # there's a stronger test of this when creating the xpath
    # dictionary for a survey.
    def _validate_uniqueness_of_element_names(self):
        element_slugs = []
        for element in self._children:
            if element.get_name() in element_slugs:
                raise Exception(
                    "Element with this name already exists.",
                    element_slugs, element.get_name()
                    )
            element_slugs.append(element.get_name())

    def xml_instance(self):
        if type(self) == RepeatingSection:
            kwargs = {"jr:template": ""}
        else:
            kwargs = {}
        result = node(self.get_name(), **kwargs)
        for child in self._children:
            result.appendChild(child.xml_instance())
        return result

    def xml_control(self):
        """
        Ideally, we'll have groups up and rolling soon, but for now
        let's just return a list of controls from all the children of
        this section.
        """
        return [e.xml_control() for e in self._children if e.xml_control() is not None]


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
        control_dict = self.get_control()
        if u"appearance" in control_dict:
            repeat_node = node(
                u"repeat", nodeset=self.get_xpath(),
                appearance=control_dict[u"appearance"]
                )
        else:
            repeat_node = node(u"repeat", nodeset=self.get_xpath())
        for n in Section.xml_control(self):
            repeat_node.appendChild(n)

        label = self.xml_label()
        if label:
            return node(
                u"group", self.xml_label(), repeat_node,
                ref=self.get_xpath()
                )
        return node(u"group", repeat_node, ref=self.get_xpath())


class GroupedSection(Section):
    def xml_control(self):
        control_dict = self.get_control()
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

    def to_dict(self):
        # This is quite hacky, might want to think about a smart way
        # to approach this problem.
        result = super(GroupedSection, self).to_dict()
        result[u"type"] = u"group"
        return result

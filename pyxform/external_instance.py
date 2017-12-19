from pyxform.survey_element import SurveyElement
from pyxform.utils import node


class ExternalInstance(SurveyElement):

    def xml_instance(self):
        """
        Get the XML representation of the external instance element.
        """
        return node(
            "instance",
            id=self[u"name"],
            src="jr://file/{}.xml".format(self[u"name"]))

    def xml_control(self):
        """
        No-op since there is no associated form control to place under <body/>.

        Exists here because there's a soft abstractmethod in SurveyElement.
        """
        pass

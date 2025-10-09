from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyxform.utils import DetachableElement


class Element:
    """
    Base class for Element interface and default behaviour.

    Unlike SurveyElement which may emit multiple elements for a particular survey
    component, this class is for defining individual elements for output.
    """

    name: str

    def node(self) -> "DetachableElement":
        """
        Create the element.
        """
        raise NotImplementedError()

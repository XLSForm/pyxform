from collections.abc import Generator
from itertools import chain
from typing import TYPE_CHECKING
from xml.dom.minidom import Attr

from pyxform import constants as const
from pyxform.elements import action
from pyxform.survey_element import SURVEY_ELEMENT_FIELDS, SurveyElement
from pyxform.utils import DetachableElement

if TYPE_CHECKING:
    from pyxform.survey import Survey


ATTRIBUTE_EXTRA_FIELDS = (
    "actions",
    "value",
    const.BIND,
    const.TYPE,
)
ATTRIBUTE_FIELDS = (*SURVEY_ELEMENT_FIELDS, *ATTRIBUTE_EXTRA_FIELDS)


class Attribute(SurveyElement):
    @staticmethod
    def get_slot_names() -> tuple[str, ...]:
        return ATTRIBUTE_FIELDS

    def __init__(self, fields: tuple[str, ...] | None = None, **kwargs):
        # Structure
        self.actions: list[dict[str, str]] | None = None
        self.value: str = ""
        self.bind: dict | None = None
        self.type: str | None = None

        if fields is None:
            fields = ATTRIBUTE_FIELDS
        else:
            fields = chain(ATTRIBUTE_FIELDS, fields)
        super().__init__(fields=fields, **kwargs)

    @property
    def name_for_xpath(self) -> str:
        return f"@{self.name}"

    def xml_instance(self, survey: "Survey", **kwargs):
        attr = Attr(self.name)
        attr.value = self.value
        return attr

    def xml_actions(
        self, survey: "Survey", in_repeat: bool = False
    ) -> Generator[DetachableElement | None, None, None]:
        action_fields = {"name", "event", "value"}
        if self.actions:
            for _action in self.actions:
                event = action.Event(_action["event"])
                if (not in_repeat and event == action.Event.ODK_NEW_REPEAT.value) or (
                    in_repeat and event != action.Event.ODK_NEW_REPEAT
                ):
                    continue

                yield action.ACTION_CLASSES[_action["name"]](
                    ref=self.get_xpath(),
                    event=event,
                    value=_action.get("value"),
                    **{k: v for k, v in _action.items() if k not in action_fields},
                ).node()

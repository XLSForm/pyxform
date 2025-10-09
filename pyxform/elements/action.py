from enum import Enum

from pyxform.elements.element import Element
from pyxform.util.enum import StrEnum
from pyxform.utils import node


class Event(StrEnum):
    """
    Supported W3C XForms 1.1 Events and ODK extensions.
    """

    # For actions in model under /html/head/model
    ODK_INSTANCE_FIRST_LOAD = "odk-instance-first-load"
    ODK_INSTANCE_LOAD = "odk-instance-load"
    # For actions in repeat control under /html/body
    ODK_NEW_REPEAT = "odk-new-repeat"
    # For actions in question control under /html/body
    XFORMS_VALUE_CHANGED = "xforms-value-changed"


class Action(Element):
    """
    Base class for supported Action elements.

    https://getodk.github.io/xforms-spec/#actions
    """

    __slots__ = ("event", "kwargs", "ref", "value")

    def __init__(
        self,
        ref: str,
        event: Event,
        value: str | None = None,
        **kwargs,
    ):
        super().__init__()
        self.ref: str = ref
        self.event: Event = event
        self.value: str | None = value

    def node(self):
        return node(self.name, ref=self.ref, event=self.event.value)


class Setvalue(Action):
    """
    Explicitly sets the value of the specified instance data node.

    https://getodk.github.io/xforms-spec/#action:setvalue
    """

    name = "setvalue"

    def __init__(self, ref: str, event: Event, value: str | None = None, **kwargs):
        super().__init__(ref=ref, event=event, value=value, **kwargs)

    def node(self):
        result = super().node()
        if self.value:
            result.setAttribute("value", self.value)
        return result


class ODKSetGeopoint(Action):
    """
    Sets the current location's geopoint value in the instance data node specified in the
    ref attribute.

    https://getodk.github.io/xforms-spec/#action:setgeopoint
    """

    name = "odk:setgeopoint"

    def __init__(
        self,
        ref: str,
        event: Event,
        value: str | None = None,
        **kwargs,
    ):
        super().__init__(ref=ref, event=event, value=value, **kwargs)


class ODKRecordAudio(Action):
    """
    Records audio starting at the triggering event, saves the audio to a file, and writes
    the filename to the node specified in the ref attribute.

    https://getodk.github.io/xforms-spec/#action:recordaudio
    """

    __slots__ = ("quality",)
    name = "odk:recordaudio"

    def __init__(
        self,
        ref: str,
        event: Event,
        value: str | None = None,
        **kwargs,
    ):
        super().__init__(ref=ref, event=event, value=value, **kwargs)
        self.quality: str | None = kwargs.get("odk:quality")

    def node(self):
        result = super().node()
        if self.quality:
            result.setAttribute("odk:quality", self.quality)
        return result


ACTION_CLASSES = {
    "setvalue": Setvalue,
    "odk:setgeopoint": ODKSetGeopoint,
    "odk:recordaudio": ODKRecordAudio,
}


class LibraryMember:
    def __init__(self, name: str, event: str):
        self.name: str = name
        self.event: str = event

    def to_dict(self):
        return {"name": self.name, "event": self.event}


class ActionLibrary(Enum):
    """
    A collection of action/event configs used by pyxform.
    """

    setvalue_first_load = LibraryMember(
        name=Setvalue.name,
        event=Event.ODK_INSTANCE_FIRST_LOAD.value,
    )
    setvalue_new_repeat = LibraryMember(
        name=Setvalue.name,
        event=Event.ODK_NEW_REPEAT.value,
    )
    setvalue_value_changed = LibraryMember(
        name=Setvalue.name,
        event=Event.XFORMS_VALUE_CHANGED.value,
    )
    odk_setgeopoint_first_load = LibraryMember(
        name=ODKSetGeopoint.name,
        event=Event.ODK_INSTANCE_FIRST_LOAD.value,
    )
    odk_setgeopoint_value_changed = LibraryMember(
        name=ODKSetGeopoint.name,
        event=Event.XFORMS_VALUE_CHANGED.value,
    )
    odk_recordaudio_instance_load = LibraryMember(
        name=ODKRecordAudio.name,
        event=Event.ODK_INSTANCE_LOAD.value,
    )

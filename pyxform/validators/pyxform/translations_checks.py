from collections import defaultdict
from typing import TYPE_CHECKING

from pyxform import aliases
from pyxform import constants as const
from pyxform.errors import PyXFormError

if TYPE_CHECKING:
    from collections.abc import Sequence

    SheetData = tuple[tuple[str, ...]]
    Warnings = list[str]


OR_OTHER_WARNING = (
    "This form uses or_other and translations, which is not recommended. "
    "An untranslated input question label and choice label is generated "
    "for 'other'. Learn more: https://xlsform.org/en/#specify-other)."
)


def format_missing_translations_msg(
    _in: "dict[str, dict[str, Sequence]]",
) -> str | None:
    """
    Format the missing translations data into a warning message.

    :param _in: A dict structured as Dict[survey|choices: Dict[language: (columns)]].
      In other words, for the survey or choices sheet, a dict of the language(s) and
      column names for which there are missing translations.
    :return: The warning message, or None if there were no missing columns.
    """

    def get_sheet_msg(name, sheet):
        if sheet is not None:
            langs = sorted(sheet.keys())
            if 0 < len(langs):
                lang_msgs = []
                for lang in langs:
                    cols = sheet[lang]
                    if isinstance(cols, str):
                        msg = f"Expected a sequence of columns, got a string for {lang}."
                        raise PyXFormError(msg)
                    if 1 == len(cols):
                        msg = f"Language '{lang}' is missing the {name} {cols[0]} column."
                        lang_msgs.append(msg)
                    if 1 < len(cols):
                        c = ", ".join(sorted(cols))
                        msg = f"Language '{lang}' is missing the {name} columns {c}."
                        lang_msgs.append(msg)
                return "\n".join(lang_msgs)
        return None

    survey = get_sheet_msg(name=const.SURVEY, sheet=_in.get(const.SURVEY))
    choices = get_sheet_msg(name=const.CHOICES, sheet=_in.get(const.CHOICES))

    messages = tuple(i for i in (survey, choices) if i is not None)
    if 0 == len(messages):
        return None
    return "\n".join(messages)


class Translations:
    """
    Sheet-level container for translations info.

    For each translatable column used in the sheet, there should be a translation for
    each language (including the default / unspecified language) that is used for any
    other translatable column.

    Only the first row is inspected since the checks are concerned with the presence of
    columns, not individual cells. It therefore assumes that each row object has the same
    structure.
    """

    def __init__(
        self,
        sheet_data: "SheetData",
        translatable_columns: dict[str, str],
    ):
        """
        :param sheet_data: The survey or choices sheet data.
        :param translatable_columns: The translatable columns for a sheet. The structure
          should be Dict[internal_name, external_name]. See the aliases module.
        """
        self.seen: defaultdict[str, list[str]] = defaultdict(list)
        self.columns_seen: set[str] = set()
        self.missing: defaultdict[str, list[str]] = defaultdict(list)

        self._find_translations(sheet_data, translatable_columns)
        self._find_missing()

    def _find_translations(
        self, sheet_data: "SheetData", translatable_columns: dict[str, str]
    ):
        def process_header(head):
            if head[0] in translatable_columns.keys():
                name = translatable_columns[head[0]]
                if len(head) == 1:
                    self.seen[const.DEFAULT_LANGUAGE_VALUE].append(name)
                elif len(head) == 2:
                    self.seen[head[1]].append(name)
                self.columns_seen.add(name)

        for header in sheet_data:
            if 1 < len(header) and header[0] in (const.MEDIA, const.BIND):
                process_header(head=header[1:])
            else:
                process_header(head=header)

    def seen_default_only(self) -> bool:
        return 0 == len(self.seen) or (
            const.DEFAULT_LANGUAGE_VALUE in self.seen and 1 == len(self.seen)
        )

    def _find_missing(self):
        if self.seen_default_only():
            return
        for lang, lang_trans in self.seen.items():
            for seen_tran in self.columns_seen:
                if seen_tran not in lang_trans:
                    self.missing[lang].append(seen_tran)


class SheetTranslations:
    """Workbook-level container for translations info, with validation checks."""

    def __init__(
        self,
        survey_sheet: "SheetData",
        choices_sheet: "SheetData",
    ):
        """
        :param survey_sheet: The survey sheet data.
        :param choices_sheet: The choices sheet data.
        """
        self.survey: Translations = Translations(
            sheet_data=survey_sheet,
            translatable_columns=aliases.TRANSLATABLE_SURVEY_COLUMNS,
        )
        self.choices: Translations = Translations(
            sheet_data=choices_sheet,
            translatable_columns=aliases.TRANSLATABLE_CHOICES_COLUMNS,
        )
        self.or_other_seen: bool = False

    def missing_check(self, warnings: "Warnings") -> "Warnings":
        """Add a warning if survey or choices have missing translations."""
        if 0 < len(self.survey.missing) or 0 < len(self.choices.missing):
            msg = format_missing_translations_msg(
                _in={"survey": self.survey.missing, "choices": self.choices.missing}
            )
            if msg is not None:
                warnings.append(msg)
        return warnings

    def or_other_check(self, warnings: "Warnings") -> "Warnings":
        """Add a warning if translations and or_other are present."""
        if self.or_other_seen and (
            not self.survey.seen_default_only() or not self.choices.seen_default_only()
        ):
            warnings.append(OR_OTHER_WARNING)
        return warnings

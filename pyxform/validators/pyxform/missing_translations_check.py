from collections import defaultdict
from typing import TYPE_CHECKING

from pyxform import aliases, constants

if TYPE_CHECKING:
    from typing import Any, Dict, List, Optional, Sequence, Union

    SheetData = List[Dict[str, Union[str, Dict]]]


def format_missing_translations_msg(
    _in: "Dict[str, Dict[str, Sequence]]",
) -> "Optional[str]":
    """
    Format the missing translations data into a warning message.

    :param _in: A dict structured as Dict[survey|choices: Dict[column_name: (languages)]].
      In other words, for the survey or choices sheet, a dict of the column names and
      language(s) for which there are missing translations.
    :return: The warning message, or None if there were no missing columns.
    """

    def get_sheet_msg(name, sheet):
        prefix = "{s} column(s) and language(s): {c}"
        if sheet is not None:
            _keys = sorted(sheet.keys())
            if 0 < len(_keys):
                c = "; ".join((f"'{k}': '" + "', '".join(sheet[k]) + "'" for k in _keys))
                return prefix.format(s=name, c=c)
        return ""

    survey = get_sheet_msg(name=constants.SURVEY, sheet=_in.get(constants.SURVEY))
    choices = get_sheet_msg(name=constants.CHOICES, sheet=_in.get(constants.CHOICES))

    messages = tuple(i for i in (survey, choices) if i != "")
    if 0 == len(messages):
        return None
    return (
        "Missing translation column(s): there is no default_language set, and a "
        "translation column was not found for the {cols_msg}. "
        "To avoid unexpected form behaviour, specify a default_language in the "
        "settings sheet, or add the missing translation columns."
    ).format(cols_msg=" and ".join(messages))


def find_missing_translations(
    sheet_data: "SheetData",
    translatable_columns: "Dict[str, str]",
) -> "Dict[str, List[str]]":
    """
    Find missing translation columns in the sheet data.

    For each translatable column used in the sheet, there should be a translation for
    each language (including the default / unspecified language) that is used for any
    other translatable column.

    This checks the first row only since it is concerned with the presence of columns, not
    individual cells. It therefore assumes that each row object has the same structure.

    :param sheet_data: The survey or choices sheet data.
    :param translatable_columns: The translatable columns for a sheet. The structure
      should be Dict[internal_name, external_name]. See the aliases module.
    :return: Dict[column_name, List[languages]]
    """
    translations_seen = defaultdict(list)
    translation_columns_seen = set()

    def process_cell(typ, cell):
        if cell is not None:
            if typ in translatable_columns.keys():
                name = translatable_columns[typ]
                if isinstance(cell, str):
                    translations_seen[constants.DEFAULT_LANGUAGE_VALUE].append(name)
                    translation_columns_seen.add(name)
                elif isinstance(cell, dict):
                    for lng in cell:
                        translations_seen[lng].append(name)
                        translation_columns_seen.add(name)

    if 0 < len(sheet_data):
        # e.g. ("name", "q1"), ("label", {"en": "Hello", "fr": "Bonjour"})
        for column_type, cell_content in sheet_data[0].items():
            if column_type == constants.MEDIA:
                # e.g. ("audio", {"eng": "my.mp3"})
                for media_type, media_cell in cell_content.items():
                    process_cell(typ=media_type, cell=media_cell)
            if column_type == constants.BIND:
                # e.g. ("jr:constraintMsg", "Try again")
                for bind_type, bind_cell in cell_content.items():
                    process_cell(typ=bind_type, cell=bind_cell)
            else:
                process_cell(typ=column_type, cell=cell_content)

    missing = defaultdict(list)
    for lang, lang_trans in translations_seen.items():
        for seen_tran in translation_columns_seen:
            if seen_tran not in lang_trans:
                missing[seen_tran].append(lang)

    return missing


def missing_translations_check(
    settings: "Dict[str, Any]",
    default_language: str,
    survey_sheet: "SheetData",
    choices_sheet: "SheetData",
    warnings: "List[str]",
):
    """
    Add a warning if there are missing translation columns in the survey or choices data.

    :param settings: The settings sheet data.
    :param default_language: The XLSForm default lanugage setting.
    :param survey_sheet: The survey sheet data.
    :param choices_sheet: The choices sheet data.
    :param warnings: The warnings list, which may be empty.
    :return: The warnings list, possibly with a new message, otherwise unchanged.
    """
    survey_missing_trans = find_missing_translations(
        sheet_data=survey_sheet,
        translatable_columns=aliases.TRANSLATABLE_SURVEY_COLUMNS,
    )
    choices_missing_trans = find_missing_translations(
        sheet_data=choices_sheet,
        translatable_columns=aliases.TRANSLATABLE_CHOICES_COLUMNS,
    )
    if (0 < len(survey_missing_trans) or 0 < len(choices_missing_trans)) and (
        "default_language" not in settings
        or default_language == constants.DEFAULT_LANGUAGE_VALUE
    ):
        msg = format_missing_translations_msg(
            _in={"survey": survey_missing_trans, "choices": choices_missing_trans}
        )
        if msg is not None:
            warnings.append(msg)
    return warnings

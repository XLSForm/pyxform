import re
from functools import lru_cache
from pathlib import Path

LANG_CODE_REGEX = re.compile(r"\((.*)\)$")
HERE = Path(__file__).parent


@lru_cache(maxsize=2)  # Expecting to read 2 files.
def read_tags(file_name: str) -> set[str]:
    path = HERE / file_name
    with open(path, encoding="utf-8") as f:
        return {line.strip() for line in f}


def get_languages_with_bad_tags(languages):
    """
    Returns languages with invalid or missing IANA subtags.
    """
    languages_with_bad_tags = []
    for lang in languages:
        # Minimum matchable lang code attempt requires 3 characters e.g. "a()".
        if lang == "default" or len(lang) < 3:
            continue
        lang_code = LANG_CODE_REGEX.search(lang)
        if not lang_code:
            languages_with_bad_tags.append(lang)
        else:
            lang_match = lang_code.group(1)
            # Check the short list first: 190 short codes vs 7948 long codes.
            if lang_match in read_tags("iana_subtags_2_characters.txt"):
                continue
            elif lang_match in read_tags("iana_subtags_3_or_more_characters.txt"):
                continue
            else:
                languages_with_bad_tags.append(lang)
    return languages_with_bad_tags

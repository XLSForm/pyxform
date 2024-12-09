import re

"""
The IANA tag registry is updated occasionally. Use this script to update pyxform's copy.

Save (don't commit) a local .txt copy of the full tag registry and run this script. The
registry includes definitions for things other than languages, so the regex looks for only
primary language subtags. The tag registry referenced by the XLSForm docs is:
https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry

For further reference see the RFC/BCP: https://datatracker.ietf.org/doc/html/rfc5646
"""


def update():
    with open("language-subtag-registry.txt", encoding="utf-8") as f1:
        matches = re.findall(r"Type: language\nSubtag:\s(.*?)\n", f1.read())

    with open(
        "iana_subtags_2_characters.txt", mode="w", encoding="utf-8", newline="\n"
    ) as f2:
        f2.write("\n".join(i for i in matches if len(i) == 2))

    with open(
        "iana_subtags_3_or_more_characters.txt", mode="w", encoding="utf-8", newline="\n"
    ) as f3:
        f3.write("\n".join(i for i in matches if len(i) > 2))


if __name__ == "__main__":
    update()

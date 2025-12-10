"""
Cleans up error messages from the validators.
"""

import re

ERROR_MESSAGE_REGEX = re.compile(r"(/[a-z0-9\-_]+(?:/[a-z0-9\-_]+)+)", flags=re.I)


class ErrorCleaner:
    """Cleans up raw error messages from XForm validators for end users."""

    @staticmethod
    def _replace_xpath_with_tokens(match):
        strmatch = match.group()
        # eliminate e.g /html/body/select1[@ref=/id_string/elId]/item/value
        # instance('q4')/root/item[...]
        if strmatch.startswith(
            (("/html/body"), ("/root/item"), ("/html/head/model/bind"))
        ) or strmatch.endswith("/item/value"):
            return strmatch
        line = match.group().split("/")
        return f"${{{line[len(line) - 1]}}}"

    @staticmethod
    def _cleanup_errors(error_message):
        error_message = ERROR_MESSAGE_REGEX.sub(
            ErrorCleaner._replace_xpath_with_tokens,
            error_message,
        )
        lines = str(error_message).strip().splitlines()
        no_dupes = [
            line for i, line in enumerate(lines) if line != lines[i - 1] or i == 0
        ]
        return no_dupes

    @staticmethod
    def _remove_java_content(line):
        # has a java filename (with line number)
        has_java_filename = line.find(".java:") != -1
        # starts with '    at java class path or method path'
        is_a_java_method = line.find("\tat") != -1
        if not has_java_filename and not is_a_java_method:
            # remove java.lang.RuntimeException
            if line.startswith("java.lang.RuntimeException: "):
                line = line.replace("java.lang.RuntimeException: ", "")
            # remove org.javarosa.xpath.XPathUnhandledException
            if line.startswith("org.javarosa.xpath.XPathUnhandledException: "):
                line = line.replace("org.javarosa.xpath.XPathUnhandledException: ", "")
            # remove java.lang.NullPointerException
            if line.startswith("java.lang.NullPointerException"):
                line = line.replace("java.lang.NullPointerException", "")
            if line.startswith("org.javarosa.xform.parse.XFormParseException"):
                line = line.replace("org.javarosa.xform.parse.XFormParseException", "")
            return line

    @staticmethod
    def _join_final(error_messages):
        return "\n".join(line for line in error_messages if line is not None)

    @staticmethod
    def _improve_selected_error_message(error_message: str) -> str:
        """
        Improve misleading error message for selected() function type mismatches.
        
        ODK Validate reports "The second parameter to the selected() function must be
        in quotes" for type mismatches, which is misleading because non-literal
        expressions can be valid. This method detects type mismatch errors and
        replaces them with a clearer message.
        """
        # Check if this is a type mismatch error (not just a syntax error)
        is_type_mismatch = (
            "XPathTypeMismatchException" in error_message
            or "type mismatch" in error_message.lower()
        )
        
        # Check if the misleading message is present and relates to selected()
        misleading_pattern = (
            r"The second parameter to the selected\(\) function must be in quotes"
        )
        
        if is_type_mismatch and re.search(misleading_pattern, error_message, re.IGNORECASE):
            # Replace with clearer message that explains it's a type/expression issue
            improved_message = (
                "The second parameter to the selected() function has an invalid type or "
                "expression. The parameter must evaluate to a string value, but the "
                "provided expression does not return a compatible type."
            )
            # Replace the misleading message (may include text like "(like '1')")
            error_message = re.sub(
                misleading_pattern + r"(?: \(like '[^']+'\))?",
                improved_message,
                error_message,
                flags=re.IGNORECASE,
            )
        
        return error_message

    @staticmethod
    def odk_validate(error_message):
        if "Error: Unable to access jarfile" in error_message:
            return error_message  # Avoids tokenising the file path.
        
        # Improve selected() error messages before cleanup
        error_message = ErrorCleaner._improve_selected_error_message(error_message)
        
        common = ErrorCleaner._cleanup_errors(error_message)
        java_clean = [ErrorCleaner._remove_java_content(i) for i in common]
        final_message = ErrorCleaner._join_final(java_clean)
        return final_message

    @staticmethod
    def enketo_validate(error_message):
        common = ErrorCleaner._cleanup_errors(error_message)
        final_message = ErrorCleaner._join_final(common)
        return final_message

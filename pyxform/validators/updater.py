from __future__ import print_function
import argparse
from datetime import datetime
import json
import os
from zipfile import ZipFile
from pyxform.errors import PyXFormError
from pyxform.validators.util import request_get


HERE = os.path.abspath(os.path.dirname(__file__))
UTC_FMT = "%Y-%m-%dT%H:%M:%SZ"


class Updater(object):

    def __init__(self, api_url, repo_url, validate_subfolder):
        self.api_url = api_url
        self.repo_url = repo_url
        self.validate_subfolder = validate_subfolder

        self.mod_path = os.path.join(HERE, self.validate_subfolder)
        self.latest_path = os.path.join(self.mod_path, "latest.json")
        self.last_check_path = os.path.join(self.mod_path, ".last_check")

        self.bin_path = os.path.join(self.mod_path, "bin")
        self.installed_path = os.path.join(self.bin_path, "installed.json")

        self.manual_msg = "Download manually from: {r}.".format(r=self.repo_url)
        self.xform_path = self._get_xform_path()

    @staticmethod
    def _get_xform_path():
        """
        Get the path to the XLSForm spec test XML file for checking updates.
        """
        loop_count = 0
        folder = HERE
        while not os.path.exists(os.path.join(folder, ".gitignore")):
            folder = os.path.dirname(folder)
            if 5 < loop_count:
                raise PyXFormError("Couldn't find project root. Current: {f}"
                                   "".format(f=folder))
            loop_count += 1
        return os.path.join(folder, "pyxform", "tests", "test_expected_output",
                            "xlsform_spec_test.xml")

    @staticmethod
    def _request_latest_json(url):
        """
        Get the GitHub API JSON response doc for the latest release from URL.
        """
        content = request_get(url=url)
        return json.loads(content.decode("utf-8"))

    @staticmethod
    def _read_json(file_path):
        """
        Read the JSON file to a string.
        """
        if not os.path.exists(file_path):
            raise PyXFormError("Expected JSON file does not exist: {p}"
                               "".format(p=file_path))
        with open(file_path, mode="r") as in_file:
            return json.load(in_file)

    @staticmethod
    def _write_json(file_path, content):
        """
        Save the JSON data to a file.
        """
        with open(file_path, mode="w") as out_file:
            json.dump(content, out_file, indent=2, sort_keys=True)

    @staticmethod
    def _read_last_check(file_path):
        """
        Read the .last_check file.
        """
        with open(file_path, mode="r") as in_file:
            first_line = in_file.readline()
        try:
            last_check = datetime.strptime(first_line, UTC_FMT)
        except ValueError:
            return None
        else:
            return last_check

    @staticmethod
    def _write_last_check(file_path, content):
        """
        Write the .last_check file.
        """
        with open(file_path, mode="w") as out_file:
            out_file.write(content.strftime(UTC_FMT))

    def _check_necessary(self, utc_now):
        """
        Determine whether a check for the latest version is necessary.
        """
        if not os.path.exists(self.last_check_path):
            return True
        elif not os.path.exists(self.latest_path):
            return True
        else:
            last_check = self._read_last_check(file_path=self.last_check_path)
            if last_check is None:
                return True
            age = utc_now - last_check
            thirty_minutes = 1800
            if thirty_minutes < age.seconds:
                return True
            else:
                return False

    def _get_latest(self):
        """
        Get the latest release info, either from GitHub or a recent file copy.
        """
        utc_now = datetime.utcnow()
        if self._check_necessary(utc_now=utc_now):
            latest = self._request_latest_json(url=self.api_url)
            self._write_json(file_path=self.latest_path, content=latest)
            self._write_last_check(
                file_path=self.last_check_path, content=utc_now)
        else:
            latest = self._read_json(file_path=self.latest_path)
        return latest

    @staticmethod
    def _get_release_message(json_data):
        template = "- Tag name = {tag_name}\n" \
                   "- Tag URL = {tag_url}\n\n"
        return template.format(
            tag_name=json_data["tag_name"],
            tag_url=json_data["html_url"])

    def list(self):
        """
        List the current and latest release info, and latest available files.
        """
        latest = self._get_latest()
        latest_files = latest["assets"]
        if len(latest_files) == 0:
            file_message = "- None!\n\n{m}".format(m=self.manual_msg)
        else:
            file_names = ["- {n}".format(n=x["name"]) for x in latest_files]
            file_message = "\n".join(file_names)
        installed = self._read_json(file_path=self.installed_path)

        template = "\nCurrently installed:\n\n{installed}" \
                   "Latest release:\n\n{latest}" \
                   "Files available for latest release:\n\n{file_message}\n"
        message = template.format(
            installed=self._get_release_message(json_data=installed),
            latest=self._get_release_message(json_data=latest),
            file_message=file_message
        )
        print(message)

    def _find_download_url(self, json_data, file_name):
        """
        Find the download URL for the file in the GitHub API JSON response doc.
        """
        rel_name = json_data["name"]
        files = json_data["assets"]

        if len(files) == 0:
            raise PyXFormError(
                "No files attached to release '{r}'. {h}"
                "".format(r=rel_name, h=self.manual_msg))

        file_urls = [x["browser_download_url"] for x in files
                     if x["name"] == file_name]

        urls_len = len(file_urls)
        if 0 == urls_len:
            raise PyXFormError(
                "No files with the name '{n}' attached to release '{r}'. {h}"
                "".format(n=file_name, r=rel_name, h=self.manual_msg))
        elif 1 < urls_len:
            raise PyXFormError(
                "{c} files with the name '{n}' attached to release '{r}'. {h}"
                "".format(c=urls_len, n=file_name, r=rel_name,
                          h=self.manual_msg))

        return file_urls[0]

    @staticmethod
    def _download_file(url, file_path):
        """
        Save response content from the URL to a binary file at the file path.
        """
        with open(file_path, mode='wb') as out_file:
            file_data = request_get(url=url)
            out_file.write(file_data)

    @staticmethod
    def _unzip(file_path, out_path):
        """
        Unzip the contents of a zip file to an existing output path.
        """
        if not os.path.exists(file_path):
            raise PyXFormError(
                "Zip file not found. Expected at: '{p}'".format(p=file_path))
        if not os.path.exists(out_path):
            raise PyXFormError(
                "Output path not found. Expected at: '{p}'".format(p=out_path))
        with ZipFile(file_path, mode="r") as zip_file:
            test = zip_file.testzip()
            if test is not None:
                raise PyXFormError(
                    "Zip file contains at least one bad file. First bad file: "
                    "'{f}'. Try a manual download.".format(f=test))
            zip_file.extractall(path=out_path)

    def update(self, file_name, force):
        latest = self._get_latest()
        installed = self._read_json(file_path=self.installed_path)
        file_path = os.path.join(self.bin_path, file_name)

        if installed["tag_name"] == latest["tag_name"] and not force:
            template = "\nUpdate failed!\n\n" \
                       "The current version appears to be the latest.\n\n" \
                       "To update anyway, use the '--force' flag.\n\n" \
                       "Currently installed:\n\n{installed}"
            message = template.format(
                installed=self._get_release_message(json_data=installed))
            print(message)
        else:
            try:
                url = self._find_download_url(
                    json_data=latest, file_name=file_name)
                self._download_file(url=url, file_path=file_path)
                if file_name.endswith(".zip"):
                    self._unzip(file_path=file_path, out_path=self.bin_path)
            except Exception as e:
                print("\n\nUpdate failed!\n\n")
                raise e

        # TODO: use self.xform_path to check it went OK, otherwise revert to old


class EnketoValidateUpdater(Updater):

    def __init__(self):
        super(EnketoValidateUpdater, self).__init__(
            api_url="https://api.github.com/repos/enketo/enketo-validate/"
                    "releases/latest",
            repo_url="https://github.com/enketo/enketo-validate",
            validate_subfolder="enketo_validate"
        )


class ODKValidateUpdater(Updater):

    def __init__(self):
        super(ODKValidateUpdater, self).__init__(
            api_url="https://api.github.com/repos/opendatakit/validate/"
                    "releases/latest",
            repo_url="https://github.com/opendatakit/validate",
            validate_subfolder="odk_validate"
        )


def _build_validator_menu(main_subparser, validator_name, updater_instance):

    main = main_subparser.add_parser(
        validator_name.lower(),
        description="{v} Sub-menu".format(v=validator_name),
        help="For help, use '{v} -h'.".format(v=validator_name.lower())
    )
    subs = main.add_subparsers(metavar="<sub_command>")

    cmd_list = subs.add_parser(
        "list",
        help="List available files for the latest release."
    )
    cmd_list.set_defaults(command=updater_instance.list)

    cmd_update = subs.add_parser(
        "update",
        help="Update the validator to the latest version."
    )
    cmd_update.set_defaults(command=updater_instance.update)
    cmd_update.add_argument(
        "file_name",
        help="Name of the release file to use for updating."
    )
    cmd_update.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="If the current version appears to be the latest, update anyway."
    )
    return main


def _create_parser():
    """
    Parse command line arguments.
    """
    main_title = "pyxform validator updater"
    epilog = \
        "------------------------------------------------------\n" \
        "Use this tool to update external validators.\n\n" \
        "Example usage:\n\n" \
        "updater.py enketo list\n" \
        "updater.py enketo update linux.zip\n\n" \
        "First, use the 'list' sub-command for the validator\n" \
        "to check for a new release and to show what (if any) \n" \
        "files are attached to it.\n\n" \
        "Second, use the 'update' sub-command for the validator\n" \
        "to apply the update, specifying the file to use.\n" \
        "------------------------------------------------------"
    main_parser = argparse.ArgumentParser(
        description=main_title,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub_parsers = main_parser.add_subparsers(metavar="<sub_menu>")
    _build_validator_menu(
        main_subparser=sub_parsers,
        validator_name="Enketo",
        updater_instance=EnketoValidateUpdater()
    )
    _build_validator_menu(
        main_subparser=sub_parsers,
        validator_name="ODK",
        updater_instance=ODKValidateUpdater()
    )
    return main_parser


def main_cli():
    parser = _create_parser()
    args = parser.parse_args()
    kwargs = args.__dict__.copy()
    del kwargs["command"]
    args.command(**kwargs)


if __name__ == '__main__':
    main_cli()

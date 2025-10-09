import logging
import requests
import os
import json
from datetime import datetime, date
from importlib.metadata import version, PackageNotFoundError

from terralab.config import load_config

package_name = "terralab-cli"

LOGGER = logging.getLogger(__name__)


def get_version_info_file_path() -> str:
    """Get the path to the version info file for storing the last version check date."""
    config = load_config()
    version_info_file_path = config.version_info_file
    os.makedirs(os.path.dirname(version_info_file_path), exist_ok=True)
    return version_info_file_path


def get_last_version_check_date() -> date | None:
    """Get the date when the latest version was last checked."""
    info_file = get_version_info_file_path()
    try:
        if os.path.exists(info_file):
            with open(info_file, "r") as f:
                data = json.load(f)
                return datetime.strptime(
                    data.get("last_version_check", ""), "%Y-%m-%d"
                ).date()
    except (ValueError, KeyError):
        # Delete the potentially corrupted file
        try:
            os.remove(info_file)
        except OSError:
            LOGGER.debug(
                "Version info file is unreadable and could not be automatically cleaned up"
            )
    return None


def update_last_version_check_date() -> None:
    """Update the version check field with today's date."""
    info_file = get_version_info_file_path()
    data = {"last_version_check": date.today().strftime("%Y-%m-%d")}
    try:
        with open(info_file, "w") as f:
            json.dump(data, f)
    except IOError:
        # Silently fail if we can't write to the info file
        LOGGER.debug("Failed to write to version info file")


def check_version() -> None:
    """Check for new version and show warning only once per day."""
    last_version_check = get_last_version_check_date()
    today = date.today()

    if last_version_check == today:
        LOGGER.debug(
            f"Skipping version check: last version check: {last_version_check}, today: {today}"
        )
        return

    try:
        installed_version = version(package_name)
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=5)
        response.raise_for_status()
        latest_version = response.json()["info"]["version"]

        LOGGER.debug(
            f"Installed version: {installed_version}, Latest version: {latest_version}"
        )

        if installed_version < latest_version:
            LOGGER.warning(
                f"A new version of {package_name} ({latest_version}) is available. You are using {installed_version}. Please update to the latest version to get the latest features and ensure continued compatibility."
            )
            update_last_version_check_date()
    except (requests.exceptions.RequestException, PackageNotFoundError) as e:
        # Silently fail - we don't want to bother the user in this case
        LOGGER.debug(f"Version check failed: {e}")

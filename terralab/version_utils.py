import logging
import requests
import os
import json
from datetime import datetime, date
from importlib.metadata import version, PackageNotFoundError

package_name = "terralab-cli"

LOGGER = logging.getLogger(__name__)


def get_version_check_file_path() -> str:
    """Get the path to the cache file for storing the last warning date."""
    cache_dir = os.path.expanduser("~/.terralab")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, "version_check.json")


def get_last_version_check_date() -> date | None:
    """Get the date when the latest version was last checked."""
    cache_file = get_version_check_file_path()
    try:
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                data = json.load(f)
                return datetime.strptime(
                    data.get("last_version_check", ""), "%Y-%m-%d"
                ).date()
    except (json.JSONDecodeError, ValueError, KeyError):
        pass
    return None


def update_last_version_check_date() -> None:
    """Update the version check file with today's date."""
    cache_file = get_version_check_file_path()
    data = {"last_version_check": date.today().strftime("%Y-%m-%d")}
    try:
        with open(cache_file, "w") as f:
            json.dump(data, f)
    except IOError:
        # Silently fail if we can't write to the cache file
        LOGGER.debug("Failed to write to version check file")
        pass


def check_version_once_per_day() -> None:
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

        print(  # Debug line to show versions being compared
            f"Installed version: {installed_version}, Latest version: {latest_version}"
        )

        if installed_version < latest_version:
            print(
                f"A new version of {package_name} ({latest_version}) is available. You are using {installed_version}."
            )
            update_last_version_check_date()
    except (requests.exceptions.RequestException, PackageNotFoundError) as e:
        # Silently fail - we don't want to bother the user in this case
        LOGGER.debug(f"Version check failed: {e}")
        pass

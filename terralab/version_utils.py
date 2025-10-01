import requests
import os
import json
from datetime import datetime, date
from importlib.metadata import version, PackageNotFoundError

package_name = 'terralab-cli'

def get_cache_file_path():
    """Get the path to the cache file for storing the last warning date."""
    cache_dir = os.path.expanduser("~/.terralab")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, "version_check_cache.json")

def get_last_warning_date():
    """Get the date when the version warning was last shown."""
    cache_file = get_cache_file_path()
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                data = json.load(f)
                return datetime.strptime(data.get('last_warning_date', ''), '%Y-%m-%d').date()
    except (json.JSONDecodeError, ValueError, KeyError):
        pass
    return None

def update_last_warning_date():
    """Update the cache file with today's date."""
    cache_file = get_cache_file_path()
    data = {'last_warning_date': date.today().strftime('%Y-%m-%d')}
    try:
        with open(cache_file, 'w') as f:
            json.dump(data, f)
    except IOError:
        # Silently fail if we can't write to cache file
        pass

def check_version_once_per_day():
    """Check for new version and show warning only once per day."""
    # Check if we already showed the warning today
    last_warning_date = get_last_warning_date()
    today = date.today()

    if last_warning_date == today:
        return  # Already showed warning today

    try:
        installed_version = version(package_name)
        response = requests.get(f'https://pypi.org/pypi/{package_name}/json', timeout=5)
        response.raise_for_status()
        latest_version = response.json()['info']['version']

        if installed_version < latest_version:
            print(f"WARNING: A new version of {package_name} ({latest_version}) is available. You are using {installed_version}.")
            update_last_warning_date()
    except (requests.exceptions.RequestException, PackageNotFoundError) as e:
        # Silently fail - don't show error messages for version checks
        pass

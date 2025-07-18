import requests
import sys
import os
import hashlib
from version import __version__
from packaging import version

def check_for_updates():
    try:
        response = requests.get(
            "https://api.github.com/repos/Kalicorn-Foundation/viome-chat-frontend/releases/latest",
            timeout=5
        )
        response.raise_for_status()
        latest_version = response.json()["tag_name"].lstrip('v')
        assets = response.json()["assets"]
        if version.parse(latest_version) > version.parse(__version__):
            print(f"New version available: {latest_version}")
            exe_asset = next(a for a in assets if a["name"] == "chrome.exe")
            download_url = exe_asset["browser_download_url"]
            new_exe = requests.get(download_url).content
            # Optional: checksum verification
            checksum_url = download_url + ".sha256"
            checksum_resp = requests.get(checksum_url)
            expected_checksum = checksum_resp.text.strip() if checksum_resp.ok else None
            actual_checksum = hashlib.sha256(new_exe).hexdigest()
            if expected_checksum and expected_checksum != actual_checksum:
                raise Exception("Checksum mismatch")
            temp_path = os.path.join(os.path.dirname(sys.executable), "chrome_new.exe")
            with open(temp_path, "wb") as f:
                f.write(new_exe)
            updater_script = f"""
import time
import os
import sys
time.sleep(1)
os.remove(r"{sys.executable}")
os.rename(r"{temp_path}", r"{sys.executable}")
os.startfile(r"{sys.executable}")
"""
            with open("updater.py", "w") as f:
                f.write(updater_script)
            os.system(f"start python updater.py")
            sys.exit(0)
    except Exception as e:
        print(f"Update check failed: {e}")

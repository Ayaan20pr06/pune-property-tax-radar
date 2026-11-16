"""Clone the published Pune wards repository without a pasted terminal URL."""
import subprocess
from pathlib import Path
target=Path("data/raw/pune_wards")
if target.exists(): raise SystemExit("Already exists: data/raw/pune_wards")
subprocess.run(["git","clone","https://github.com/datameet/Pune_wards",str(target)],check=True)
print("Cloned to",target)

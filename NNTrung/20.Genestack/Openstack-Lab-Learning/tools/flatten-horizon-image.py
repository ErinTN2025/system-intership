#!/usr/bin/env python3
"""Export/import Horizon filesystem; preserve runtime metadata needed by the chart."""
import json
from pathlib import Path
import subprocess
import sys
import tarfile

if len(sys.argv) != 4:
    raise SystemExit("Usage: flatten-horizon-image.py SOURCE_IMAGE TARGET_IMAGE WORK_DIR")
base, target, directory = sys.argv[1:]
if base == target:
    raise SystemExit("Source and target must be different")
root = Path(directory).expanduser()
root.mkdir(parents=True, exist_ok=True)
archive = root / "rootfs.tar"

def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()

config = json.loads(run(["docker", "image", "inspect", base]))[0]["Config"]
container = run(["docker", "create", "--entrypoint", "/bin/true", base])
try:
    subprocess.run(["docker", "export", "--output", str(archive), container], check=True)
finally:
    subprocess.run(["docker", "rm", container], check=True)

with tarfile.open(archive) as package:
    for name in [
        "etc/passwd", "etc/group", "etc/apache2/envvars", "usr/sbin/a2enmod",
        "var/lib/openstack/lib/python3.12/site-packages/pymysql/__init__.py",
    ]:
        entry = package.getmember(name)
        if entry.size <= 0:
            raise SystemExit("Empty source file: " + name)
        print(name, "bytes=", entry.size)

args = ["docker", "import", "--platform", "linux/amd64", "--change", "USER 0:0"]
for item in config.get("Env") or []:
    key, value = item.split("=", 1)
    args += ["--change", "ENV " + key + "=" + json.dumps(value)]
if config.get("WorkingDir"):
    args += ["--change", "WORKDIR " + config["WorkingDir"]]
for key in ["Entrypoint", "Cmd"]:
    if config.get(key):
        args += ["--change", key.upper() + " " + json.dumps(config[key])]
if config.get("StopSignal"):
    args += ["--change", "STOPSIGNAL " + config["StopSignal"]]
args += [str(archive), target]
subprocess.run(args, check=True)
subprocess.run([
    "docker", "run", "--rm", "--entrypoint", "/var/lib/openstack/bin/python3", target,
    "-c", 'import pwd, pymysql; from importlib.metadata import version; '
          'assert pwd.getpwnam("horizon"); '
          'assert hasattr(pymysql, "install_as_MySQLdb"); '
          'print("Horizon:", version("horizon")); '
          'print("Octavia Dashboard:", version("octavia-dashboard"))'
], check=True)
print("Local image ready:", target)
print("Temporary filesystem archive:", archive)

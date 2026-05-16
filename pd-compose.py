#!/data/data/com.termux/files/usr/bin/python3


import argparse
import subprocess
import sys
from pathlib import Path

import yaml


def main():
    parser = argparse.ArgumentParser(description="pd-compose: proot-distro compose tool")
    parser.add_argument("command", choices=["up", "down", "ps"])
    args = parser.parse_args()

    config_path = Path("pd-compose.yaml")
    if not config_path.exists():
        print("error: pd-compose.yaml not found")
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    services = config.get("services", {})

    if args.command == "up":
        for name, svc in services.items():
            image = svc.get("image", "ubuntu")
            print(f"Installing {name} from {image}...")
            subprocess.run(["proot-distro", "install", "--name", name, image])

            login_args = ["proot-distro", "login", name]
            for bind in svc.get("binds", []):
                login_args += ["--bind", bind]
            env_vars = svc.get("environment", {})
            for k, v in env_vars.items():
                login_args += ["--env", f"{k}={v}"]

            print(f"Starting {name}...")
            print(" ".join(login_args))

    elif args.command == "down":
        for name in services:
            print(f"Removing {name}...")
            subprocess.run(["proot-distro", "remove", name])

    elif args.command == "ps":
        subprocess.run(["proot-distro", "list"])


if __name__ == "__main__":
    main()

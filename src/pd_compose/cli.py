#!/data/data/com.termux/files/usr/bin/python3

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import typer
import yaml

app = typer.Typer(help="pd-compose: proot-distro compose tool")

PID_DIR = Path.home() / ".local" / "share" / "pd-compose"
PID_DIR.mkdir(parents=True, exist_ok=True)


def load_config(file: Path) -> dict:
    if not file.exists():
        typer.echo(f"error: {file} not found", err=True)
        raise typer.Exit(1)
    with open(file) as f:
        return yaml.safe_load(f) or {}


def get_login_args(name: str, svc: dict, use_run: bool = False) -> list[str]:
    args = ["proot-distro"]
    if use_run:
        args.append("run")
    else:
        args.append("login")
    args.append(name)

    for bind in svc.get("binds", []):
        args += ["--bind", bind]

    for k, v in svc.get("environment", {}).items():
        args += ["--env", f"{k}={v}"]

    args.append("--no-kill-on-exit")
    return args


def get_run_command(svc: dict) -> list[str] | None:
    if svc.get("command"):
        cmd = svc["command"]
        if isinstance(cmd, str):
            return cmd.split()
        return cmd
    return None


def run_detached(name: str, args: list[str]) -> int:
    log_file = PID_DIR / f"{name}.log"
    pid_file = PID_DIR / f"{name}.pid"

    with open(log_file, "a") as log:
        process = subprocess.Popen(
            args,
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )

    pid_file.write_text(str(process.pid))
    return process.pid


def stop_detached(name: str) -> bool:
    pid_file = PID_DIR / f"{name}.pid"
    if not pid_file.exists():
        return False

    pid = int(pid_file.read_text().strip())
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(1)
        os.kill(pid, 0)
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    finally:
        pid_file.unlink(missing_ok=True)
    return True


def get_detached_services() -> list[tuple[str, int]]:
    services = []
    for pid_file in PID_DIR.glob("*.pid"):
        name = pid_file.stem
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)
            services.append((name, pid))
        except (ProcessLookupError, ValueError):
            pid_file.unlink(missing_ok=True)
    return services


@app.command()
def up(
    file: Path = typer.Option("pd-compose.yaml", "--file", "-f", help="Config file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print commands without running"),
    detach: bool = typer.Option(False, "--detach", "-d", help="Run containers in background"),
):
    """Install and run containers defined in pd-compose.yaml"""
    config = load_config(file)

    for name, svc in config.get("services", {}).items():
        image = svc.get("image", "ubuntu")
        typer.echo(f"Installing {name} from {image}...")
        if not dry_run:
            subprocess.run(["proot-distro", "install", "--name", name, image])

        command = get_run_command(svc)
        use_run = command is None

        login_args = get_login_args(name, svc, use_run)

        if command:
            login_args += ["--"] + command

        if detach:
            if dry_run:
                typer.echo(f"[dry-run] Would start {name} in background: {' '.join(login_args)}")
            else:
                pid = run_detached(name, login_args)
                typer.echo(f"Started {name} in background (PID: {pid})")
        else:
            typer.echo(" ".join(login_args))
            if not dry_run:
                subprocess.run(login_args)


@app.command()
def down(
    file: Path = typer.Option("pd-compose.yaml", "--file", "-f", help="Config file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print commands without running"),
    all: bool = typer.Option(False, "--all", "-a", help="Stop all running detached containers"),
):
    """Remove containers or stop detached processes"""
    if all:
        stopped = 0
        for pid_file in PID_DIR.glob("*.pid"):
            name = pid_file.stem
            if dry_run:
                typer.echo(f"[dry-run] Would stop {name}")
            else:
                if stop_detached(name):
                    typer.echo(f"Stopped {name}")
                    stopped += 1
        if stopped == 0 and not dry_run:
            typer.echo("No detached containers running")
        return

    config = load_config(file)
    for name in config.get("services", {}):
        pid_file = PID_DIR / f"{name}.pid"
        if pid_file.exists() and not dry_run:
            stop_detached(name)

        typer.echo(f"Removing {name}...")
        if not dry_run:
            subprocess.run(["proot-distro", "remove", name])


@app.command()
def ps(
    all: bool = typer.Option(False, "--all", "-a", help="Show all including stopped detached"),
):
    """List installed containers and detached processes"""
    typer.echo("=== Installed containers ===")
    subprocess.run(["proot-distro", "list"])

    typer.echo("\n=== Detached processes ===")
    running = 0
    for pid_file in PID_DIR.glob("*.pid"):
        name = pid_file.stem
        pid = int(pid_file.read_text().strip())
        try:
            os.kill(pid, 0)
            log_file = PID_DIR / f"{name}.log"
            typer.echo(f"  {name} (PID: {pid}, log: {log_file})")
            running += 1
        except ProcessLookupError:
            if all:
                typer.echo(f"  {name} (stopped)")
            pid_file.unlink(missing_ok=True)

    if running == 0 and not all:
        typer.echo("  (none running)")


@app.command()
def logs(
    name: str = typer.Argument(..., help="Container name"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    tail: int = typer.Option(50, "--tail", "-n", help="Number of lines to show"),
):
    """Show logs of a detached container"""
    log_file = PID_DIR / f"{name}.log"
    if not log_file.exists():
        typer.echo(f"error: no logs found for {name}", err=True)
        raise typer.Exit(1)

    if follow:
        subprocess.run(["tail", "-f", str(log_file)])
    else:
        subprocess.run(["tail", "-n", str(tail), str(log_file)])


if __name__ == "__main__":
    app()
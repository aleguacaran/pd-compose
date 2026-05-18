# pd-compose

**pd-compose** is a minimal compose-like tool for [proot-distro](https://github.com/termux/proot-distro). It reads a `pd-compose.yaml` to install, start, and stop proot-distro containers — inspired by Docker Compose.

## Usage

Define services in `pd-compose.yaml`:

```yaml
services:
  ubuntu-vm:
    image: ubuntu:24.04
    binds:
      - /host/path:/container/path
    environment:
      DEBIAN_FRONTEND: noninteractive
    command: nginx  # optional: command to run
```

Run:

```bash
pd-compose up                    # install and run containers interactively
pd-compose up -d                 # run containers in background (detached)
pd-compose ps                    # list installed containers and detached processes
pd-compose ps -a                 # show all including stopped detached
pd-compose logs <name>           # view logs of detached container
pd-compose logs <name> -f         # follow logs
pd-compose down                  # stop detached and remove containers
pd-compose down -a                # stop all detached containers
```

## Commands

- **up**: Install and run containers. Use `-d` for detached mode (background).
- **down**: Stop detached processes and remove containers. Use `-a` to stop all detached.
- **ps**: List installed containers and running detached processes.
- **logs**: View logs of a detached container. Use `-f` to follow, `-n N` for tail.

## Architecture

- Uses `proot-distro run` for images with Entrypoint/Cmd (server images)
- Uses `proot-distro login -- <command>` for services with explicit `command`
- PID files stored in `~/.local/share/pd-compose/`
- Log files stored in `~/.local/share/pd-compose/<name>.log`

## Credits

- Built on top of [proot-distro](https://github.com/termux/proot-distro) by Termux.
- Inspired by [Docker Compose](https://github.com/docker/compose).
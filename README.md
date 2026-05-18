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
```

Run:

```
pd-compose.py up    # install and show login command
pd-compose.py ps    # list installed containers
pd-compose.py down  # remove all containers
```

## Credits

- Built on top of [proot-distro](https://github.com/termux/proot-distro) by Termux.
- Inspired by [Docker Compose](https://github.com/docker/compose).

# Docker

## What it is

A **container** is a running program packaged with everything it needs (its libraries and a minimal file system) and isolated from the rest of the computer. **Docker** is the tool that builds and runs containers. A container is not a full virtual machine: it shares the computer's operating-system kernel and only isolates processes, files, users and networks, which is why it starts in a second.

An **image** is the read-only package a container starts from; a **registry** (such as Docker Hub) stores images by name and tag (`python:3.12.8-slim-bookworm`). A **volume** is storage that lives outside any one container.

## Why this repository uses it

Two jobs: run a service in a form that works the same on any computer (the Dockerfile) and run services that the project depends on without installing them (PostgreSQL with pgvector, in `ai-cited-answers`). The default `make run` path needs no Docker at all; Docker is used for `make up` in the database repository, and for the optional image checks.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Dockerfile` | builds the service image (see `dockerfile.md`) |
| `docker-compose.yml` | runs services together (see `docker-compose.md`) |
| `Makefile` | targets that call Docker:  |
| `.github/workflows/ci.yml` | CI starts the database as a service container |

## How it works underneath

**Isolation is made of Linux features.** *Namespaces* give a process its own view of process ids, network interfaces, mount points and host name. *Control groups* (cgroups) limit memory and CPU. A *union file system* stacks the image layers read-only and adds a thin writable layer for the container. On macOS and Windows, Docker Desktop runs a small Linux virtual machine to provide these features; the disk of that VM is a single large file (`Docker.raw`), which is why a full VM disk makes every Docker command fail.

**The engine and the client.** The `docker` command is a client that talks to the Docker engine (a background service, the *daemon*) over a socket. If the engine is not running, commands that need it fail with "Cannot connect to the Docker daemon", while commands that only read files (`docker compose config`) still work.

**Ports.** A container has its own network. `-p 8080:8080` (or the compose `ports:`) asks the engine to forward a port on the machine to a port in the container.

**State.** A container's own file system is thrown away with the container. Data that must survive goes in a volume.

## Walkthrough of this repository's use

How this repository uses Docker, in order:

- **Build**: `docker compose --profile api up -d --build --wait` or `docker compose up --build --detach --wait` builds the image from the `Dockerfile` and starts it.
- **Run a dependency**: `docker compose up -d --wait db` starts only the database.
- **Run a command inside a running container**: `docker compose exec -T db psql ...` (the `-T` means no interactive terminal, so SQL can be piped in).
- **Stop and clean**: `docker compose down -v` removes containers, the network and volumes.

The details of each file are in `dockerfile.md` and `docker-compose.md`.

**Status when this note was written.** While these notes were being written, the machine's Docker engine could not run containers (the engine's disk was full), so every command marked "not run" was left unexecuted and no image was built for this note. What was checked instead: the compose file parses (`docker compose config`), and the service code was tested outside Docker, as real processes, in the test suite. The README's "Verification notes" section lists the Docker checks that are still pending and the exact command for each.

## Try it yourself

1. The Docker client version.

```bash
docker --version
```

What you should see (captured from this repository):

```text
Docker version 24.0.6, build ed223bc
```

2. The Compose plug-in version.

```bash
docker compose version
```

What you should see (captured from this repository):

```text
Docker Compose version v2.23.0-desktop.1
```

3. Ask the engine about itself. Not run here; with the engine down it prints "Cannot connect to the Docker daemon".

```bash
docker info
```

4. List running containers.

```bash
docker ps
```

5. List images on this machine.

```bash
docker images
```

## Mistakes people make

- **Thinking a container is a VM.** It shares the host kernel; it isolates processes, not hardware.
- **Storing data inside a container.** It vanishes with the container; use a volume.
- **Running as root inside.** `USER app` in the Dockerfile avoids that.
- **Pulling `latest`.** Tags are pinned so builds repeat.
- **Leaving the engine's disk full.** Every Docker command then fails; prune old images and volumes.

## Check yourself

1. What is the difference between an image and a container?

   *Answer:* An image is the read-only package; a container is a running copy of it.

2. Does `docker compose config` need the engine?

   *Answer:* No; it only reads and validates files.

3. What makes containers lighter than virtual machines?

   *Answer:* They share the host's kernel.

4. Where should a container keep data that must survive?

   *Answer:* In a volume.

5. Why does `make down` for the database repository use `-v`?

   *Answer:* To delete the database volume and start clean.

## Further reading

- Docker documentation, https://docs.docker.com/ (Docker 24.0.6 client and Compose v2.23 are installed on the machine where this was written; containers could not be run there, see the status note above).

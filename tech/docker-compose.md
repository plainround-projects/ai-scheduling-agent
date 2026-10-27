# Docker Compose

## What it is

**Docker Compose** describes and runs a set of related containers with one file and one command. Instead of typing a long `docker run` with ports, volumes and variables for each container, you write them once in `docker-compose.yml` (a YAML file, see `yaml.md`) and run `docker compose up`. The file defines **services** (the containers), **volumes** (storage that outlives containers) and the **network** the containers share (created automatically).

## Why this repository uses it

It turns "start the database, wait until it is ready, then start the service" into a declared fact with a health check and a dependency, instead of a README paragraph. The file also records the exact image, the ports and the credentials of the local setup, so a new machine reproduces it.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `docker-compose.yml` | the whole file |
| `Makefile` | the targets that call `docker compose` |
| `Dockerfile` | `build: .` uses it |

## How it works underneath

**Project, network, names.** Compose gives the project a name (the `name:` key), creates a network `<project>_default` that all services join, and names containers `<project>-<service>-<n>`. Services reach each other by service name: the `api` service connects to the database at the host name `db`.

**`up` and `down`.** `docker compose up -d --wait SERVICE` creates and starts the containers (detached, `-d`) and waits for their health checks. `docker compose down` stops and removes them; `-v` also removes the named volumes, deleting their data.

**Interpolation.** `${NAME:-default}` inside the file is replaced from the shell environment or a `.env` file next to the compose file.

**Profiles.** A service with `profiles: [...]` starts only when one of its profiles is activated.

**Host vs. container ports.** In `"55432:5432"` the left number is the port on your computer, the right one the port inside the container.

**Validation without an engine.** `docker compose config` parses and checks the file and prints the resolved result; it does not need the Docker engine to be running.

## Walkthrough of this repository's use

`docker-compose.yml`, the whole file, block by block. Under each block, every line is explained.

```yaml
# The calendar service in a container. `make up` runs the same service as a local process instead; use this file to
# check the image or to run the service somewhere that has no Python environment.
name: ai-scheduling-agent
```

- `` # The calendar service in a container. `make up` runs the same service as a local process instead; use this file to ``: A comment (YAML ignores text after `#`).
- `# check the image or to run the service somewhere that has no Python environment.`: A comment (YAML ignores text after `#`).
- `name: ai-scheduling-agent`: The project name. Compose prefixes the names of containers, networks and volumes with it (for example `ai-scheduling-agent-db-1`).

```yaml
services:
  calendar:
    build: .
    ports:
      - "8090:8090"
    environment:
      CALENDAR_ALLOW_RESET: "on"       # demo and test aid behind POST /admin/reset; leave it off anywhere real
    volumes:
      - calendar-data:/data
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8090/health', timeout=3).status == 200 else 1)"]
      interval: 5s
      timeout: 5s
      retries: 10
```

- `services:`: Starts the mapping of services. A **service** is one container definition (one program that runs).
- `calendar:`: A service named `calendar`.
- `build: .`: Build the image from the Dockerfile in this folder instead of pulling one.
- `ports:`: Port mappings between the machine and the container.
- `- "8090:8090"`: Publish the container's port 8090 on the machine's port 8090 (`HOST:CONTAINER`). The program is then reachable at `localhost:8090`.
- `environment:`: Environment variables for the container.
- `CALENDAR_ALLOW_RESET: "on"`: (The comment on this line says: demo and test aid behind POST /admin/reset; leave it off anywhere real.) `CALENDAR_ALLOW_RESET`: `on` enables the reset endpoint of the calendar service (demos and the task runner only).
- `volumes:`: Starts a list (inside a service) of mounts, or the top-level definition of named volumes.
- `- calendar-data:/data`: Mount the **named volume** `calendar-data` at `/data` inside the container. A named volume is storage managed by Docker that outlives the container, so the data survives a restart (`down -v` deletes it).
- `healthcheck:`: How to test the container's health (overrides any check in the image).
- `test: ["CMD", "python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8090/health', timeout=3).status == 200 else 1)"]`: The check, run directly without a shell (`CMD`): a Python one-liner that fetches `/health` and exits 0 only if the status is 200.
- `interval: 5s`: Run the check every 5s.
- `timeout: 5s`: A check that takes longer than 5s counts as failed.
- `retries: 10`: Mark the container unhealthy after 10 failures in a row.

```yaml
volumes:
  calendar-data:
```

- `volumes:`: Starts a list (inside a service) of mounts, or the top-level definition of named volumes.
- `calendar-data:`: Declares the named volume `calendar-data` (Docker creates it on first use).

### The compose commands this repository uses

(none)

## Try it yourself

1. The installed Compose.

```bash
docker compose version
```

What you should see (captured from this repository):

```text
Docker Compose version v2.23.0-desktop.1
```

2. Parse and validate the file; no engine needed. Nothing is printed on success except our message.

```bash
docker compose config -q && echo 'docker-compose.yml is valid'
```

What you should see (captured from this repository):

```text
docker-compose.yml is valid
```

3. The file after Compose resolved it: defaults filled in, paths made absolute, short forms expanded.

```bash
docker compose config | sed -n 1,25p
```

What you should see (captured from this repository):

```text
name: ai-scheduling-agent
services:
  calendar:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      CALENDAR_ALLOW_RESET: "on"
    healthcheck:
      test:
        - CMD
        - python
        - -c
        - import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8090/health', timeout=3).status == 200 else 1)
      timeout: 5s
      interval: 5s
      retries: 10
    networks:
      default: null
    ports:
      - mode: ingress
        target: 8090
        published: "8090"
        protocol: tcp
    volumes:
```

4. Start the services and wait for them to be healthy. Not run in this session (the machine's Docker engine had no free disk space).

```bash
docker compose up -d --wait
```

5. Stop everything and delete the volumes. Not run here.

```bash
docker compose down -v
```

## Mistakes people make

- **Using `depends_on` without a health check.** It only orders start-up; the service may start before the database accepts connections. Here the condition is `service_healthy`.
- **Expecting `down` to keep data.** `down -v` removes volumes by design for a clean demo.
- **Real secrets in the file.** The credentials here are local test values for a throwaway container.
- **Mixing up host and container ports.** `HOST:CONTAINER`; services on the same network use the container port.
- **Binding a service to `127.0.0.1` inside the container.** Then the published port cannot reach it. Services in containers listen on `0.0.0.0` (`HTTP_HOST=0.0.0.0`).

## Check yourself

1. What does `docker compose up -d --wait db` do?

   *Answer:* Starts the `db` service in the background and waits until it is healthy.

2. What does `55432:5432` mean?

   *Answer:* Machine port 55432 forwards to container port 5432.

3. What is a named volume?

   *Answer:* Storage managed by Docker that survives container removal until `down -v`.

4. How does one service reach another?

   *Answer:* By its service name on the shared network.

5. How can you check the file with no running engine?

   *Answer:* `docker compose config -q`.

## Further reading

- Compose file reference, https://docs.docker.com/reference/compose-file/ (the file was validated here with `docker compose config`, Compose v2.23; containers were not started because the machine's Docker engine had no free disk).

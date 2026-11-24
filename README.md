# BookScout

**Discover books from your terminal.** BookScout is a Python command-line application backed by a Flask REST API. It lets readers search the Open Library catalog by title or author, sort results, and browse large result sets without opening a web browser.

The CLI is available as a public Docker image, while the production API runs on two Ubuntu application servers behind an HTTPS-enabled HAProxy load balancer.

**Quick links:** [Source code](https://github.com/jlouange/book-scout) · [Production API](https://www.jlmushumba.tech/api/books?q=python&type=title) · [Health check](https://www.jlmushumba.tech/api/health) · [Docker image](https://github.com/jlouange?tab=packages)

**Demo video:** _Add the recording link before submission._

## Features

- Search books **by title or author** using Open Library.
- View book titles, authors, first publication years, and Open Library work IDs.
- Choose **1–20 results per page** and navigate forward or backward.
- Sort by **relevance**, **newest**, or **oldest** (sorting is performed by Open Library across results).
- See continuous numbering and the current result range, such as `Showing books 6–10 of 3434`.
- Reuse visited pages through an **in-memory, per-search CLI cache**.
- Retry unsuccessful requests without losing the current search.
- Access the Flask API through **HTTPS**, with **two backends** and automatic health checks.
- Build, test, deploy, and publish with **GitHub Actions**.

## Quick start — Docker (recommended)

**Requirements:** Docker and an internet connection. You do **not** need to install Python or clone the repository.

```bash
docker run -it --rm ghcr.io/jlouange/bookscout-cli:latest
```

Docker downloads the public image automatically if it is not already available. The `-it` flags enable the interactive menu; `--rm` removes the stopped container.

Select **1** to search by title or **2** to search by author, choose a page size and sort order, then use **N** (next), **P** (previous), or **B** (back). Choose **3** from the main menu to exit.

**Note:** The Docker image contains the **CLI only**. It sends HTTPS requests to the deployed BookScout API; the API and Open Library must be reachable for searches to succeed.

### Build the CLI image yourself

```bash
git clone https://github.com/jlouange/book-scout.git
cd book-scout
docker build -f Dockerfile.cli -t bookscout-cli:1.0 .
docker run -it --rm bookscout-cli:1.0
```

## Run from source

**Requirements:** Python 3.14, `pip`, and an internet connection.

```bash
git clone https://github.com/jlouange/book-scout.git
cd book-scout
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m client.main
```

The CLI's API destination is configured in `client/api_client.py`. For the hosted API, use:

```python
API_URL = "https://www.jlmushumba.tech/api/books"
```

### Run the Flask API locally

In `client/api_client.py`, switch the URL to `http://127.0.0.1:5001/api/books` when you want the CLI to talk to your local API. Then, in one terminal, run:

```bash
python app.py
```

In another terminal, from the same project directory and virtual environment, run:

```bash
python -m client.main
```

The local Flask development server listens on port **5001**. Flask's development server is for local testing, **not** production hosting.

## Architecture

```text
                  BookScout CLI
              (Python or Docker)
                         |
                        HTTPS
                         v
             www.jlmushumba.tech
                  HAProxy LB
           TLS termination + health checks
                    /       \
                   /         \
                  v           v
           Web server 01   Web server 02
               Nginx          Nginx
                 |              |
              Gunicorn       Gunicorn
                 |              |
               Flask          Flask
                  \            /
                   \          /
                    Open Library
                    Search API
```

- **HAProxy** accepts HTTPS requests, balances `/api/` traffic using round robin, and checks backend health via `GET /api/health`.
- **Nginx** on each web server proxies `/api/` traffic to Gunicorn and returns an `X-Served-By` header identifying the backend.
- **Gunicorn** serves the Flask application on `127.0.0.1:8000` and is managed by `bookscout.service` under systemd.
- **Flask** validates requests, queries Open Library, and returns a compact JSON response.
- **Open Library** supplies book metadata. BookScout does not require an API key.

The Docker image packages the **client**, not the two production API servers.

## API reference

**Base URL:** `https://www.jlmushumba.tech`

### `GET /api/books`

Search the Open Library catalog through BookScout.

| Parameter | Values | Default | Purpose |
| --- | --- | --- | --- |
| `q` | Nonempty search text | Required | Title or author to search for |
| `type` | `title`, `author` | `title` | Search field |
| `limit` | Integer `1`–`20` | `3` | Results per page |
| `page` | Positive integer | `1` | Page number (starting at 1) |
| `sort` | `relevance`, `new`, `old` | `relevance` | Result order |

**Examples:**

```bash
# Search by title, newest first, page 2
curl 'https://www.jlmushumba.tech/api/books?q=linux&type=title&limit=5&page=2&sort=new'

# Search by author
curl 'https://www.jlmushumba.tech/api/books?q=Mark%20Lutz&type=author&limit=3'

# Invalid sort option: HTTP 400
curl -i 'https://www.jlmushumba.tech/api/books?q=linux&sort=invalid'
```

**Sample response (shortened for readability):**

```json
{
  "total": 3434,
  "page": 2,
  "limit": 5,
  "total_pages": 687,
  "has_next": true,
  "has_previous": true,
  "books": [
    {
      "book_id": "/works/OL46019969W",
      "book_title": "Agentic Linux",
      "book_authors": ["Ravi Vale"],
      "book_pub_year": 2026
    }
  ]
}
```

The actual `books` array may include up to `limit` records. Totals and titles can change as Open Library data changes. The displayed publication year is the work's **first publication year**; Open Library's `new`/`old` ranking is not guaranteed to form a perfectly chronological list of those displayed years.

### `GET /api/health`

Used by operators and HAProxy to check whether a backend application is responding.

```bash
curl 'https://www.jlmushumba.tech/api/health'
```

```json
{"status": "healthy"}
```

### Errors

| HTTP status | Meaning |
| --- | --- |
| `400` | Missing/invalid query, search type, page, limit, or sort option |
| `502` | Could not connect to Open Library or received an invalid upstream response |
| `504` | Request to Open Library timed out |

The CLI displays request failures and offers **Retry** or **Back**. The application depends on Open Library's availability and network access.

## Deploy to the provided Ubuntu web servers

This section documents how to reproduce the **deployed BookScout API**, not the CLI Docker image. It follows the project's existing setup: **two Ubuntu application servers** running Flask through Gunicorn and Nginx, and a **separate HAProxy load balancer** providing HTTPS and distributing requests. The real servers were previously configured; the examples below are a reproducible guide, not a reason to overwrite working configurations.

### Server roles and prerequisites

| Machine | Role | Application traffic |
| --- | --- | --- |
| `7357-web-01` | Application server 1 | Nginx `:80` → Gunicorn `127.0.0.1:8000` |
| `7357-web-02` | Application server 2 | Nginx `:80` → Gunicorn `127.0.0.1:8000` |
| Load balancer (`lb-01`) | HAProxy, HTTPS termination, health checks | Public `:443` → both Nginx servers on `:80` |

**You need:** SSH access to the three provided hosts, the repository's source code, outbound internet access to Open Library, permission to install packages/manage services, a DNS name pointing to the load balancer, and a valid HTTPS certificate on the load balancer. The examples assume the provided servers use the `ubuntu` account and the code lives in `/home/ubuntu/book-scout`. Substitute the correct host addresses and paths for a new environment.

**Network exposure:** Allow public HTTPS (`443`) to the load balancer; redirect or serve HTTP (`80`) as required. Allow the load balancer to reach each web server's Nginx port (`80`), ideally restricting that access to the load balancer. Keep Gunicorn bound to `127.0.0.1`, not publicly exposed. Restrict SSH access to approved administrators.

### A. Connect to each application server

From your local machine, connect to **web-01** using the school SSH key (adjust the host address):

```bash
ssh -i ~/.ssh/school ubuntu@<WEB01_HOST>
```

Perform steps **B–D** on `7357-web-01` and then repeat the same steps on `7357-web-02` (connect using `<WEB02_HOST>`). If your SSH configuration already defines host aliases, use those aliases instead. The SSH public key must already be authorized on each host; never commit private keys to Git.

### B. Install the application and Python dependencies on *both* web servers

On Ubuntu 20.04 / ARM64, Python 3.14 may not be available from the default APT repositories. BookScout's deployment used [uv](https://docs.astral.sh/uv/) to install the Python runtime and create its virtual environment.

```bash
sudo apt update
sudo apt install -y git curl ca-certificates nginx

# Install uv for the ubuntu user; see the official uv installation docs.
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python 3.14 and create an isolated application environment.
/home/ubuntu/.local/bin/uv python install 3.14
cd /home/ubuntu
git clone https://github.com/jlouange/book-scout.git
cd /home/ubuntu/book-scout
/home/ubuntu/.local/bin/uv venv --python 3.14 .venv
/home/ubuntu/.local/bin/uv pip install --python .venv/bin/python -r requirements.txt

# Verify Gunicorn and Python are installed.
.venv/bin/python --version
.venv/bin/gunicorn --version
```

If the repository is already present, **do not clone it again**: update it with `git fetch origin main` and `git pull --ff-only origin main` before installing dependencies. Review external install scripts before running them on systems you administer.

### C. Run Flask through Gunicorn and systemd on *both* web servers

Create a systemd unit on each server at `/etc/systemd/system/bookscout.service` (requires sudo):

```ini
[Unit]
Description=BookScout Flask API (Gunicorn)
After=network-online.target
Wants=network-online.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/book-scout
ExecStart=/home/ubuntu/book-scout/.venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 app:app
Restart=on-failure
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Save the unit, then run:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now bookscout
sudo systemctl status bookscout --no-pager
curl -i http://127.0.0.1:8000/api/health
```

The expected local health response is HTTP `200` with `{"status":"healthy"}`. If startup fails, inspect logs with `sudo journalctl -u bookscout -n 50 --no-pager`.

### D. Configure Nginx as a reverse proxy on *both* web servers

In the **active Nginx `server` block that listens on port 80**, add a location for `/api/` (or create an appropriate Nginx site if this is a fresh server). **Do not replace unrelated Nginx configuration** on a server being used for other coursework:

```nginx
location /api/ {
    # No trailing slash on proxy_pass: preserve /api/... in Flask.
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 30s;
    add_header X-Served-By $hostname always;
}
```

Validate and reload Nginx, then verify the proxy locally:

```bash
sudo nginx -t
sudo systemctl reload nginx
curl -i http://127.0.0.1/api/health
```

The response should include `X-Served-By` with that server's hostname. Repeat the installation and configuration checks on **both web-01 and web-02** before touching the load balancer.

### E. Configure HAProxy on the dedicated load balancer

Connect to the provided load-balancer host and install HAProxy if it is not already present:

```bash
ssh -i ~/.ssh/school ubuntu@<LOAD_BALANCER_HOST>
sudo apt update
sudo apt install -y haproxy
```

In `/etc/haproxy/haproxy.cfg`, preserve the existing `global` and `defaults` sections. The following shows the **relevant frontend/backend pattern**. If the server already has port-80/443 frontends, **merge the ACL and backend routing into those frontends rather than duplicating binds**:

```haproxy
# Illustrative frontends for a fresh, dedicated load balancer.
frontend bookscout_http
    bind *:80
    http-request redirect scheme https code 301

frontend bookscout_https
    bind *:443 ssl crt /etc/haproxy/certs/www.jlmushumba.tech.pem
    acl is_bookscout_api path_beg /api/
    use_backend bookscout_servers if is_bookscout_api

backend bookscout_servers
    balance roundrobin
    option httpchk GET /api/health
    http-check expect status 200
    server web01 <WEB01_REACHABLE_IP>:80 check
    server web02 <WEB02_REACHABLE_IP>:80 check
```

Replace `<WEB01_REACHABLE_IP>` and `<WEB02_REACHABLE_IP>` with addresses reachable **from the load balancer**. The `:443` bind expects a valid PEM bundle containing the certificate chain and private key at the specified location, with restricted filesystem permissions. Obtain the certificate through your approved certificate provider and follow [HAProxy's SSL/TLS guidance](https://www.haproxy.com/documentation/haproxy-configuration-tutorials/ssl-tls/). Do **not** store private keys in Git or in the README.

Point the `www.jlmushumba.tech` DNS record to the public address of the load balancer. Once the configuration and certificate are in place:

```bash
sudo haproxy -c -f /etc/haproxy/haproxy.cfg
sudo systemctl enable haproxy
sudo systemctl reload haproxy
curl -i https://www.jlmushumba.tech/api/health
```

If this is the **first installation**, use `sudo systemctl start haproxy` after enabling instead of `reload`. For any existing deployment, validate the configuration and use a reload to avoid unnecessary interruption.

### F. Verify both servers and the production API

From your laptop or another HTTPS client:

```bash
# Confirm that HTTPS and the application are responding.
curl -i 'https://www.jlmushumba.tech/api/health'

# Verify round-robin backend identification.
for i in {1..6}; do
  curl -sS -D - -o /dev/null 'https://www.jlmushumba.tech/api/health' \
    | grep -i '^x-served-by:'
done

# Verify production search, pagination and sorting.
curl -i 'https://www.jlmushumba.tech/api/books?q=linux&type=title&limit=5&page=2&sort=new'
```

With both backends healthy, the `X-Served-By` values should include `7357-web-01` and `7357-web-02`. Check HTTP status codes, not just the header, when diagnosing failures.

**Optional failover demonstration:** In a controlled test, stop `bookscout` on one backend, allow HAProxy's health check to mark it unhealthy, and confirm the other backend still returns HTTP `200`; promptly restart the stopped service. Do not perform this on a shared production system without authorization.

### G. Deploy subsequent changes (manual or GitHub Actions)

For an authorized **manual update** on each web server:

```bash
cd /home/ubuntu/book-scout
git fetch origin main
git pull --ff-only origin main
/home/ubuntu/.local/bin/uv pip install --python .venv/bin/python -r requirements.txt
sudo systemctl restart bookscout
curl -fsS http://127.0.0.1:8000/api/health
```

The project's preferred path is **CI/CD**: push a tested change to `main`; the **BookScout CI** workflow runs first, and a successful CI push starts **BookScout CD**, which updates both servers via SSH and checks health. The deployment workflow uses these repository **Actions secrets** (configure values for your own servers):

| GitHub Actions secret | Purpose |
| --- | --- |
| `WEB01_HOST` | SSH-reachable address of application server 1 |
| `WEB02_HOST` | SSH-reachable address of application server 2 |
| `BOOKSCOUT_DEPLOY_KEY` | Private SSH key used by the deploy workflow |
| `BOOKSCOUT_KNOWN_HOSTS` | Verified SSH host keys to protect host identity |

The deploy key must be authorized for the `ubuntu` account on both hosts. Configure passwordless permission only for the specific service restart required by deployment; avoid storing root passwords or private keys in the repository. Inspect the actual workflow files in `.github/workflows/` for the source-of-truth deployment commands.

### Troubleshooting the deployed architecture

| Symptom | Check |
| --- | --- |
| SSH `Permission denied (publickey)` | Correct `ubuntu` username, host, SSH private key and `authorized_keys` |
| Gunicorn not responding on `:8000` | `systemctl status bookscout`, `journalctl -u bookscout`, Python/venv path |
| Nginx returns `502` | Gunicorn status, `proxy_pass` target, Nginx error logs |
| HAProxy reports backend unavailable | Web-server port `80`, security groups/firewall, `/api/health`, HAProxy checks |
| HTTPS fails | DNS points to LB, certificate covers hostname, HAProxy listens on `443` |
| Search returns `502` / `504` | Open Library availability, outbound network, request timeout; retry from CLI |
| Only one `X-Served-By` value appears | Health and reachability of the other backend; HAProxy backend status |

## CI/CD and container publishing

The repository contains three GitHub Actions workflows:

| Workflow | Trigger | Purpose |
| --- | --- | --- |
| **BookScout CI** | Pushes and pull requests | Install dependencies, compile Python files, run unit tests |
| **BookScout CD** | Successful CI after a push to `main` | Update both application servers over SSH, restart the service, verify health |
| **BookScout Docker Publish** | Successful CI after a push to `main` | Build `Dockerfile.cli` and publish `latest` and immutable commit-SHA tags to GHCR |

The deployment workflow uses GitHub Actions secrets for SSH credentials and server settings. Container publishing uses the workflow's `GITHUB_TOKEN` with package-write permission. The GHCR image is public and can be run without a registry login.

## Tests

Run the current automated test suite:

```bash
python -m unittest discover -s tests -v
python -m compileall -q app.py client tests
```

The existing unit tests cover a book search, the health endpoint, and invalid search types. Pagination, sorting, retry behavior, and two-server routing have also been exercised manually; they are not all covered by the current automated suite.

## Challenges and solutions

| Challenge | Approach |
| --- | --- |
| External API timeouts | Explicit request timeouts, HTTP error handling, and a CLI retry option |
| Repeated requests when revisiting pages | Per-search in-memory cache of successfully loaded pages |
| Large search result sets | Configurable page sizes, next/previous navigation, and continuous numbering |
| Serving the same API on two servers | Gunicorn + systemd + Nginx on each server, HAProxy health checks and round robin |
| Keeping deployments consistent | CI-gated GitHub Actions deployment to both servers |
| Simplifying installation for users | Docker CLI image published publicly through GHCR |

## Limitations

- BookScout is a **search-and-discovery** tool; it does not currently provide accounts, saved reading lists, or offline book data.
- CLI caching lasts only for the current search and is lost when the application exits.
- Search requires the deployed API and Open Library to be reachable.
- External records may have missing authors or publication years.

## Credits and references

**External data and its developers:** Book data comes from the **[Open Library](https://openlibrary.org/) Search API**, maintained by the Open Library community and the **Internet Archive**. BookScout uses the official [`/search.json` endpoint](https://openlibrary.org/dev/docs/api/search), including `title`/`author`, `page`/`limit`, and `sort`. Thank you to Open Library contributors for making catalog information available without requiring an API key.

**Libraries, infrastructure, and documentation used:**

| Resource | Role | Official documentation |
| --- | --- | --- |
| Python | Language for CLI/API | [python.org](https://docs.python.org/3/) |
| Flask | REST API and HTTP responses | [Flask](https://flask.palletsprojects.com/) |
| Requests | Calling the BookScout API and Open Library | [Requests](https://requests.readthedocs.io/) |
| Gunicorn | WSGI production application server | [Gunicorn](https://docs.gunicorn.org/) |
| Nginx | Reverse proxy on web-01 and web-02 | [Nginx](https://nginx.org/en/docs/) |
| HAProxy | HTTPS termination, health checks, load balancing | [HAProxy](https://www.haproxy.com/documentation/) |
| uv | Python 3.14 installation and environment management on servers | [uv](https://docs.astral.sh/uv/) |
| Docker | CLI image packaging and execution | [Docker](https://docs.docker.com/) |
| GitHub Actions | Automated CI, server deployment and GHCR publishing | [GitHub Actions](https://docs.github.com/en/actions) |
| GitHub Container Registry | Hosting the public CLI Docker image | [GitHub Packages](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry) |

- **Source repository:** [jlouange/book-scout](https://github.com/jlouange/book-scout)
- **Author:** `jlouange` — Software Engineering, African Leadership University.

**Demo video:** _Add the final recording URL here before submission._

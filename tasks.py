from pathlib import Path
import time
import urllib.error
import urllib.request

from invoke import task


DEFAULT_USERNAME = "username"
DEFAULT_PASSWORD = "password"
DEFAULT_TOURNAMENT_CODE = "1"
DEFAULT_MAIN_URL = "http://127.0.0.1:3000"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = "7070"
DEFAULT_CONFIG_PATH = "config.yaml"


def _python_bin():
    venv_python = Path(".venv/bin/python")
    if venv_python.exists():
        return str(venv_python)
    return "python3"


def _wait_for_backend(base_url, timeout=30):
    deadline = time.time() + timeout
    health_url = f"{base_url.rstrip('/')}/healthz"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    last_error = None

    while time.time() < deadline:
        try:
            with opener.open(health_url) as response:
                if response.status == 200:
                    return
                last_error = f"unexpected status {response.status}"
        except urllib.error.HTTPError as error:
            last_error = f"http {error.code}"
        except Exception as error:
            last_error = repr(error)
        time.sleep(0.5)

    raise RuntimeError(f"backend did not become ready at {health_url}: {last_error}")


def _write_config(path, username, password, tournament_code, main_instance_url, remote_instance_url):
    config_path = Path(path)
    remote_value = remote_instance_url or ""
    config_path.write_text(
        "\n".join(
            [
                f"username: '{username}'",
                f"password: '{password}'",
                f"tournament_code: '{tournament_code}'",
                f"main_instance_url: '{main_instance_url}'",
                f"remote_instance_url: '{remote_value}'",
                "",
            ]
        ),
        encoding="utf-8",
    )


@task
def setup(c):
    """Create a local virtualenv and install match dependencies."""
    c.run("python3 -m venv .venv", pty=True)
    c.run(".venv/bin/pip install -r requirements.txt invoke", pty=True)


@task(name="write-config")
def write_config(
    c,
    username=DEFAULT_USERNAME,
    password=DEFAULT_PASSWORD,
    tournament_code=DEFAULT_TOURNAMENT_CODE,
    main_instance_url=DEFAULT_MAIN_URL,
    remote_instance_url="",
    path=DEFAULT_CONFIG_PATH,
):
    """Write a config.yaml for local development."""
    _write_config(
        path,
        username,
        password,
        tournament_code,
        main_instance_url,
        remote_instance_url,
    )


@task(name="check-backend")
def check_backend(c, main_instance_url=DEFAULT_MAIN_URL, timeout=30):
    """Wait for the configured backend healthcheck to respond."""
    _wait_for_backend(main_instance_url, timeout=int(timeout))
    print(f"Backend is ready at {main_instance_url}")


@task
def start(
    c,
    username=DEFAULT_USERNAME,
    password=DEFAULT_PASSWORD,
    tournament_code=DEFAULT_TOURNAMENT_CODE,
    main_instance_url=DEFAULT_MAIN_URL,
    remote_instance_url="",
    config_path=DEFAULT_CONFIG_PATH,
    host=DEFAULT_HOST,
    port=DEFAULT_PORT,
    install=True,
    wait_for_backend=True,
):
    """Write config and start the match UI against a specific backend URL."""
    if install and not Path(".venv").exists():
        setup(c)

    if wait_for_backend:
        _wait_for_backend(main_instance_url)

    _write_config(
        config_path,
        username,
        password,
        tournament_code,
        main_instance_url,
        remote_instance_url,
    )
    c.run(f"HOST={host} PORT={port} {_python_bin()} main.py", pty=True)

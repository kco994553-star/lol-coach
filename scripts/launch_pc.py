"""Loopback-only PC launcher. Secrets stay out of process arguments and logs."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import secrets
import sys
import webbrowser
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def default_data_dir():
    base = Path(os.environ['LOCALAPPDATA']) if os.environ.get('LOCALAPPDATA') else Path.home() / '.local' / 'share'
    return base / 'LoL-Coach-PC' / 'private'


def create_server(data_dir, *, port=8765):
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError('Port must be between 0 and 65535')
    data_dir = Path(data_dir).expanduser().absolute()
    if data_dir.is_symlink():
        raise ValueError('Data directory must not be a symbolic link')
    data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    token_file = data_dir / 'access-token'
    if token_file.is_symlink() or token_file.exists() and not token_file.is_file():
        raise ValueError('Access token path must be a regular local file')
    from coach_v1.pregame_server import PregameWorkbench
    from coach_v1.server import Limits
    token = secrets.token_urlsafe(32)
    server = PregameWorkbench(data_dir / 'work.sqlite', token,
                              Limits(1_000_000, 1000, 1000, 1000, 1000, 8), port)
    try:
        descriptor = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC |
                             getattr(os, 'O_NOFOLLOW', 0), 0o600)
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            stream.write(token + '\n')
        if os.name != 'nt':
            token_file.chmod(0o600)
        server.pc_data_dir = data_dir
    except Exception:
        server.server_close()
        raise
    return server


def browser_url(server):
    return f'http://127.0.0.1:{server.server_port}/pc#' + urlencode({'token': server.token})


def print_ready(server):
    print(f'LoL Coach PC: http://127.0.0.1:{server.server_port}/pc', flush=True)
    print('Keep this window open. Close with Ctrl+C. The browser receives the private access key automatically.', flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Start local LoL Coach PC; no in-game coaching')
    parser.add_argument('--port', type=int, default=8765, help='Loopback port (0 chooses a free port)')
    parser.add_argument('--data-dir', type=Path, default=default_data_dir())
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--lcu-lockfile', type=Path, help='Explicitly pair this local League client lockfile')
    parser.add_argument('--lcu-certificate-sha256', help='Pinned local LCU certificate SHA256')
    args = parser.parse_args(argv)
    server = None
    services = None
    try:
        server = create_server(args.data_dir, port=args.port)
        from coach_v1.pc_runtime import start_pc_services
        services = start_pc_services(server, lcu_lockfile=args.lcu_lockfile,
                                     lcu_certificate_sha256=args.lcu_certificate_sha256)
        print_ready(server)
        if not args.no_browser:
            webbrowser.open(browser_url(server), new=2)
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        return 0
    except (OSError, ValueError) as error:
        # Error values from OS or network implementations may contain secrets.
        print('Could not start the local PC app (' + type(error).__name__ + '). Close any existing instance and check the data directory or port.', file=sys.stderr)
        return 1
    finally:
        if services is not None:
            services.close()
        if server is not None:
            server.server_close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

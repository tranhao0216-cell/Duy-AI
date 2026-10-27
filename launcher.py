"""Create an environment for this Python version, then start the local app."""
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import venv
import webbrowser


ROOT = Path(__file__).resolve().parent
URL = 'http://127.0.0.1:5000'


def open_when_ready(process):
    # Open the browser only after this server accepts requests.
    for _ in range(60):
        if process.poll() is not None:
            return
        try:
            with urllib.request.urlopen(URL, timeout=1) as response:
                if response.status == 200:
                    webbrowser.open(URL)
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.5)


def main():
    if sys.version_info < (3, 10):
        print('Can Python 3.10 tro len. Khuyen dung Python 3.14 64-bit.', flush=True)
        return 1
    version = f'{sys.version_info.major}.{sys.version_info.minor}'
    environment = ROOT / f'.venv-{version}'
    python = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    print(f'Viet Dich - Python {version} ({sys.executable})', flush=True)
    print(f'Moi truong rieng: {environment.name}', flush=True)
    try:
        if not python.exists():
            venv.EnvBuilder(with_pip=True).create(environment)
        # Binary wheels avoid requiring C/C++ or Rust toolchains on Windows.
        subprocess.run([str(python), '-m', 'pip', 'install', '--upgrade', 'pip'], check=True, cwd=ROOT)
        subprocess.run([str(python), '-m', 'pip', 'install', '--only-binary=:all:',
                        '-r', str(ROOT / 'requirements.txt')], check=True, cwd=ROOT)
        print(f'Mo {URL}. Giu cua so nay mo; nhan Ctrl+C de dung app.', flush=True)
        process = subprocess.Popen([str(python), str(ROOT / 'app.py')], cwd=ROOT)
        threading.Thread(target=open_when_ready, args=(process,), daemon=True).start()
        try:
            return process.wait()
        except KeyboardInterrupt:
            if process.poll() is None:
                process.terminate()
            process.wait()
            return 0
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f'Khoi dong khong thanh cong: {exc}', flush=True)
        print('Kiem tra loi phia tren, ket noi Internet va Python 64-bit.', flush=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())

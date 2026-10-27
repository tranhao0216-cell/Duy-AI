import os
from pathlib import Path
import shutil
import subprocess
import sys
from collections import namedtuple

import pytest

import launcher


def test_launcher_isolates_environment_and_uses_its_python(tmp_path, monkeypatch):
    """A stale .venv must not be reused after upgrading Python."""
    (tmp_path / '.venv').mkdir()
    monkeypatch.setattr(launcher, 'ROOT', tmp_path)
    version_info = namedtuple('VersionInfo', 'major minor micro releaselevel serial')
    monkeypatch.setattr(launcher.sys, 'version_info', version_info(3, 14, 0, 'final', 0))
    calls = []
    class Builder:
        def __init__(self, with_pip):
            assert with_pip
        def create(self, path):
            calls.append(('create', path))
    class Process:
        def wait(self):
            return 0
    class Thread:
        def __init__(self, **kwargs):
            pass
        def start(self):
            pass
    monkeypatch.setattr(launcher.venv, 'EnvBuilder', Builder)
    monkeypatch.setattr(launcher.subprocess, 'run', lambda args, **kw: calls.append(('run', args)))
    monkeypatch.setattr(launcher.subprocess, 'Popen', lambda args, **kw: calls.append(('start', args)) or Process())
    monkeypatch.setattr(launcher.threading, 'Thread', Thread)
    assert launcher.main() == 0
    environment = tmp_path / '.venv-3.14'
    python = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    assert calls[0] == ('create', environment)
    assert all(call[1][0] == str(python) for call in calls[1:])
    assert '--only-binary=:all:' in calls[2][1]


def test_launcher_install_failure_does_not_start_server(tmp_path, monkeypatch):
    monkeypatch.setattr(launcher, 'ROOT', tmp_path)
    monkeypatch.setattr(launcher.venv.EnvBuilder, 'create', lambda self, path: None)
    def fail(args, **kwargs):
        raise subprocess.CalledProcessError(1, args)
    monkeypatch.setattr(launcher.subprocess, 'run', fail)
    monkeypatch.setattr(launcher.subprocess, 'Popen', lambda *args, **kw: pytest.fail('server started after install failure'))
    assert launcher.main() == 1


@pytest.mark.skipif(os.name != 'nt', reason='Windows batch integration')
def test_windows_batch_starts_launcher(tmp_path):
    batch = Path(__file__).resolve().parents[1] / 'run.bat'
    shutil.copy(batch, tmp_path / 'run.bat')
    (tmp_path / 'launcher.py').write_text(
        'import sys; print("LAUNCH_OK=" + str(sys.version_info.major) + "." + str(sys.version_info.minor))', encoding='utf-8')
    completed = subprocess.run(['cmd', '/c', str(tmp_path / 'run.bat')],
                               input='\n', capture_output=True, text=True, timeout=30)
    assert 'LAUNCH_OK=' in completed.stdout, completed.stdout + completed.stderr
    if sys.version_info[:2] == (3, 14):
        assert 'LAUNCH_OK=3.14' in completed.stdout

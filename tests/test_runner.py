try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

from py_config_runner.runner import run_script, _setup_config, _check_script, _ConfigObject

import pytest


def test_run_script_script_file_no_run(dirname):  # noqa: F811
    script_fp = dirname / "script.py"

    s = """
import numpy as np

a = 123
b = np.array([1, 2, 3])

    """

    with script_fp.open("w") as h:
        h.write(s)

    with pytest.raises(RuntimeError, match="should contain a method `run"):
        run_script(script_fp, "")


def test_run_script_script_file_run_not_callable(dirname):  # noqa: F811
    script_fp = dirname / "script.py"

    s = """
run = 0
    """

    with script_fp.open("w") as h:
        h.write(s)

    with pytest.raises(RuntimeError, match="should be a callable function"):
        run_script(script_fp, "")


def test_run_script_script_file_run_wrong_signature(dirname):  # noqa: F811
    script_fp = dirname / "script.py"

    s = """
def run():
    pass
    """

    with script_fp.open("w") as h:
        h.write(s)

    with pytest.raises(RuntimeError, match="Run method signature should be"):
        run_script(script_fp, "")


def test_run_script(capsys, script_filepath, config_filepath):  # noqa: F811

    run_script(script_filepath, config_filepath)

    captured = capsys.readouterr()
    out = captured.out.split('\r')
    out = list(map(lambda x: x.strip(), out))
    out = list(filter(None, out))
    assert "Run\n1\n2\n{}\n{}".format(config_filepath.as_posix(), script_filepath.as_posix()) in out[-1]


def test_run_logging_script(capsys, logging_script_filepath, config_filepath):  # noqa: F811

    run_script(logging_script_filepath, config_filepath)

    captured = capsys.readouterr()
    out = captured.err.split('\n')
    out = list(map(lambda x: x.strip(), out))
    out = list(filter(None, out))
    assert "|script|INFO| Start run script" in out[0]
    assert "|script|INFO| 1" in out[1]
    assert "|script|INFO| 2" in out[2]


def test_run_script_raise_exeption(dirname, config_filepath):  # noqa: F811
    script_fp = dirname / "bad_script.py"

    s = """
def run(config, **kwargs):
    raise RuntimeError("STOP")
    """

    with script_fp.open("w") as h:
        h.write(s)

    with pytest.raises(RuntimeError):
        run_script(script_fp, config_filepath)


def test_run_script_manual_config_loading(capsys, dirname, config_filepath):  # noqa: F811
    script_fp = dirname / "manual_config_loading_script.py"

    s = """
from pathlib import Path


def run(config, **kwargs):
    config = config.setup()

    assert getattr(config, 'a', None) == 1
    assert getattr(config, 'b', None) == 2
    assert getattr(config, 'config_filepath', None) == Path("{}")
    assert getattr(config, 'script_filepath', None) == Path("{}")
    """.format(config_filepath, script_fp)

    with script_fp.open("w") as h:
        h.write(s)

    run_script(script_fp, config_filepath, manual_config_load=True)


def test_run_script_with_local_rank(capsys, dirname, config_filepath):  # noqa: F811
    script_fp = dirname / "script.py"

    s = """
def run(config, local_rank=0, **kwargs):
    assert local_rank == 1
    """

    with script_fp.open("w") as h:
        h.write(s)

    run_script(script_fp, config_filepath, local_rank=1)


def test__setup_config(config_filepath, script_filepath):

    config = _setup_config(config_filepath, script_filepath)

    assert getattr(config, 'a', None) == 1
    assert getattr(config, 'b', None) == 2
    assert getattr(config, 'config_filepath', None) == Path(config_filepath)
    assert getattr(config, 'script_filepath', None) == Path(script_filepath)


def test__ConfigObject(config_filepath, script_filepath):

    config = _ConfigObject(config_filepath, script_filepath)
    config = config.setup()

    assert getattr(config, 'a', None) == 1
    assert getattr(config, 'b', None) == 2
    assert getattr(config, 'config_filepath', None) == Path(config_filepath)
    assert getattr(config, 'script_filepath', None) == Path(script_filepath)


def test_example(example_baseline_config, example_scripts_training, example_path):

    import sys
    sys.path.insert(0, example_path.as_posix())
    run_script(example_scripts_training, example_baseline_config)
    run_script(example_scripts_training, example_baseline_config, manual_config_load=True)

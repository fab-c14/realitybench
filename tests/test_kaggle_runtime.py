"""Guards for Kaggle run gating and task .run() wiring."""

from pathlib import Path

import pytest

from benchmark.kaggle_runtime import should_run_kbench
from benchmark.tasks.registry import ALL_TASKS


def test_should_run_kbench_default_false(monkeypatch):
    monkeypatch.delenv("REALITYBENCH_KBENCH_RUN", raising=False)
    monkeypatch.delenv("KAGGLE_KERNEL_RUN_TYPE", raising=False)
    assert should_run_kbench() is False


def test_should_run_kbench_env_gate(monkeypatch):
    monkeypatch.setenv("REALITYBENCH_KBENCH_RUN", "1")
    monkeypatch.delenv("KAGGLE_KERNEL_RUN_TYPE", raising=False)
    assert should_run_kbench() is True


def test_should_run_kbench_kaggle_kernel(monkeypatch):
    monkeypatch.delenv("REALITYBENCH_KBENCH_RUN", raising=False)
    monkeypatch.setenv("KAGGLE_KERNEL_RUN_TYPE", "Batch")
    assert should_run_kbench() is True


@pytest.mark.parametrize("task", ALL_TASKS, ids=lambda t: t.task_id)
def test_task_source_wires_kbench_run(task):
    """Each task module must call .run(kbench.llm) behind should_run_kbench()."""
    func = task.kbench_task.func
    source_path = Path(func.__code__.co_filename)
    source = source_path.read_text(encoding="utf-8")
    assert "should_run_kbench()" in source
    assert f"{func.__name__}.run(kbench.llm)" in source

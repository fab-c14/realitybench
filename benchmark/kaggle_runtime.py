"""Helpers for Kaggle Benchmarks notebook vs local CLI execution."""

from __future__ import annotations

import os


def should_run_kbench() -> bool:
    """
    True when the task module should call ``task_fn.run(kbench.llm)``.

    - Kaggle kernels set ``KAGGLE_KERNEL_RUN_TYPE``
    - Local validation: ``REALITYBENCH_KBENCH_RUN=1``
    - Importing tasks into the CLI/registry must NOT trigger LLM runs
    """
    if os.environ.get("REALITYBENCH_KBENCH_RUN") == "1":
        return True
    return bool(os.environ.get("KAGGLE_KERNEL_RUN_TYPE"))

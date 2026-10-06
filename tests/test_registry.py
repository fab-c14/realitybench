"""
Tests for RealityBench Task Registry
Validates that all 12 tasks are registered, have valid specifications, and conform to the task schema.
"""

from benchmark.tasks.registry import ALL_TASKS, TASK_MAP, TaskDefinition


def test_registry_count():
    """Asserts that exactly 12 tasks are registered in the benchmark suite."""
    assert len(ALL_TASKS) == 12
    assert len(TASK_MAP) == 12


def test_task_indices_and_uniqueness():
    """Validates sequential numbering from 1 to 12 and unique task identifiers."""
    task_numbers = [t.task_number for t in ALL_TASKS]
    assert task_numbers == list(range(1, 13))

    task_ids = [t.task_id for t in ALL_TASKS]
    assert len(set(task_ids)) == 12
    for tid in task_ids:
        assert tid.startswith("realitybench-")


def test_task_definitions_complete():
    """Validates that each task contains non-empty prompts, baselines, and callable graders."""
    for task in ALL_TASKS:
        assert isinstance(task, TaskDefinition)
        assert task.name.strip() != "", f"Empty name for task {task.task_id}"
        assert task.category_focus.strip() != "", f"Empty category focus for task {task.task_id}"
        assert task.prompt.strip() != "", f"Empty prompt for task {task.task_id}"
        assert len(task.prompt) > 80, f"Suspiciously short prompt for task {task.task_id}"

        # Baselines must be valid HTML documents
        assert "<html" in task.naive_code.lower(), f"Missing <html> in naive code for {task.task_id}"
        assert "<html" in task.robust_code.lower(), f"Missing <html> in robust code for {task.task_id}"

        # Grader must be callable
        assert callable(task.grader), f"Grader is not callable for {task.task_id}"

        # kbench task must exist
        assert task.kbench_task is not None


def test_pilot_tasks_included():
    """Validates that the 3 core pilot tasks (Login, Search, Checkout) are correctly registered."""
    pilot_ids = ["realitybench-login", "realitybench-search", "realitybench-checkout"]
    for pid in pilot_ids:
        assert pid in TASK_MAP, f"Pilot task {pid} not found in TASK_MAP"
        assert TASK_MAP[pid].task_number in [1, 2, 3]

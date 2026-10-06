"""
RealityBench Reusable Rich Panels
Consistent panel presentation for task headers, results, code previews, and errors.
"""


from rich import box
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text


def task_header_panel(
    task_number: int,
    task_name: str,
    category_focus: str,
    model_name: str | None = None,
    phase: str | None = None
) -> Panel:
    """Renders a structured, clean panel introducing a running task."""
    content = Text()
    content.append(f"Task {task_number:02d}: ", style="info")
    content.append(f"{task_name}\n", style="task")
    content.append("Focus:   ", style="info")
    content.append(f"{category_focus}\n", style="muted")

    if model_name:
        content.append("Model:   ", style="info")
        content.append(f"{model_name}\n", style="model")
    if phase:
        content.append("Phase:   ", style="info")
        content.append(f"{phase.upper()}", style="warning" if phase.lower() == "reality" else "success")

    return Panel(
        content,
        title="[header]RealityBench Task Execution[/header]",
        border_style="border",
        box=box.ROUNDED
    )


def task_result_panel(
    task_name: str,
    demo_score: float,
    reality_score: float,
    reality_gap: float,
    model_name: str | None = None
) -> Panel:
    """Renders the final summary scores for a single task."""
    content = Text()
    if model_name:
        content.append("Model:         ", style="info")
        content.append(f"{model_name}\n", style="model")
    content.append("Task:          ", style="info")
    content.append(f"{task_name}\n\n", style="white")

    content.append("Demo Score:    ", style="info")
    content.append(f"{demo_score * 100:.1f}%\n", style="success")

    content.append("Reality Score: ", style="info")
    content.append(f"{reality_score * 100:.1f}%\n", style="warning" if reality_score < 0.6 else "success")

    content.append("Reality Gap:   ", style="info")
    gap_style = "failure" if reality_gap > 0.25 else ("warning" if reality_gap > 0.05 else "success")
    content.append(f"{reality_gap * 100:+.1f}%\n", style=gap_style)

    return Panel(
        content,
        title="[header]Task Evaluation Summary[/header]",
        border_style="border",
        box=box.ROUNDED
    )


def error_panel(
    arg1: str,
    arg2: str = "",
    reason: str | None = None,
    exception: Exception | None = None,
    is_infrastructure: bool = False
) -> Panel:
    """
    Renders an error panel.
    Flexible calling conventions:
      - error_panel("Title", "Error details / message")
      - error_panel("Task Name", "Model Name", "Failure reason", exception=...)
    """
    if reason is not None:
        # Full (task_name, model_name, reason) call
        task_name = arg1
        model_name = arg2
        error_type = "BENCHMARK INFRASTRUCTURE ERROR" if is_infrastructure else "EXPECTED MODEL FAILURE"
        border_style = "bold red" if is_infrastructure else "red"

        content = Text()
        content.append(f"Type:   {error_type}\n", style="bold red")
        content.append(f"Task:   {task_name}\n", style="white")
        content.append(f"Model:  {model_name}\n\n", style="model")
        content.append(f"Reason: {reason}\n", style="yellow")
        if exception and is_infrastructure:
            content.append(f"\nException Details: {exception!s}", style="muted")

        return Panel(
            content,
            title=f"[{border_style}]Error Encountered[/{border_style}]",
            border_style=border_style,
            box=box.HEAVY
        )
    else:
        # Generic (title, message) call
        title = arg1
        details = arg2
        content = Text()
        content.append(f"{details}\n", style="yellow")
        if exception:
            content.append(f"\nException Details: {exception!s}", style="muted")

        return Panel(
            content,
            title=f"[bold red]{title}[/bold red]",
            border_style="red",
            box=box.ROUNDED
        )


def code_panel(
    arg1: str,
    arg2: str | None = None,
    language: str = "html",
    title: str | None = None
) -> Panel:
    """
    Renders formatted code with syntax highlighting using Rich Syntax.
    Accepts (code, language="html", title="...") or (title, code, language="html").
    """
    if arg2 is not None:
        panel_title = arg1
        code_str = arg2
    else:
        code_str = arg1
        panel_title = title or "Generated Implementation"

    syntax = Syntax(
        code_str.strip(),
        language,
        theme="monokai",
        line_numbers=True,
        word_wrap=True
    )
    return Panel(
        syntax,
        title=f"[cyan]{panel_title}[/cyan]",
        border_style="border",
        box=box.ROUNDED
    )

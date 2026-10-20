"""Command Line Interface for openapi-spec-linter."""

import fnmatch
import os
import sys
from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console
from rich.table import Table

from . import __version__
from .config import LinterConfig, create_default_config_file
from .loader import load_spec
from .models import LintResult, Severity
from .reporter import JsonReporter, JUnitReporter, MarkdownReporter, TerminalReporter
from .rules import RuleRegistry


def find_spec_files(paths: List[str], recursive: bool = True, ignore_patterns: Optional[List[str]] = None) -> List[str]:
    """Finds OpenAPI spec files (.yaml, .yml, .json) in given files and directories."""
    spec_extensions = {".yaml", ".yml", ".json"}
    found_files = []
    ignore_patterns = ignore_patterns or []

    for path_str in paths:
        p = Path(path_str)
        if not p.exists():
            found_files.append(path_str)  # Keep it so loader can report 'File not found'
            continue

        if p.is_file():
            found_files.append(str(p))
        elif p.is_dir():
            pattern = "**/*" if recursive else "*"
            for sub_p in p.glob(pattern):
                if sub_p.is_file() and sub_p.suffix.lower() in spec_extensions:
                    rel_path = str(sub_p)
                    # Check ignore patterns
                    ignored = False
                    for pat in ignore_patterns:
                        if fnmatch.fnmatch(rel_path, pat) or fnmatch.fnmatch(sub_p.name, pat):
                            ignored = True
                            break
                    if not ignored:
                        found_files.append(rel_path)

    return sorted(list(dict.fromkeys(found_files)))


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(version=__version__, prog_name="openapi-spec-linter")
def cli():
    """openapi-spec-linter: Production-grade OpenAPI v3 specification linter."""
    pass


@cli.command("lint")
@click.argument("files", nargs=-1, required=False, type=click.Path())
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["terminal", "text", "json", "markdown", "junit"], case_sensitive=False),
    default="terminal",
    help="Output report format (terminal, json, markdown, junit).",
)
@click.option(
    "--config",
    "-c",
    "config_path",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Path to custom configuration file.",
)
@click.option(
    "--fail-level",
    type=click.Choice(["error", "warning", "info"], case_sensitive=False),
    default=None,
    help="Minimum severity level that will trigger exit code 1 (default: error).",
)
@click.option(
    "--ignore-rule",
    "ignored_rules",
    multiple=True,
    help="Rule ID to disable (can be specified multiple times).",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Write report output to a file instead of stdout.",
)
@click.option(
    "--recursive/--no-recursive",
    "-r/-R",
    default=True,
    help="Recursively scan directories for spec files (default: true).",
)
@click.option(
    "--color/--no-color",
    default=True,
    help="Enable or disable terminal colors.",
)
def lint_cmd(
    files: tuple,
    output_format: str,
    config_path: Optional[str],
    fail_level: Optional[str],
    ignored_rules: tuple,
    output_file: Optional[str],
    recursive: bool,
    color: bool,
):
    """Lint OpenAPI YAML/JSON specification files."""
    # Load configuration
    config = LinterConfig.load(config_path)

    # CLI option overrides
    if fail_level:
        config.fail_level = Severity.from_str(fail_level)

    for rule_id in ignored_rules:
        config.rules[rule_id] = Severity.OFF

    # Discover targets
    target_paths = list(files) if files else ["."]
    spec_files = find_spec_files(target_paths, recursive=recursive, ignore_patterns=config.ignore_files)

    if not spec_files:
        click.echo("No OpenAPI files found to lint.", err=True)
        sys.exit(0)

    results: List[LintResult] = []
    has_fatal_error = False

    for file_path in spec_files:
        context, result = load_spec(file_path)
        if result.parse_error:
            has_fatal_error = True
            results.append(result)
            continue

        if context is not None:
            issues = RuleRegistry.run_all(context, config)
            result.issues.extend(issues)
            results.append(result)

    # Format output
    fmt = output_format.lower()
    if fmt in ("terminal", "text"):
        reporter = TerminalReporter(color=color)
        output_text = reporter.report(results)
    elif fmt == "json":
        reporter = JsonReporter()
        output_text = reporter.report(results)
    elif fmt == "markdown":
        reporter = MarkdownReporter()
        output_text = reporter.report(results)
    elif fmt == "junit":
        reporter = JUnitReporter()
        output_text = reporter.report(results)
    else:
        output_text = TerminalReporter(color=color).report(results)

    # Render output
    if output_file:
        Path(output_file).write_text(output_text, encoding="utf-8")
        click.echo(f"Report written to: {output_file}")
    else:
        try:
            click.echo(output_text)
        except UnicodeEncodeError:
            if hasattr(sys.stdout, "buffer"):
                sys.stdout.buffer.write(output_text.encode(sys.stdout.encoding or "utf-8", errors="replace"))
                sys.stdout.buffer.write(b"\n")
            else:
                click.echo(output_text.encode("ascii", errors="replace").decode("ascii"))

    # Exit code determination
    if has_fatal_error:
        sys.exit(2)

    is_all_clean = all(r.is_clean(config.fail_level) for r in results)
    if not is_all_clean:
        sys.exit(1)

    sys.exit(0)


@cli.command("rules")
@click.option("--json", "json_format", is_flag=True, help="Output rules as JSON.")
def rules_cmd(json_format: bool):
    """List all available OpenAPI linting rules."""
    rules = RuleRegistry.all_rules()

    if json_format:
        data = [
            {
                "id": r.id,
                "name": r.name,
                "category": r.category,
                "default_severity": r.default_severity.value,
                "description": r.description,
            }
            for r in rules
        ]
        import json
        click.echo(json.dumps(data, indent=2))
        return

    console = Console()
    table = Table(title="Available OpenAPI Lint Rules", header_style="bold magenta", expand=True)
    table.add_column("Rule ID", style="bold cyan", width=26)
    table.add_column("Category", style="green", width=12)
    table.add_column("Default", width=10)
    table.add_column("Description", style="white")

    for r in rules:
        sev = r.default_severity.value.upper()
        if r.default_severity == Severity.ERROR:
            sev_badge = f"[red]{sev}[/red]"
        elif r.default_severity == Severity.WARNING:
            sev_badge = f"[yellow]{sev}[/yellow]"
        else:
            sev_badge = f"[cyan]{sev}[/cyan]"

        table.add_row(r.id, r.category, sev_badge, r.description)

    console.print(table)


@cli.command("init")
@click.option(
    "--output",
    "-o",
    "target_path",
    default=None,
    help="Target path for configuration file (defaults to .openapi-linter.yaml).",
)
def init_cmd(target_path: Optional[str]):
    """Generate a default .openapi-linter.yaml configuration file."""
    created_path = create_default_config_file(target_path)
    click.echo(f"Created default configuration file: {created_path}")


def main():
    cli()


if __name__ == "__main__":
    main()

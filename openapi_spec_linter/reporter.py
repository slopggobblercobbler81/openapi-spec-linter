"""Result reporters for terminal, JSON, Markdown, and JUnit XML outputs."""

import json
from typing import List
from xml.sax.saxutils import escape as xml_escape

from .models import LintResult, Severity


class TerminalReporter:
    """Renders formatted terminal output using Rich or ANSI."""

    def __init__(self, color: bool = True):
        self.color = color

    def report(self, results: List[LintResult]) -> str:
        try:
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
            import io

            string_io = io.StringIO()
            console = Console(file=string_io, force_terminal=self.color, width=120)

            total_errors = sum(r.error_count for r in results)
            total_warnings = sum(r.warning_count for r in results)
            total_infos = sum(r.info_count for r in results)

            for res in results:
                console.print(f"\n[bold blue]File:[/bold blue] [cyan]{res.file_path}[/cyan]")
                if res.spec_version:
                    console.print(f"[dim]OpenAPI version: {res.spec_version}[/dim]")

                if res.parse_error:
                    console.print(f"[bold red]PARSE ERROR:[/bold red] {res.parse_error}")

                if not res.issues:
                    console.print("[bold green]  OK: No issues found![/bold green]")
                    continue

                table = Table(show_header=True, header_style="bold magenta", expand=True)
                table.add_column("Location", width=12, style="dim")
                table.add_column("Severity", width=10)
                table.add_column("Rule", width=24)
                table.add_column("Message", style="white")

                for issue in res.issues:
                    loc = f"{issue.line}:{issue.column}" if issue.line else "-"
                    if issue.severity == Severity.ERROR:
                        sev_badge = "[bold red]ERROR[/bold red]"
                    elif issue.severity == Severity.WARNING:
                        sev_badge = "[bold yellow]WARN[/bold yellow]"
                    else:
                        sev_badge = "[bold cyan]INFO[/bold cyan]"

                    msg = issue.message
                    if issue.suggestion:
                        msg += f"\n[dim italic]Suggestion: {issue.suggestion}[/dim italic]"
                    if issue.path:
                        msg += f"\n[dim]Path: {issue.path}[/dim]"

                    table.add_row(loc, sev_badge, issue.rule_id, msg)

                console.print(table)

            # Summary Panel
            status_text = (
                f"[bold red]{total_errors} error(s)[/bold red]  "
                f"[bold yellow]{total_warnings} warning(s)[/bold yellow]  "
                f"[bold cyan]{total_infos} info(s)[/bold cyan]"
            )
            title = "[bold green]PASS[/bold green]" if total_errors == 0 else "[bold red]FAIL[/bold red]"
            console.print(Panel(status_text, title=title, expand=False))

            return string_io.getvalue()
        except ImportError:
            # Fallback simple text formatter
            lines = []
            for res in results:
                lines.append(f"\nFile: {res.file_path}")
                if res.issues:
                    for issue in res.issues:
                        loc = f"{issue.line}:{issue.column}" if issue.line else "-"
                        lines.append(
                            f"  [{issue.severity.value.upper()}] ({loc}) {issue.rule_id}: {issue.message} at {issue.path}"
                        )
                else:
                    lines.append("  OK: No issues found!")
            return "\n".join(lines)


class JsonReporter:
    """Outputs results in structured JSON format."""

    def report(self, results: List[LintResult]) -> str:
        data = {
            "summary": {
                "total_files": len(results),
                "total_errors": sum(r.error_count for r in results),
                "total_warnings": sum(r.warning_count for r in results),
                "total_infos": sum(r.info_count for r in results),
            },
            "files": [r.to_dict() for r in results],
        }
        return json.dumps(data, indent=2)


class MarkdownReporter:
    """Outputs GitHub Flavored Markdown report."""

    def report(self, results: List[LintResult]) -> str:
        total_errors = sum(r.error_count for r in results)
        total_warnings = sum(r.warning_count for r in results)
        total_infos = sum(r.info_count for r in results)

        lines = [
            "# OpenAPI Lint Report",
            "",
            f"**Summary:** ❌ {total_errors} Error(s) | ⚠️ {total_warnings} Warning(s) | ℹ️ {total_infos} Info(s)",
            "",
        ]

        for res in results:
            lines.append(f"## File: `{res.file_path}`")
            if res.spec_version:
                lines.append(f"- **Spec Version:** `{res.spec_version}`")

            if not res.issues:
                lines.append("✅ **Clean! No lint issues found.**\n")
                continue

            lines.append("")
            lines.append("| Location | Severity | Rule ID | Message | Path |")
            lines.append("|---|---|---|---|---|")

            for issue in res.issues:
                loc = f"`{issue.line}:{issue.column}`" if issue.line else "`-`"
                sev = (
                    "🔴 **Error**"
                    if issue.severity == Severity.ERROR
                    else ("🟡 **Warning**" if issue.severity == Severity.WARNING else "🔵 **Info**")
                )
                safe_msg = issue.message.replace("|", "\\|")
                if issue.suggestion:
                    safe_msg += f"<br>_💡 {issue.suggestion.replace('|', chr(92) + '|')}_"
                safe_path = f"`{issue.path}`" if issue.path else "`-`"

                lines.append(f"| {loc} | {sev} | `{issue.rule_id}` | {safe_msg} | {safe_path} |")

            lines.append("")

        return "\n".join(lines)


class JUnitReporter:
    """Outputs JUnit XML format suitable for CI test reports."""

    def report(self, results: List[LintResult]) -> str:
        total_tests = sum(len(r.issues) for r in results)
        total_errors = sum(r.error_count for r in results)
        total_failures = sum(r.warning_count for r in results)

        xml = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml.append(
            f'<testsuites name="openapi-spec-linter" tests="{max(1, total_tests)}" '
            f'errors="{total_errors}" failures="{total_failures}">'
        )

        for res in results:
            xml.append(
                f'  <testsuite name="{xml_escape(res.file_path)}" tests="{max(1, len(res.issues))}" '
                f'errors="{res.error_count}" failures="{res.warning_count}">'
            )

            if not res.issues:
                xml.append(f'    <testcase name="valid_spec" classname="{xml_escape(res.file_path)}" />')
            else:
                for issue in res.issues:
                    cname = f"{xml_escape(res.file_path)}:{issue.line or 0}"
                    tname = f"{issue.rule_id}_{xml_escape(issue.path)}"
                    xml.append(f'    <testcase name="{tname}" classname="{cname}">')
                    if issue.severity == Severity.ERROR:
                        xml.append(
                            f'      <error message="{xml_escape(issue.message)}" type="{issue.rule_id}">'
                            f"{xml_escape(issue.message)}\nPath: {issue.path}\nSuggestion: {issue.suggestion or 'None'}"
                            f"</error>"
                        )
                    elif issue.severity == Severity.WARNING:
                        xml.append(
                            f'      <failure message="{xml_escape(issue.message)}" type="{issue.rule_id}">'
                            f"{xml_escape(issue.message)}\nPath: {issue.path}\nSuggestion: {issue.suggestion or 'None'}"
                            f"</failure>"
                        )
                    xml.append("    </testcase>")

            xml.append("  </testsuite>")

        xml.append("</testsuites>")
        return "\n".join(xml)

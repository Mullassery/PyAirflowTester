"""
Report generation module.

Generates reports in multiple formats: JSON, HTML, Markdown, SARIF.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates analysis reports in multiple formats."""

    def generate(self, format: str, violations: List[Dict[str, Any]], output_path: Path) -> Path:
        """
        Generate report in specified format.

        Args:
            format: Report format (json, html, markdown, sarif)
            violations: List of violations
            output_path: Output file path

        Returns:
            Path to generated report
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating {format} report to {output_path}")

        if format == "json":
            return self.generate_json(violations, output_path)
        elif format == "html":
            return self.generate_html(violations, output_path)
        elif format == "markdown":
            return self.generate_markdown(violations, output_path)
        elif format == "sarif":
            return self.generate_sarif(violations, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def generate_json(self, violations: List[Dict[str, Any]], output_path: Path) -> Path:
        """Generate JSON report."""
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "total_violations": len(violations),
            "violations": violations,
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"JSON report generated: {output_path}")
        return output_path

    def generate_html(self, violations: List[Dict[str, Any]], output_path: Path) -> Path:
        """Generate HTML report."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>PyAirflowTester Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{
            max-width: 1000px; margin: 0 auto; background-color: white;
            padding: 20px; border-radius: 8px;
        }}
        h1 {{ color: #333; }}
        .summary {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .violation {{
            border-left: 4px solid #dc3545; padding: 15px; margin: 10px 0;
            background-color: #f8f9fa;
        }}
        .critical {{ border-left-color: #dc3545; }}
        .high {{ border-left-color: #fd7e14; }}
        .medium {{ border-left-color: #ffc107; }}
        .low {{ border-left-color: #17a2b8; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>PyAirflowTester Analysis Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="summary">
            <h2>Summary</h2>
            <p><strong>Total Violations:</strong> {len(violations)}</p>
        </div>

        <h2>Violations</h2>
        <table>
            <thead>
                <tr>
                    <th>Rule</th>
                    <th>Severity</th>
                    <th>Resource</th>
                    <th>Message</th>
                </tr>
            </thead>
            <tbody>
"""

        for v in violations:
            severity = v.get("severity", "info")
            html += f"""
                <tr class="{severity}">
                    <td>{v.get("rule_id", "")}</td>
                    <td><strong>{severity.upper()}</strong></td>
                    <td>{v.get("affected_resource", "")}</td>
                    <td>{v.get("message", "")}</td>
                </tr>
"""

        html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""

        with open(output_path, "w") as f:
            f.write(html)

        logger.info(f"HTML report generated: {output_path}")
        return output_path

    def generate_markdown(self, violations: List[Dict[str, Any]], output_path: Path) -> Path:
        """Generate Markdown report."""
        md = f"""# PyAirflowTester Analysis Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Total Violations:** {len(violations)}

## Violations

| Rule | Severity | Resource | Message |
|------|----------|----------|---------|
"""

        for v in violations:
            rule_id = v.get("rule_id", "")
            severity = v.get("severity", "info")
            resource = v.get("affected_resource", "")
            message = v.get("message", "")
            md += f"| {rule_id} | {severity} | {resource} | {message} |\n"

        with open(output_path, "w") as f:
            f.write(md)

        logger.info(f"Markdown report generated: {output_path}")
        return output_path

    def generate_sarif(self, violations: List[Dict[str, Any]], output_path: Path) -> Path:
        """Generate SARIF report for GitHub integration."""
        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "PyAirflowTester",
                            "version": "0.1.0",
                            "informationUri": "https://github.com/mullassery/pyairflowtester",
                        }
                    },
                    "results": [
                        {
                            "ruleId": v.get("rule_id", ""),
                            "message": {"text": v.get("message", "")},
                            "level": self._severity_to_level(v.get("severity", "note")),
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {"uri": v.get("affected_resource", "")}
                                    }
                                }
                            ],
                        }
                        for v in violations
                    ],
                }
            ],
        }

        with open(output_path, "w") as f:
            json.dump(sarif, f, indent=2)

        logger.info(f"SARIF report generated: {output_path}")
        return output_path

    @staticmethod
    def _severity_to_level(severity: str) -> str:
        """Convert severity to SARIF level."""
        mapping = {
            "critical": "error",
            "high": "error",
            "medium": "warning",
            "low": "note",
            "info": "note",
        }
        return mapping.get(severity, "note")

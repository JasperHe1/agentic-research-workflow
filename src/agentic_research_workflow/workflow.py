from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PACKAGE_ROOT / "config" / "stages.toml"
DEFAULT_TEMPLATES = PACKAGE_ROOT / "templates"


@dataclass(frozen=True)
class Stage:
    name: str
    file: str
    role: str
    requires: tuple[str, ...]
    approval_gate: str | None = None


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "untitled-project"


def load_stages(config_path: Path = DEFAULT_CONFIG) -> tuple[list[str], dict[str, Stage]]:
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)

    stages: dict[str, Stage] = {}
    for name, values in raw["stages"].items():
        stages[name] = Stage(
            name=name,
            file=values["file"],
            role=values["role"],
            requires=tuple(values.get("requires", [])),
            approval_gate=values.get("approval_gate"),
        )
    return list(raw["order"]), stages


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    boundary = text.find("\n---\n", 4)
    if boundary < 0:
        return {}
    output: dict[str, str] = {}
    for line in text[4:boundary].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            output[key.strip()] = value.strip().strip('"').strip("'")
    return output


def bootstrap(intake_path: Path, output_dir: Path) -> Path:
    intake_path = intake_path.resolve()
    output_dir = output_dir.resolve()
    intake_text = intake_path.read_text(encoding="utf-8")
    metadata = parse_frontmatter(intake_text)
    title = metadata.get("project_title", intake_path.stem)
    slug = metadata.get("project_slug", slugify(title))

    output_dir.mkdir(parents=True, exist_ok=True)
    order, stages = load_stages()

    for name in order:
        stage = stages[name]
        target = output_dir / stage.file
        if name == "intake":
            target.write_text(intake_text, encoding="utf-8")
            continue
        template = DEFAULT_TEMPLATES / stage.file
        content = template.read_text(encoding="utf-8")
        content = content.replace("{{PROJECT_TITLE}}", title)
        content = content.replace("{{PROJECT_SLUG}}", slug)
        target.write_text(content, encoding="utf-8")

    manifest: dict[str, Any] = {
        "project_title": title,
        "project_slug": slug,
        "created": date.today().isoformat(),
        "source_intake": str(intake_path),
        "stage_order": order,
        "stages": {
            name: {
                "file": stages[name].file,
                "role": stages[name].role,
                "requires": list(stages[name].requires),
            }
            for name in order
        },
    }
    (output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_dir


def is_approved(review_path: Path) -> bool:
    if not review_path.exists():
        return False
    return bool(re.search(r"^decision:\s*approve\s*$", review_path.read_text(encoding="utf-8"), re.M | re.I))


def validate(run_dir: Path) -> list[str]:
    run_dir = run_dir.resolve()
    order, stages = load_stages()
    issues: list[str] = []

    if not (run_dir / "run_manifest.json").exists():
        issues.append("Missing run_manifest.json")

    for name in order:
        stage = stages[name]
        target = run_dir / stage.file
        if not target.exists():
            issues.append(f"Missing stage file: {stage.file}")
            continue
        for requirement in stage.requires:
            if not (run_dir / requirement).exists():
                issues.append(f"{stage.file} requires missing file {requirement}")
        if stage.approval_gate and target.stat().st_size > 0:
            gate_path = run_dir / stage.approval_gate
            if not is_approved(gate_path):
                issues.append(f"{stage.file} is blocked until {stage.approval_gate} contains 'decision: approve'")
    return issues


def status(run_dir: Path) -> list[dict[str, str]]:
    order, stages = load_stages()
    rows: list[dict[str, str]] = []
    for name in order:
        stage = stages[name]
        path = run_dir / stage.file
        state = "missing"
        if path.exists():
            text = path.read_text(encoding="utf-8")
            state = "template" if "status: pending" in text else "present"
        if stage.approval_gate and not is_approved(run_dir / stage.approval_gate):
            state = "blocked"
        rows.append({"stage": name, "role": stage.role, "state": state, "file": stage.file})
    return rows

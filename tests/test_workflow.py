from pathlib import Path
import tempfile
import unittest

from agentic_research_workflow.workflow import bootstrap, is_approved, status, validate


ROOT = Path(__file__).resolve().parents[1]


class WorkflowTests(unittest.TestCase):
    def test_bootstrap_creates_manifest_and_stage_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = bootstrap(ROOT / "examples" / "sample_intake.md", Path(temporary) / "run")
            self.assertTrue((run_dir / "run_manifest.json").exists())
            self.assertTrue((run_dir / "03_literature_map.md").exists())
            self.assertEqual(status(run_dir)[6]["state"], "blocked")

    def test_review_gate_requires_explicit_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            review = Path(temporary) / "review.md"
            review.write_text("decision: revise\n", encoding="utf-8")
            self.assertFalse(is_approved(review))
            review.write_text("decision: approve\n", encoding="utf-8")
            self.assertTrue(is_approved(review))

    def test_validation_reports_blocked_paper(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = bootstrap(ROOT / "examples" / "sample_intake.md", Path(temporary) / "run")
            issues = validate(run_dir)
            self.assertTrue(any("blocked" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()


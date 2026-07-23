from pathlib import Path
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]


class LocPolicyTests(unittest.TestCase):
    def read(self, relative_path):
        return (SKILL_ROOT / relative_path).read_text(encoding="utf-8")

    def test_rubric_budgets_only_production_application_loc(self):
        rubric = self.read("reference/4r-rubric.md")

        self.assertIn("200–400 changed production application LOC", rubric)
        self.assertIn("600 production", rubric)
        self.assertIn("app_added_loc + app_removed_loc", rubric)
        self.assertIn("Total additions/deletions and excluded LOC", rubric)

    def test_agent_prompts_exclude_tests_docs_and_auxiliary_content(self):
        reviewer = self.read("reference/reviewer-agent.md")
        implementer = self.read("reference/implementer-agent.md")

        self.assertIn("Use only `app_added_loc + app_removed_loc`", reviewer)
        self.assertIn("Never", reviewer)
        self.assertIn("Tests required to prove the fix do not consume that budget", implementer)

    def test_coverage_only_override_is_report_only(self):
        skill = self.read("SKILL.md")
        rubric = self.read("reference/4r-rubric.md")

        self.assertIn('merge_policy: "coverage-only"', skill)
        self.assertIn("run a single report-only review", skill)
        self.assertIn("4R findings are advisory", rubric)
        self.assertIn("exact-head tests/coverage gate", rubric)


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]


class LocPolicyTests(unittest.TestCase):
    def read(self, relative_path):
        return (SKILL_ROOT / relative_path).read_text(encoding="utf-8")

    def test_rubric_makes_loc_informational_only(self):
        rubric = self.read("reference/4r-rubric.md")

        self.assertIn("PR size and changed LOC are unrestricted", rubric)
        self.assertIn("must not affect severity or approval", rubric)
        self.assertNotIn("200–400", rubric)
        self.assertNotIn("hard ceiling", rubric)

    def test_agent_prompts_do_not_enforce_a_size_budget(self):
        reviewer = self.read("reference/reviewer-agent.md")
        implementer = self.read("reference/implementer-agent.md")

        self.assertIn("never create a finding based on size", reviewer)
        self.assertNotIn("size-budget check", reviewer)
        self.assertNotIn("Size budget", reviewer)
        self.assertNotIn("size budget", implementer)

    def test_coverage_only_override_is_report_only(self):
        skill = self.read("SKILL.md")
        rubric = self.read("reference/4r-rubric.md")

        self.assertIn('merge_policy: "coverage-only"', skill)
        self.assertIn("run a single report-only review", skill)
        self.assertIn("4R findings are advisory", rubric)
        self.assertIn("exact-head tests/coverage gate", rubric)


if __name__ == "__main__":
    unittest.main()

import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location(
    "classify_app_loc",
    Path(__file__).resolve().parents[1] / "scripts" / "classify_app_loc.py",
)
classify_app_loc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(classify_app_loc)


class ClassifyAppLocTests(unittest.TestCase):
    def test_counts_main_application_code(self):
        for path in (
            "lib/screens/cart/cart_bloc.dart",
            "src/routes/orders.ts",
            "app/services/payment.js",
            "web/components/Checkout.vue",
        ):
            with self.subTest(path=path):
                self.assertTrue(classify_app_loc.is_app_code(path))

    def test_excludes_tests_docs_generated_config_assets_and_tooling(self):
        for path in (
            "test/cart_bloc_test.dart",
            "src/orders.spec.ts",
            "docs/architecture.md",
            "lib/models/order.g.dart",
            "config/app.ts",
            "src/runtime.config.ts",
            "assets/checkout.css",
            "scripts/release.py",
            ".github/actions/check.js",
            "migrations/001_orders.js",
            "package.json",
        ):
            with self.subTest(path=path):
                self.assertFalse(classify_app_loc.is_app_code(path))

    def test_summarizes_only_application_loc_for_budget(self):
        stats = classify_app_loc.summarize_numstat([
            "100\t20\tlib/cart.dart\n",
            "250\t10\ttest/cart_test.dart\n",
            "80\t5\tdocs/cart.md\n",
            "40\t2\tsrc/cart.ts\n",
            "-\t-\tassets/logo.png\n",
        ])

        self.assertEqual(stats, {
            "app_changed_files": 2,
            "app_added_loc": 140,
            "app_removed_loc": 22,
            "excluded_changed_files": 2,
            "excluded_added_loc": 330,
            "excluded_removed_loc": 15,
        })


if __name__ == "__main__":
    unittest.main()

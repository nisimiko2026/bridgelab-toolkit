from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch3_3f import (
    REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3F,
    apply_category_normalization_batch3_3f_report,
    build_category_normalization_batch3_3f_report,
)


TARGET = "play/principles/eight-ever-nine-never.md"
PROBABILITY_FOLDER_FILES = (
    "a-priori-and-a-posteriori-probabilities.md",
    "combination-counts.md",
    "conditional-probability.md",
    "missing-honor-probabilities.md",
    "probability-in-bridge.md",
    "suit-distributions.md",
)


def article_text(newline: str = "\n", subcategory: str = "principles") -> str:
    return (
        f"---{newline}title: Eight Ever, Nine Never{newline}"
        f"description: Exact fixture.{newline}category: probability{newline}"
        f"subcategory: {subcategory}{newline}difficulty: Intermediate{newline}"
        f"tags:{newline}- finesse{newline}- principles{newline}- probability{newline}"
        f"systems: []{newline}aliases: []{newline}acronyms: []{newline}"
        f"references:{newline}- retained/reference{newline}last_updated: 2026-08-22{newline}"
        f"status: Draft{newline}unknown: exact{newline}---{newline}"
        f"# Eight Ever, Nine Never{newline}{newline}Body  with  spacing.{newline}"
    )


class CategoryNormalizationBatch33fTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.backup = self.base / "backup"
        self.runner = CliRunner()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def target(self, newline: str = "\n") -> Path:
        path = self.root / TARGET
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(article_text(newline).encode())
        return path

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            ["repair-category-normalization-batch3-3f", "--root", str(self.root), *args],
        )

    def test_exact_selection_exclusions_and_deterministic_immutable_dry_run(self) -> None:
        self.assertEqual(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3F, {TARGET})
        target = self.target()
        excluded = [
            *(f"play/declarer-play/probability/{name}" for name in PROBABILITY_FOLDER_FILES),
            "play/declarer-play/probability/probability-index.md",
            "play/unrelated.md",
            "bidding/unrelated.md",
        ]
        paths = [target]
        for relative in excluded:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(article_text(subcategory="declarer-play").encode())
            paths.append(path)
        before = {path: path.read_bytes() for path in paths}

        first = self.invoke()
        second = self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET CATEGORY |"), 1)
        self.assertIn(TARGET, first.output)
        self.assertIn("Files selected      : 1", first.output)
        for relative in excluded:
            self.assertNotIn(relative, first.output)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)

    def test_category_only_lf_and_crlf_mutation_with_frozen_metadata(self) -> None:
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                target = self.target(newline)
                original = target.read_bytes()
                report = build_category_normalization_batch3_3f_report(self.root)
                self.assertEqual(len(report.actions), 1)
                expected = original.replace(
                    f"category: probability{newline}".encode(),
                    f"category: play{newline}".encode(),
                    1,
                )
                self.assertEqual(report.actions[0].updated, expected)
                self.assertIn(f"subcategory: principles{newline}".encode(), expected)
                self.assertIn(f"- finesse{newline}".encode(), expected)
                self.assertIn(f"- principles{newline}".encode(), expected)
                self.assertIn(f"- probability{newline}".encode(), expected)
                self.assertNotIn(f"- play{newline}".encode(), expected)

    def test_stale_category_subcategory_and_tag_preconditions(self) -> None:
        target = self.target()
        original = target.read_bytes()
        for old, new, message in (
            (b"category: probability", b"category: other", "category precondition"),
            (b"category: probability", b"category:  probability", "Unsafe category line"),
            (b"subcategory: principles", b"subcategory: declarer-play", "frozen-subcategory"),
            (b"- finesse", b"- changed", "frozen-tag"),
            (b"- finesse\n- principles", b"- principles\n- finesse", "frozen-tag"),
            (b"- probability", b"- probability\n- extra", "frozen-tag"),
            (b"- probability", b"- play", "frozen-tag"),
        ):
            target.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_category_normalization_batch3_3f_report(self.root)
            target.write_bytes(original)

    def test_complete_byte_stale_plan_backup_and_overwrite_contract(self) -> None:
        target = self.target()
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_category_normalization_batch3_3f_report(self.root)
        target.write_bytes(target.read_bytes() + b"stale body change\n")
        stale = target.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_category_normalization_batch3_3f_report(report, self.root, self.backup)
        self.assertEqual(target.read_bytes(), stale)
        self.assertFalse(self.backup.exists())

        target.write_bytes(report.actions[0].original)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_category_normalization_batch3_3f_report(report, self.root, self.backup)

    def test_path_preserving_backup_and_atomic_replacement_failure(self) -> None:
        target = self.target()
        original = target.read_bytes()
        with patch(
            "metadata.category_normalization_batch3_3f._atomic_write",
            side_effect=OSError("atomic replacement failed"),
        ):
            result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertNotEqual(result.exit_code, 0)
        self.assertEqual(target.read_bytes(), original)
        self.assertEqual((self.backup / TARGET).read_bytes(), original)

    def test_idempotence_explicit_root_and_cli_help(self) -> None:
        target = self.target()
        result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertEqual(result.exit_code, 0, result.output)
        after = target.read_bytes()
        self.assertEqual(build_category_normalization_batch3_3f_report(self.root).actions, ())
        self.assertEqual(self.invoke("--apply").exit_code, 0)
        self.assertEqual(target.read_bytes(), after)
        self.assertEqual((self.backup / TARGET).read_bytes().count(b"category: probability"), 1)
        help_result = self.runner.invoke(
            app, ["repair-category-normalization-batch3-3f", "--help"]
        )
        self.assertEqual(help_result.exit_code, 0, help_result.output)


if __name__ == "__main__":
    unittest.main()

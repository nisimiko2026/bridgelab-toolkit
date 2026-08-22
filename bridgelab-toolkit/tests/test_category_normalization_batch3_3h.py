from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch3_3h import (
    REQUIRED_TAGS,
    REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3H,
    apply_category_normalization_batch3_3h_report,
    build_category_normalization_batch3_3h_report,
)


TARGET = "play/declarer-play/general-techniques/establishing-suits.md"


def article_text(newline: str = "\n") -> str:
    tag_lines = "".join(f"  - {tag}{newline}" for tag in REQUIRED_TAGS)
    return (
        f"---{newline}title: Establishing Suits{newline}"
        f"description: Exact fixture.{newline}category: Declarer Play{newline}"
        f"subcategory: declarer-play{newline}difficulty: Intermediate{newline}"
        f"tags:{newline}{tag_lines}systems: []{newline}aliases: []{newline}"
        f"acronyms: []{newline}references:{newline}  - retained/reference{newline}"
        f"last_updated: 2026-08-22{newline}status: Draft{newline}unknown: exact{newline}"
        f"---{newline}# Establishing Suits{newline}{newline}Body  with  spacing.{newline}"
    )


class CategoryNormalizationBatch33hTests(unittest.TestCase):
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
            ["repair-category-normalization-batch3-3h", "--root", str(self.root), *args],
        )

    def test_exact_selection_exclusions_and_deterministic_immutable_dry_run(self) -> None:
        self.assertEqual(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3H, {TARGET})
        target = self.target()
        excluded = []
        for name in (
            "avoidance-play.md",
            "communication.md",
            "ducking.md",
            "entry-management-technique.md",
            "general-techniques-index.md",
            "safety-play.md",
        ):
            path = target.parent / name
            path.write_bytes(article_text().encode())
            excluded.append(path)
        paths = [target, *excluded]
        before = {path: path.read_bytes() for path in paths}

        first = self.invoke()
        second = self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET CATEGORY |"), 1)
        self.assertIn(TARGET, first.output)
        for path in excluded:
            self.assertNotIn(path.name, first.output)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)

    def test_category_only_lf_crlf_exact_tag_order_and_subcategory(self) -> None:
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                target = self.target(newline)
                original = target.read_bytes()
                report = build_category_normalization_batch3_3h_report(self.root)
                expected = original.replace(
                    f"category: Declarer Play{newline}".encode(),
                    f"category: play{newline}".encode(),
                    1,
                )
                self.assertEqual(report.actions[0].updated, expected)
                self.assertIn(f"subcategory: declarer-play{newline}".encode(), expected)
                positions = [expected.index(f"  - {tag}".encode()) for tag in REQUIRED_TAGS]
                self.assertEqual(positions, sorted(positions))
                self.assertIn(f"  - declarer play{newline}".encode(), expected)
                self.assertNotIn(f"  - play{newline}".encode(), expected)

    def test_stale_category_subcategory_tag_and_broad_tag_failures(self) -> None:
        target = self.target()
        original = target.read_bytes()
        for old, new, message in (
            (b"category: Declarer Play", b"category: Other", "category precondition"),
            (b"category: Declarer Play", b"category:  Declarer Play", "Unsafe category line"),
            (b"subcategory: declarer-play", b"subcategory: principles", "frozen-subcategory"),
            (b"  - declarer play", b"  - changed", "frozen-tag"),
            (b"  - finesse\n  - forcing", b"  - forcing\n  - finesse", "frozen-tag"),
            (b"  - ruff", b"  - ruff\n  - play", "frozen-tag"),
        ):
            target.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_category_normalization_batch3_3h_report(self.root)
            target.write_bytes(original)

    def test_complete_byte_stale_plan_and_backup_contract(self) -> None:
        target = self.target()
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_category_normalization_batch3_3h_report(self.root)
        target.write_bytes(target.read_bytes() + b"stale body change\n")
        stale = target.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_category_normalization_batch3_3h_report(report, self.root, self.backup)
        self.assertEqual(target.read_bytes(), stale)
        self.assertFalse(self.backup.exists())

        target.write_bytes(report.actions[0].original)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_category_normalization_batch3_3h_report(report, self.root, self.backup)

    def test_path_preserving_backup_and_atomic_replacement_failure(self) -> None:
        target = self.target()
        original = target.read_bytes()
        with patch(
            "metadata.category_normalization_batch3_3h._atomic_write",
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
        self.assertEqual(build_category_normalization_batch3_3h_report(self.root).actions, ())
        self.assertEqual(self.invoke("--apply").exit_code, 0)
        self.assertEqual(target.read_bytes(), after)
        self.assertIn(b"  - declarer play", after)
        help_result = self.runner.invoke(
            app, ["repair-category-normalization-batch3-3h", "--help"]
        )
        self.assertEqual(help_result.exit_code, 0, help_result.output)


if __name__ == "__main__":
    unittest.main()

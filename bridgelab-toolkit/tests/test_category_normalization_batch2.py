from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch2 import (
    REVIEWED_CATEGORY_NORMALIZATION_BATCH2,
    apply_category_normalization_batch2_report,
    build_category_normalization_batch2_report,
)
from metadata.sentinel_cleanup import _atomic_write


def article_text(newline: str = "\n") -> str:
    return (
        f"---{newline}title: Reviewed{newline}description: Preserve exact bytes.{newline}"
        f"category: Play{newline}subcategory: Planning{newline}"
        f"difficulty: Intermediate{newline}tags:{newline}- play{newline}- retained{newline}"
        f"systems: []{newline}aliases: []{newline}acronyms: []{newline}references: []{newline}"
        f"last_updated: 2026-08-18{newline}status: Draft{newline}unknown_field: exact{newline}"
        f"---{newline}# Reviewed{newline}{newline}Body  with  spacing.{newline}"
    )


class CategoryNormalizationBatch2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.backup = self.base / "backup"
        self.runner = CliRunner()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode())
        return path

    def targets(self) -> dict[str, Path]:
        return {
            relative: self.write(relative, article_text("\r\n" if index == 0 else "\n"))
            for index, relative in enumerate(sorted(REVIEWED_CATEGORY_NORMALIZATION_BATCH2))
        }

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            ["repair-category-normalization-batch2", "--root", str(self.root), *args],
        )

    def test_dry_run_exact_scope_and_apply_preserves_unrelated_bytes(self) -> None:
        targets = self.targets()
        other = self.write("play/other.md", article_text())
        before = {path: path.read_bytes() for path in [*targets.values(), other]}
        dry = self.invoke()
        self.assertEqual(dry.exit_code, 0, dry.output)
        self.assertEqual(dry.output.count("SET CATEGORY |"), 4)
        self.assertIn("Files selected      : 4", dry.output)
        self.assertIn("Tag changes         : 0", dry.output)
        self.assertNotIn("play/other.md", dry.output)
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        applied = self.invoke("--apply", "--backup", str(self.backup))
        self.assertEqual(applied.exit_code, 0, applied.output)
        for relative, path in targets.items():
            original = before[path]
            ending = b"\r\n" if b"\r\n" in original else b"\n"
            expected = original.replace(
                b"category: Play" + ending, b"category: play" + ending, 1
            )
            self.assertEqual(path.read_bytes(), expected)
            self.assertEqual((self.backup / relative).read_bytes(), original)
            self.assertIn(b"- play" + ending, expected)
            self.assertIn(b"subcategory: Planning" + ending, expected)
            self.assertIn(b"last_updated: 2026-08-18" + ending, expected)
            self.assertIn(b"Body  with  spacing." + ending, expected)

    def test_apply_requires_backup_and_stale_report_aborts(self) -> None:
        targets = self.targets()
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_category_normalization_batch2_report(self.root)
        stale = list(targets.values())[1]
        stale.write_bytes(stale.read_bytes() + b"stale\n")
        before = {path: path.read_bytes() for path in targets.values()}
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_category_normalization_batch2_report(report, self.root, self.backup)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, before)
        self.assertFalse(self.backup.exists())

    def test_tag_precondition_and_existing_backup_are_refused(self) -> None:
        targets = self.targets()
        path = list(targets.values())[0]
        original = path.read_bytes()
        path.write_bytes(original.replace(b"- play", b"- absent", 1))
        with self.assertRaisesRegex(RuntimeError, "canonical-tag"):
            build_category_normalization_batch2_report(self.root)
        path.write_bytes(original)
        report = build_category_normalization_batch2_report(self.root)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_category_normalization_batch2_report(report, self.root, self.backup)

    def test_mid_batch_failure_has_all_backups(self) -> None:
        targets = self.targets()
        originals = {relative: path.read_bytes() for relative, path in targets.items()}
        calls = 0

        def fail_second(path: Path, content: bytes) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("second failed")
            _atomic_write(path, content)

        with patch("metadata.category_normalization_batch2._atomic_write", side_effect=fail_second):
            result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertNotEqual(result.exit_code, 0)
        self.assertNotIn("Files updated", result.output)
        ordered = sorted(REVIEWED_CATEGORY_NORMALIZATION_BATCH2)
        self.assertNotEqual(targets[ordered[0]].read_bytes(), originals[ordered[0]])
        for relative in ordered[1:]:
            self.assertEqual(targets[relative].read_bytes(), originals[relative])
        for relative, original in originals.items():
            self.assertEqual((self.backup / relative).read_bytes(), original)

    def test_idempotence_root_and_help(self) -> None:
        targets = self.targets()
        self.assertEqual(self.invoke("--apply", "--backup", str(self.backup)).exit_code, 0)
        after = {path: path.read_bytes() for path in targets.values()}
        self.assertEqual(build_category_normalization_batch2_report(self.root).actions, ())
        second = self.invoke("--apply")
        help_result = self.runner.invoke(
            app, ["repair-category-normalization-batch2", "--help"]
        )
        self.assertEqual(second.exit_code, 0, second.output)
        self.assertIn("Files to update     : 0", second.output)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, after)
        self.assertEqual(help_result.exit_code, 0, help_result.output)


if __name__ == "__main__":
    unittest.main()

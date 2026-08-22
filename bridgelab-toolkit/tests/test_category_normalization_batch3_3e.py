from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch3_3e import (
    REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3E,
    apply_category_normalization_batch3_3e_report,
    build_category_normalization_batch3_3e_report,
)
from metadata.sentinel_cleanup import _atomic_write


def article_text(newline: str = "\n") -> str:
    return (
        f"---{newline}title: Reviewed Probability{newline}"
        f"description: Exact fixture.{newline}category: probability{newline}"
        f"subcategory: declarer-play{newline}difficulty: Advanced{newline}"
        f"tags:{newline}  - declarer-play{newline}  - finesse{newline}"
        f"  - probability{newline}systems: []{newline}aliases: []{newline}"
        f"acronyms: []{newline}references:{newline}  - retained/reference{newline}"
        f"last_updated: 2026-08-22{newline}status: Draft{newline}unknown: exact{newline}"
        f"---{newline}# Reviewed Probability{newline}{newline}"
        f"Body  with  spacing.{newline}"
    )


class CategoryNormalizationBatch33eTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.backup = self.base / "backup"
        self.runner = CliRunner()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def targets(self) -> dict[str, Path]:
        result = {}
        for index, relative in enumerate(sorted(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3E)):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(article_text("\r\n" if index % 2 == 0 else "\n").encode())
            result[relative] = path
        return result

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            ["repair-category-normalization-batch3-3e", "--root", str(self.root), *args],
        )

    def test_exact_selection_exclusions_and_deterministic_immutable_dry_run(self) -> None:
        targets = self.targets()
        excluded = {
            "play/declarer-play/probability/probability-index.md": article_text(),
            "play/principles/eight-ever-nine-never.md": article_text().replace(
                "subcategory: declarer-play", "subcategory: principles"
            ),
            "play/unrelated.md": article_text(),
        }
        excluded_paths = []
        for relative, content in excluded.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.encode())
            excluded_paths.append(path)
        all_paths = [*targets.values(), *excluded_paths]
        before = {path: path.read_bytes() for path in all_paths}

        first = self.invoke()
        second = self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET CATEGORY |"), 6)
        self.assertIn("Files selected      : 6", first.output)
        for relative in excluded:
            self.assertNotIn(relative, first.output)
        self.assertEqual({path: path.read_bytes() for path in all_paths}, before)

    def test_exact_category_only_lf_crlf_and_frozen_metadata(self) -> None:
        targets = self.targets()
        originals = {relative: path.read_bytes() for relative, path in targets.items()}
        result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertEqual(result.exit_code, 0, result.output)
        for relative, path in targets.items():
            original = originals[relative]
            ending = b"\r\n" if b"\r\n" in original else b"\n"
            expected = original.replace(
                b"category: probability" + ending, b"category: play" + ending, 1
            )
            self.assertEqual(path.read_bytes(), expected)
            self.assertEqual((self.backup / relative).read_bytes(), original)
            self.assertIn(b"subcategory: declarer-play" + ending, expected)
            self.assertIn(b"  - probability" + ending, expected)
            self.assertNotIn(b"  - play" + ending, expected)

    def test_precondition_failures(self) -> None:
        targets = self.targets()
        path = targets[sorted(targets)[0]]
        original = path.read_bytes()
        for old, new, message in (
            (b"category: probability", b"category: other", "category precondition"),
            (b"category: probability", b"category:  probability", "Unsafe category line"),
            (b"subcategory: declarer-play", b"subcategory: principles", "frozen-subcategory"),
            (b"  - finesse", b"  - play", "frozen-tag"),
            (b"tags:", b"tags: invalid", "frozen-tag"),
        ):
            path.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_category_normalization_batch3_3e_report(self.root)
            path.write_bytes(original)
        path.unlink()
        with self.assertRaisesRegex(RuntimeError, "missing"):
            build_category_normalization_batch3_3e_report(self.root)

    def test_complete_byte_stale_plan_and_backup_contract(self) -> None:
        targets = self.targets()
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_category_normalization_batch3_3e_report(self.root)
        stale = targets[sorted(targets)[-1]]
        stale.write_bytes(stale.read_bytes() + b"stale body change\n")
        before = {path: path.read_bytes() for path in targets.values()}
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_category_normalization_batch3_3e_report(report, self.root, self.backup)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, before)
        self.assertFalse(self.backup.exists())

        stale.write_bytes(report.actions[-1].original)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_category_normalization_batch3_3e_report(report, self.root, self.backup)

    def test_atomic_replacement_failure_stops_remaining_writes(self) -> None:
        targets = self.targets()
        originals = {relative: path.read_bytes() for relative, path in targets.items()}
        calls = 0

        def fail_second(path: Path, content: bytes) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("second atomic replacement failed")
            _atomic_write(path, content)

        with patch(
            "metadata.category_normalization_batch3_3e._atomic_write",
            side_effect=fail_second,
        ):
            result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertNotEqual(result.exit_code, 0)
        ordered = sorted(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3E)
        self.assertNotEqual(targets[ordered[0]].read_bytes(), originals[ordered[0]])
        for relative in ordered[1:]:
            self.assertEqual(targets[relative].read_bytes(), originals[relative])
        for relative, original in originals.items():
            self.assertEqual((self.backup / relative).read_bytes(), original)

    def test_idempotence_explicit_root_and_cli_help(self) -> None:
        targets = self.targets()
        self.assertEqual(
            self.invoke("--apply", "--backup", str(self.backup)).exit_code, 0
        )
        after = {path: path.read_bytes() for path in targets.values()}
        self.assertEqual(build_category_normalization_batch3_3e_report(self.root).actions, ())
        self.assertEqual(self.invoke("--apply").exit_code, 0)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, after)
        help_result = self.runner.invoke(
            app, ["repair-category-normalization-batch3-3e", "--help"]
        )
        self.assertEqual(help_result.exit_code, 0, help_result.output)


if __name__ == "__main__":
    unittest.main()

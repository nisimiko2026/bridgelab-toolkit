from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch3_3d import (
    REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3D,
    apply_category_normalization_batch3_3d_report,
    build_category_normalization_batch3_3d_report,
)
from metadata.sentinel_cleanup import _atomic_write


def article_text(newline: str = "\n") -> str:
    return (
        f"---{newline}title: Reviewed Endgame Defense{newline}"
        f"description: Exact fixture.{newline}category: Defensive Play{newline}"
        f"subcategory: Defensive Techniques{newline}difficulty: Advanced{newline}"
        f"tags:{newline}  - defensive play{newline}  - retained{newline}systems: []{newline}"
        f"aliases: []{newline}acronyms: []{newline}references:{newline}"
        f"  - retained/reference{newline}last_updated: 2026-08-19{newline}"
        f"status: Draft{newline}unknown: exact{newline}---{newline}"
        f"# Reviewed Endgame Defense{newline}{newline}Body  with  spacing.{newline}"
    )


class CategoryNormalizationBatch33dTests(unittest.TestCase):
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
        for index, relative in enumerate(sorted(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3D)):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(article_text("\r\n" if index == 0 else "\n").encode())
            result[relative] = path
        return result

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            ["repair-category-normalization-batch3-3d", "--root", str(self.root), *args],
        )

    def test_exact_selection_deterministic_dry_run_and_byte_preserving_apply(self) -> None:
        targets = self.targets()
        other = self.root / "play/defence/endgame-defence/other.md"
        other.write_bytes(article_text().encode())
        before = {path: path.read_bytes() for path in [*targets.values(), other]}

        first = self.invoke()
        second = self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET CATEGORY |"), 2)
        self.assertIn("Files selected      : 2", first.output)
        self.assertNotIn("other.md", first.output)
        self.assertEqual({path: path.read_bytes() for path in before}, before)

        applied = self.invoke("--apply", "--backup", str(self.backup))
        self.assertEqual(applied.exit_code, 0, applied.output)
        for relative, path in targets.items():
            original = before[path]
            ending = b"\r\n" if b"\r\n" in original else b"\n"
            expected = original.replace(
                b"category: Defensive Play" + ending,
                b"category: play" + ending,
                1,
            )
            self.assertEqual(path.read_bytes(), expected)
            self.assertEqual((self.backup / relative).read_bytes(), original)
            self.assertIn(b"subcategory: Defensive Techniques" + ending, expected)
            self.assertIn(b"  - defensive play" + ending, expected)
            self.assertNotIn(b"  - play" + ending, expected)
        self.assertEqual(other.read_bytes(), before[other])

    def test_category_tag_and_subcategory_preconditions(self) -> None:
        targets = self.targets()
        path = targets[sorted(targets)[0]]
        original = path.read_bytes()
        for old, new, message in (
            (b"category: Defensive Play", b"category: Other", "category precondition"),
            (b"  - defensive play", b"  - changed", "frozen-tag"),
            (b"  - retained", b"  - play", "frozen-tag"),
            (
                b"subcategory: Defensive Techniques",
                b"subcategory: Other",
                "frozen-subcategory",
            ),
        ):
            path.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_category_normalization_batch3_3d_report(self.root)
            path.write_bytes(original)

    def test_stale_plan_backup_requirements_and_overwrite_refusal(self) -> None:
        targets = self.targets()
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_category_normalization_batch3_3d_report(self.root)
        stale = targets[sorted(targets)[1]]
        stale.write_bytes(stale.read_bytes() + b"stale\n")
        before = {path: path.read_bytes() for path in targets.values()}
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_category_normalization_batch3_3d_report(report, self.root, self.backup)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, before)
        self.assertFalse(self.backup.exists())

        stale.write_bytes(report.actions[1].original)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_category_normalization_batch3_3d_report(report, self.root, self.backup)

    def test_atomic_failure_has_all_backups_and_stops_remaining_writes(self) -> None:
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
            "metadata.category_normalization_batch3_3d._atomic_write",
            side_effect=fail_second,
        ):
            result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertNotEqual(result.exit_code, 0)
        ordered = sorted(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3D)
        self.assertNotEqual(targets[ordered[0]].read_bytes(), originals[ordered[0]])
        self.assertEqual(targets[ordered[1]].read_bytes(), originals[ordered[1]])
        for relative, original in originals.items():
            self.assertEqual((self.backup / relative).read_bytes(), original)

    def test_idempotence_explicit_root_and_cli_help(self) -> None:
        targets = self.targets()
        self.assertEqual(
            self.invoke("--apply", "--backup", str(self.backup)).exit_code,
            0,
        )
        after = {path: path.read_bytes() for path in targets.values()}
        self.assertEqual(build_category_normalization_batch3_3d_report(self.root).actions, ())
        self.assertEqual(self.invoke("--apply").exit_code, 0)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, after)
        help_result = self.runner.invoke(
            app, ["repair-category-normalization-batch3-3d", "--help"]
        )
        self.assertEqual(help_result.exit_code, 0, help_result.output)


if __name__ == "__main__":
    unittest.main()

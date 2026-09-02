from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch3_3w import (
    REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3W,
    apply_category_normalization_batch3_3w_report,
    build_category_normalization_batch3_3w_report,
)
from metadata.sentinel_cleanup import _atomic_write


def article_text(
    tags: list[str],
    newline: str = "\n",
    category: str = "planning",
    subcategory: str = "declarer-play",
) -> str:
    tag_lines = "".join(f"  - {tag}{newline}" for tag in tags)
    return (
        f"---{newline}title: Planning Method{newline}description: Exact fixture.{newline}"
        f"category: {category}{newline}subcategory: {subcategory}{newline}difficulty: Intermediate{newline}"
        f"tags:{newline}{tag_lines}systems: []{newline}aliases: []{newline}acronyms: []{newline}"
        f"references:{newline}  - retained/reference{newline}last_updated: 2026-08-24{newline}"
        f"status: Draft{newline}unknown: exact{newline}---{newline}# Planning Method{newline}{newline}Body unchanged.{newline}"
    )


class CategoryNormalizationBatch33wTests(unittest.TestCase):
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
        for index, (relative, tags) in enumerate(
            sorted(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3W.items())
        ):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(
                article_text(tags, "\r\n" if index % 2 == 0 else "\n").encode()
            )
            result[relative] = path
        return result

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            [
                "repair-category-normalization-batch3-3w",
                "--root",
                str(self.root),
                *args,
            ],
        )

    def test_exact_selection_census_and_planning_directory_exclusions(self) -> None:
        self.assertEqual(len(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3W), 3)
        targets = self.targets()
        tags = next(iter(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3W.values()))
        excluded = []
        for relative, category in {
            "play/declarer-play/planning/planning-index.md": "Index",
            "play/declarer-play/planning/planning-the-play.md": "play",
            "play/declarer-play/planning/entry-management.md": "play",
            "play/declarer-play/general-techniques/unrelated.md": "play",
        }.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(article_text(tags, category=category).encode())
            excluded.append(path)
        paths = [*targets.values(), *excluded]
        before = {path: path.read_bytes() for path in paths}
        first, second = self.invoke(), self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET CATEGORY |"), 3)
        self.assertIn("Files selected      : 3", first.output)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)

        extra = self.root / "play/declarer-play/planning/extra.md"
        extra.write_bytes(article_text(tags).encode())
        with self.assertRaisesRegex(RuntimeError, "completeness mismatch"):
            build_category_normalization_batch3_3w_report(self.root)
        extra.unlink()
        targets[sorted(targets)[0]].unlink()
        with self.assertRaisesRegex(RuntimeError, "completeness mismatch"):
            build_category_normalization_batch3_3w_report(self.root)

    def test_category_only_lf_crlf_tags_and_subcategory(self) -> None:
        targets = self.targets()
        originals = {relative: path.read_bytes() for relative, path in targets.items()}
        report = build_category_normalization_batch3_3w_report(self.root)
        self.assertEqual(len(report.actions), 3)
        for action in report.actions:
            original = originals[action.article]
            ending = b"\r\n" if b"\r\n" in original else b"\n"
            expected = original.replace(
                b"category: planning" + ending, b"category: play" + ending, 1
            )
            self.assertEqual(action.updated, expected)
            self.assertIn(b"subcategory: declarer-play" + ending, expected)
            tags = REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3W[action.article]
            positions = [expected.index(f"  - {tag}".encode()) for tag in tags]
            self.assertEqual(positions, sorted(positions))
            self.assertIn(b"  - planning" + ending, expected)
            self.assertNotIn(b"  - play" + ending, expected)

    def test_stale_category_subcategory_and_tag_failures(self) -> None:
        targets = self.targets()
        relative = sorted(targets)[0]
        path = targets[relative]
        tags = REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3W[relative]
        original = path.read_bytes()
        first, second = tags[:2]
        for old, new, message in (
            (
                b"category: planning",
                b"category: Declarer Play",
                "completeness mismatch",
            ),
            (b"category: planning", b"category:  planning", "Unsafe category line"),
            (
                b"subcategory: declarer-play",
                b"subcategory: planning",
                "frozen-subcategory",
            ),
            (b"  - planning", b"  - changed", "frozen-tag"),
            (b"  - planning", b"  - play", "frozen-tag"),
            (
                f"  - {first}\r\n  - {second}".encode(),
                f"  - {second}\r\n  - {first}".encode(),
                "frozen-tag",
            ),
        ):
            path.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_category_normalization_batch3_3w_report(self.root)
            path.write_bytes(original)

    def test_stale_plan_apply_and_backup_guards(self) -> None:
        targets = self.targets()
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_category_normalization_batch3_3w_report(self.root)
        stale = targets[sorted(targets)[-1]]
        stale.write_bytes(stale.read_bytes() + b"stale body change\n")
        before = {path: path.read_bytes() for path in targets.values()}
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_category_normalization_batch3_3w_report(
                report, self.root, self.backup
            )
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, before)
        self.assertFalse(self.backup.exists())
        stale.write_bytes(report.actions[-1].original)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_category_normalization_batch3_3w_report(
                report, self.root, self.backup
            )

    def test_path_preserving_backups_and_atomic_failure(self) -> None:
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
            "metadata.category_normalization_batch3_3w._atomic_write",
            side_effect=fail_second,
        ):
            result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertNotEqual(result.exit_code, 0)
        ordered = sorted(targets)
        self.assertNotEqual(targets[ordered[0]].read_bytes(), originals[ordered[0]])
        for relative in ordered[1:]:
            self.assertEqual(targets[relative].read_bytes(), originals[relative])
        for relative, original in originals.items():
            self.assertEqual((self.backup / relative).read_bytes(), original)

    def test_idempotence_explicit_root_and_cli_help(self) -> None:
        targets = self.targets()
        result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertEqual(result.exit_code, 0, result.output)
        after = {path: path.read_bytes() for path in targets.values()}
        self.assertEqual(
            build_category_normalization_batch3_3w_report(self.root).actions, ()
        )
        self.assertEqual(self.invoke("--apply").exit_code, 0)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, after)
        help_result = self.runner.invoke(
            app, ["repair-category-normalization-batch3-3w", "--help"]
        )
        self.assertEqual(help_result.exit_code, 0, help_result.output)


if __name__ == "__main__":
    unittest.main()

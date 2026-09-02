from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch3_3g import (
    REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3G,
    apply_category_normalization_batch3_3g_report,
    build_category_normalization_batch3_3g_report,
)
from metadata.sentinel_cleanup import _atomic_write


FOURTH = "bidding/conventions/responses/fourth-suit-forcing.md"
NEW_MINOR = "bidding/conventions/responses/new-minor-forcing.md"


def article_text(tags: list[str], newline: str = "\n") -> str:
    tag_lines = "".join(f"  - {tag}{newline}" for tag in tags)
    return (
        f"---{newline}title: Reviewed Response{newline}"
        f"description: Exact fixture.{newline}category: Conventions{newline}"
        f"subcategory: Responses to Openings{newline}difficulty: Intermediate{newline}"
        f"tags: {newline}{tag_lines}systems: []{newline}aliases: []{newline}"
        f"acronyms: []{newline}references:{newline}  - retained/reference{newline}"
        f"last_updated: 2026-08-22{newline}status: Draft{newline}unknown: exact{newline}"
        f"---{newline}# Reviewed Response{newline}{newline}Body  with  spacing.{newline}"
    )


class CategoryNormalizationBatch33gTests(unittest.TestCase):
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
            sorted(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3G.items())
        ):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(article_text(tags, "\r\n" if index == 0 else "\n").encode())
            result[relative] = path
        return result

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            ["repair-category-normalization-batch3-3g", "--root", str(self.root), *args],
        )

    def test_exact_selection_excludes_all_other_responses_and_dry_run_is_immutable(self) -> None:
        self.assertEqual(set(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3G), {FOURTH, NEW_MINOR})
        targets = self.targets()
        excluded = []
        for name in ("checkback-stayman.md", "probability-index.md", "unrelated.md"):
            path = self.root / "bidding/conventions/responses" / name
            path.write_bytes(
                article_text(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3G[FOURTH]).encode()
            )
            excluded.append(path)
        all_paths = [*targets.values(), *excluded]
        before = {path: path.read_bytes() for path in all_paths}

        first = self.invoke()
        second = self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET CATEGORY |"), 2)
        self.assertIn("Files selected      : 2", first.output)
        for path in excluded:
            self.assertNotIn(path.name, first.output)
        self.assertEqual({path: path.read_bytes() for path in all_paths}, before)

    def test_category_only_lf_crlf_exact_tag_order_and_frozen_subcategory(self) -> None:
        targets = self.targets()
        originals = {relative: path.read_bytes() for relative, path in targets.items()}
        report = build_category_normalization_batch3_3g_report(self.root)
        self.assertEqual(len(report.actions), 2)
        for action in report.actions:
            original = originals[action.article]
            ending = b"\r\n" if b"\r\n" in original else b"\n"
            expected = original.replace(
                b"category: Conventions" + ending, b"category: bidding" + ending, 1
            )
            self.assertEqual(action.updated, expected)
            self.assertIn(b"subcategory: Responses to Openings" + ending, expected)
            expected_tags = REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3G[action.article]
            positions = [expected.index(f"  - {tag}".encode()) for tag in expected_tags]
            self.assertEqual(positions, sorted(positions))
            self.assertNotIn(b"  - bidding" + ending, expected)

    def test_stale_category_subcategory_tag_and_broad_tag_failures(self) -> None:
        targets = self.targets()
        path = targets[FOURTH]
        original = path.read_bytes()
        for old, new, message in (
            (b"category: Conventions", b"category: Other", "category precondition"),
            (b"category: Conventions", b"category:  Conventions", "Unsafe category line"),
            (
                b"subcategory: Responses to Openings",
                b"subcategory: conventions",
                "frozen-subcategory",
            ),
            (b"  - cue bid", b"  - changed", "frozen-tag"),
            (b"  - blackwood\r\n  - competitive", b"  - competitive\r\n  - blackwood", "frozen-tag"),
            (b"  - support", b"  - support\r\n  - bidding", "frozen-tag"),
        ):
            path.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_category_normalization_batch3_3g_report(self.root)
            path.write_bytes(original)

    def test_complete_byte_stale_plan_and_backup_contract(self) -> None:
        targets = self.targets()
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_category_normalization_batch3_3g_report(self.root)
        stale = targets[NEW_MINOR]
        stale.write_bytes(stale.read_bytes() + b"stale body change\n")
        before = {path: path.read_bytes() for path in targets.values()}
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_category_normalization_batch3_3g_report(report, self.root, self.backup)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, before)
        self.assertFalse(self.backup.exists())

        stale.write_bytes(report.actions[1].original)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_category_normalization_batch3_3g_report(report, self.root, self.backup)

    def test_path_preserving_backups_and_atomic_replacement_failure(self) -> None:
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
            "metadata.category_normalization_batch3_3g._atomic_write",
            side_effect=fail_second,
        ):
            result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertNotEqual(result.exit_code, 0)
        ordered = sorted(targets)
        self.assertNotEqual(targets[ordered[0]].read_bytes(), originals[ordered[0]])
        self.assertEqual(targets[ordered[1]].read_bytes(), originals[ordered[1]])
        for relative, original in originals.items():
            self.assertEqual((self.backup / relative).read_bytes(), original)

    def test_idempotence_explicit_root_and_cli_help(self) -> None:
        targets = self.targets()
        result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertEqual(result.exit_code, 0, result.output)
        after = {path: path.read_bytes() for path in targets.values()}
        self.assertEqual(build_category_normalization_batch3_3g_report(self.root).actions, ())
        self.assertEqual(self.invoke("--apply").exit_code, 0)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, after)
        help_result = self.runner.invoke(
            app, ["repair-category-normalization-batch3-3g", "--help"]
        )
        self.assertEqual(help_result.exit_code, 0, help_result.output)


if __name__ == "__main__":
    unittest.main()

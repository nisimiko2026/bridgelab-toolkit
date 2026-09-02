from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch3_3i import (
    REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3I,
    apply_category_normalization_batch3_3i_report,
    build_category_normalization_batch3_3i_report,
)
from metadata.sentinel_cleanup import _atomic_write


def article_text(tags: list[str], newline: str = "\n") -> str:
    tag_lines = "".join(f"  - {tag}{newline}" for tag in tags)
    return (
        f"---{newline}title: Reviewed Natural Bid{newline}"
        f"description: Exact fixture.{newline}category: Natural Bidding{newline}"
        f"subcategory: natural-bids{newline}difficulty: Intermediate{newline}"
        f"tags:{newline}{tag_lines}systems: []{newline}aliases: []{newline}"
        f"acronyms: []{newline}references:{newline}  - retained/reference{newline}"
        f"last_updated: 2026-08-22{newline}status: Draft{newline}unknown: exact{newline}"
        f"---{newline}# Reviewed Natural Bid{newline}{newline}Body  with  spacing.{newline}"
    )


class CategoryNormalizationBatch33iTests(unittest.TestCase):
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
            sorted(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3I.items())
        ):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            newline = "\r\n" if index % 2 == 0 else "\n"
            path.write_bytes(article_text(tags, newline).encode())
            result[relative] = path
        return result

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            [
                "repair-category-normalization-batch3-3i",
                "--root",
                str(self.root),
                *args,
            ],
        )

    def test_exact_selection_excludes_responses_indexes_and_dry_run_is_immutable(
        self,
    ) -> None:
        self.assertEqual(len(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3I), 20)
        targets = self.targets()
        default_tags = next(iter(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3I.values()))
        excluded_relatives = (
            "bidding/natural-bids/responses/response-to-1nt.md",
            "bidding/natural-bids/responses/natural-responses-index.md",
            "bidding/natural-bids/opening-bids/natural-opening-bids-index.md",
            "bidding/natural-bids/rebids/natural-rebids-index.md",
            "bidding/unrelated.md",
        )
        excluded = []
        for relative in excluded_relatives:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(article_text(default_tags).encode())
            excluded.append(path)
        paths = [*targets.values(), *excluded]
        before = {path: path.read_bytes() for path in paths}

        first = self.invoke()
        second = self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET CATEGORY |"), 20)
        self.assertIn("Files selected      : 20", first.output)
        for relative in excluded_relatives:
            self.assertNotIn(relative, first.output)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)

    def test_exact_category_only_lf_crlf_tag_order_and_subcategory(self) -> None:
        targets = self.targets()
        originals = {relative: path.read_bytes() for relative, path in targets.items()}
        report = build_category_normalization_batch3_3i_report(self.root)
        self.assertEqual(len(report.actions), 20)
        for action in report.actions:
            original = originals[action.article]
            ending = b"\r\n" if b"\r\n" in original else b"\n"
            expected = original.replace(
                b"category: Natural Bidding" + ending,
                b"category: bidding" + ending,
                1,
            )
            self.assertEqual(action.updated, expected)
            self.assertIn(b"subcategory: natural-bids" + ending, expected)
            tags = REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3I[action.article]
            positions = [expected.index(f"  - {tag}".encode()) for tag in tags]
            self.assertEqual(positions, sorted(positions))
            self.assertIn(b"  - natural bidding" + ending, expected)
            self.assertIn(b"  - natural-bids" + ending, expected)
            self.assertNotIn(b"  - bidding" + ending, expected)

    def test_stale_category_subcategory_and_tag_preconditions(self) -> None:
        targets = self.targets()
        path = targets[sorted(targets)[0]]
        original = path.read_bytes()
        for old, new, message in (
            (b"category: Natural Bidding", b"category: Other", "category precondition"),
            (
                b"category: Natural Bidding",
                b"category:  Natural Bidding",
                "Unsafe category line",
            ),
            (
                b"subcategory: natural-bids",
                b"subcategory: responses",
                "frozen-subcategory",
            ),
            (b"  - natural bidding", b"  - changed", "frozen-tag"),
            (b"  - natural-bids", b"  - bidding", "frozen-tag"),
            (
                b"  - acol\r\n  - competitive",
                b"  - competitive\r\n  - acol",
                "frozen-tag",
            ),
        ):
            path.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_category_normalization_batch3_3i_report(self.root)
            path.write_bytes(original)

    def test_complete_byte_stale_plan_and_backup_contract(self) -> None:
        targets = self.targets()
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_category_normalization_batch3_3i_report(self.root)
        stale = targets[sorted(targets)[-1]]
        stale.write_bytes(stale.read_bytes() + b"stale body change\n")
        before = {path: path.read_bytes() for path in targets.values()}
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_category_normalization_batch3_3i_report(
                report, self.root, self.backup
            )
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, before)
        self.assertFalse(self.backup.exists())

        stale.write_bytes(report.actions[-1].original)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_category_normalization_batch3_3i_report(
                report, self.root, self.backup
            )

    def test_path_preserving_backups_and_atomic_failure_behavior(self) -> None:
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
            "metadata.category_normalization_batch3_3i._atomic_write",
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

    def test_idempotence_explicit_root_apply_and_cli_help(self) -> None:
        targets = self.targets()
        result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertEqual(result.exit_code, 0, result.output)
        after = {path: path.read_bytes() for path in targets.values()}
        self.assertEqual(
            build_category_normalization_batch3_3i_report(self.root).actions, ()
        )
        self.assertEqual(self.invoke("--apply").exit_code, 0)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, after)
        help_result = self.runner.invoke(
            app, ["repair-category-normalization-batch3-3i", "--help"]
        )
        self.assertEqual(help_result.exit_code, 0, help_result.output)


if __name__ == "__main__":
    unittest.main()

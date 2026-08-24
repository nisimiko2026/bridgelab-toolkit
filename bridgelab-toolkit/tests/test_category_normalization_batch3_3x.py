from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch3_3x import (
    REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3X,
    apply_category_normalization_batch3_3x_report,
    build_category_normalization_batch3_3x_report,
)


TAGS = [
    "blackwood",
    "conventions",
    "jacoby",
    "roman keycard",
    "slam",
    "slam bidding",
    "support",
]


def article_text(
    tags: list[str] = TAGS,
    newline: str = "\n",
    category: str = "Slam Bidding",
    subcategory: str = "conventions",
) -> str:
    tag_lines = "".join(f"  - {tag}{newline}" for tag in tags)
    return (
        f"---{newline}title: Slam Trial Bids{newline}description: Exact fixture.{newline}"
        f"category: {category}{newline}subcategory: {subcategory}{newline}difficulty: Intermediate{newline}"
        f"tags:{newline}{tag_lines}systems: []{newline}aliases: []{newline}acronyms: []{newline}"
        f"references:{newline}  - retained/reference{newline}last_updated: 2026-08-24{newline}"
        f"status: Draft{newline}unknown: exact{newline}---{newline}# Slam Trial Bids{newline}{newline}Body unchanged.{newline}"
    )


class CategoryNormalizationBatch33xTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.backup = self.base / "backup"
        self.runner = CliRunner()
        self.relative = next(iter(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3X))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def target(self, newline: str = "\n") -> Path:
        path = self.root / self.relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(article_text(newline=newline).encode())
        return path

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            [
                "repair-category-normalization-batch3-3x",
                "--root",
                str(self.root),
                *args,
            ],
        )

    def test_exact_selection_census_exclusions_and_deterministic_dry_run(self) -> None:
        target = self.target()
        excluded = []
        for relative, category in {
            "bidding/conventions/slam-conventions/other.md": "bidding",
            "bidding/conventions/slam-conventions/slam-index.md": "Index",
            "bidding/conventions/competitive/other.md": "Conventions",
            "play/unrelated.md": "play",
        }.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(article_text(category=category).encode())
            excluded.append(path)
        paths = [target, *excluded]
        before = {path: path.read_bytes() for path in paths}
        first, second = self.invoke(), self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET CATEGORY |"), 1)
        self.assertIn("Files selected      : 1", first.output)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)

        extra = self.root / "bidding/conventions/slam-conventions/extra.md"
        extra.write_bytes(article_text().encode())
        with self.assertRaisesRegex(RuntimeError, "completeness mismatch"):
            build_category_normalization_batch3_3x_report(self.root)
        extra.unlink()
        target.unlink()
        with self.assertRaisesRegex(RuntimeError, "file is missing"):
            build_category_normalization_batch3_3x_report(self.root)

    def test_exact_category_only_lf_crlf_and_frozen_metadata(self) -> None:
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                target = self.target(newline)
                original = target.read_bytes()
                report = build_category_normalization_batch3_3x_report(self.root)
                expected = original.replace(
                    f"category: Slam Bidding{newline}".encode(),
                    f"category: bidding{newline}".encode(),
                    1,
                )
                self.assertEqual(report.actions[0].updated, expected)
                self.assertIn(f"subcategory: conventions{newline}".encode(), expected)
                positions = [expected.index(f"  - {tag}".encode()) for tag in TAGS]
                self.assertEqual(positions, sorted(positions))
                self.assertNotIn(f"  - bidding{newline}".encode(), expected)

    def test_stale_category_subcategory_and_tag_failures(self) -> None:
        target = self.target("\r\n")
        original = target.read_bytes()
        for old, new, message in (
            (
                b"category: Slam Bidding",
                b"category: Convention",
                "category precondition mismatch",
            ),
            (
                b"category: Slam Bidding",
                b"category:  Slam Bidding",
                "Unsafe category line",
            ),
            (b"subcategory: conventions", b"subcategory: slam", "frozen-subcategory"),
            (b"  - slam bidding", b"  - changed", "frozen-tag"),
            (b"  - conventions", b"  - bidding", "frozen-tag"),
            (
                b"  - blackwood\r\n  - conventions",
                b"  - conventions\r\n  - blackwood",
                "frozen-tag",
            ),
        ):
            target.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_category_normalization_batch3_3x_report(self.root)
            target.write_bytes(original)

    def test_stale_plan_apply_and_backup_guards(self) -> None:
        target = self.target()
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_category_normalization_batch3_3x_report(self.root)
        target.write_bytes(target.read_bytes() + b"stale body change\n")
        stale = target.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_category_normalization_batch3_3x_report(
                report, self.root, self.backup
            )
        self.assertEqual(target.read_bytes(), stale)
        self.assertFalse(self.backup.exists())
        target.write_bytes(report.actions[0].original)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_category_normalization_batch3_3x_report(
                report, self.root, self.backup
            )

    def test_path_preserving_backup_and_atomic_failure(self) -> None:
        target = self.target()
        original = target.read_bytes()
        with patch(
            "metadata.category_normalization_batch3_3x._atomic_write",
            side_effect=OSError("atomic replacement failed"),
        ):
            result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertNotEqual(result.exit_code, 0)
        self.assertEqual(target.read_bytes(), original)
        self.assertEqual((self.backup / self.relative).read_bytes(), original)

    def test_idempotence_explicit_root_and_cli_help(self) -> None:
        target = self.target()
        result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertEqual(result.exit_code, 0, result.output)
        after = target.read_bytes()
        self.assertEqual(
            build_category_normalization_batch3_3x_report(self.root).actions, ()
        )
        self.assertEqual(self.invoke("--apply").exit_code, 0)
        self.assertEqual(target.read_bytes(), after)
        help_result = self.runner.invoke(
            app, ["repair-category-normalization-batch3-3x", "--help"]
        )
        self.assertEqual(help_result.exit_code, 0, help_result.output)


if __name__ == "__main__":
    unittest.main()

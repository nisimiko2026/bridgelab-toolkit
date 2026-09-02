from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch3_3t import (
    REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3T,
    apply_category_normalization_batch3_3t_report,
    build_category_normalization_batch3_3t_report,
)


def article_text(
    tags: list[str],
    newline: str = "\n",
    category: str = "Systems",
    subcategory: str = "Ambiguous Club Systems",
) -> str:
    tag_lines = "".join(f"  - {tag}{newline}" for tag in tags)
    return (
        f"---{newline}title: Polish Club{newline}description: Exact fixture.{newline}"
        f"category: {category}{newline}subcategory: {subcategory}{newline}difficulty: Intermediate{newline}"
        f"tags:{newline}{tag_lines}systems: []{newline}aliases: []{newline}acronyms: []{newline}"
        f"references:{newline}  - retained/reference{newline}last_updated: 2026-08-23{newline}"
        f"status: Draft{newline}unknown: exact{newline}---{newline}# Polish Club{newline}{newline}Body unchanged.{newline}"
    )


class CategoryNormalizationBatch33tTests(unittest.TestCase):
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
        relative, (_, tags) = next(
            iter(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3T.items())
        )
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(article_text(tags, newline).encode())
        return path

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            [
                "repair-category-normalization-batch3-3t",
                "--root",
                str(self.root),
                *args,
            ],
        )

    def test_exact_selection_excludes_all_other_systems_files(self) -> None:
        self.assertEqual(len(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3T), 1)
        target = self.target()
        _, tags = next(iter(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3T.values()))
        excluded = []
        for name in ("acol.md", "precision.md", "standard-american.md", "unrelated.md"):
            path = self.root / "bidding/systems" / name
            path.write_bytes(article_text(tags).encode())
            excluded.append(path)
        paths = [target, *excluded]
        before = {path: path.read_bytes() for path in paths}
        first, second = self.invoke(), self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET CATEGORY |"), 1)
        self.assertIn("Files selected      : 1", first.output)
        for name in ("acol.md", "precision.md", "standard-american.md", "unrelated.md"):
            self.assertNotIn(name, first.output)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)

    def test_category_only_lf_crlf_exact_tags_and_subcategory(self) -> None:
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                target = self.target(newline)
                original = target.read_bytes()
                action = build_category_normalization_batch3_3t_report(
                    self.root
                ).actions[0]
                ending = newline.encode()
                expected = original.replace(
                    b"category: Systems" + ending, b"category: bidding" + ending, 1
                )
                self.assertEqual(action.updated, expected)
                self.assertIn(b"subcategory: Ambiguous Club Systems" + ending, expected)
                _, tags = next(iter(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3T.values()))
                positions = [expected.index(f"  - {tag}".encode()) for tag in tags]
                self.assertEqual(positions, sorted(positions))
                self.assertNotIn(b"  - bidding" + ending, expected)

    def test_stale_category_subcategory_and_tag_failures(self) -> None:
        target = self.target("\r\n")
        original = target.read_bytes()
        for old, new, message in (
            (b"category: Systems", b"category: System", "category precondition"),
            (b"category: Systems", b"category:  Systems", "Unsafe category line"),
            (
                b"subcategory: Ambiguous Club Systems",
                b"subcategory: systems",
                "frozen-subcategory",
            ),
            (b"  - ambiguous club systems", b"  - changed", "frozen-tag"),
            (b"  - systems", b"  - bidding", "frozen-tag"),
            (
                b"  - acol\r\n  - ambiguous club systems",
                b"  - ambiguous club systems\r\n  - acol",
                "frozen-tag",
            ),
        ):
            target.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_category_normalization_batch3_3t_report(self.root)
            target.write_bytes(original)

    def test_stale_plan_backup_requirement_and_overwrite_refusal(self) -> None:
        target = self.target()
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_category_normalization_batch3_3t_report(self.root)
        target.write_bytes(target.read_bytes() + b"stale body change\n")
        before = target.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_category_normalization_batch3_3t_report(
                report, self.root, self.backup
            )
        self.assertEqual(target.read_bytes(), before)
        self.assertFalse(self.backup.exists())
        target.write_bytes(report.actions[0].original)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_category_normalization_batch3_3t_report(
                report, self.root, self.backup
            )

    def test_path_preserving_backup_and_atomic_failure(self) -> None:
        target = self.target()
        original = target.read_bytes()
        with patch(
            "metadata.category_normalization_batch3_3t._atomic_write",
            side_effect=OSError("atomic replacement failed"),
        ):
            result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertNotEqual(result.exit_code, 0)
        self.assertEqual(target.read_bytes(), original)
        relative = next(iter(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3T))
        self.assertEqual((self.backup / relative).read_bytes(), original)

    def test_idempotence_explicit_root_apply_and_cli_help(self) -> None:
        target = self.target()
        result = self.invoke("--apply", "--backup", str(self.backup))
        self.assertEqual(result.exit_code, 0, result.output)
        after = target.read_bytes()
        self.assertEqual(
            build_category_normalization_batch3_3t_report(self.root).actions, ()
        )
        self.assertEqual(self.invoke("--apply").exit_code, 0)
        self.assertEqual(target.read_bytes(), after)
        help_result = self.runner.invoke(
            app, ["repair-category-normalization-batch3-3t", "--help"]
        )
        self.assertEqual(help_result.exit_code, 0, help_result.output)


if __name__ == "__main__":
    unittest.main()

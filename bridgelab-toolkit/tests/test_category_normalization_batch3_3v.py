from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from metadata.category_normalization_batch3_3v import (
    REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3V,
    apply_category_normalization_batch3_3v_report,
    build_category_normalization_batch3_3v_report,
)
from metadata.sentinel_cleanup import _atomic_write


def article_text(
    category: str,
    tags: list[str],
    newline: str = "\n",
    subcategory: str = "conventions",
) -> str:
    tag_lines = "".join(f"  - {tag}{newline}" for tag in tags)
    return (
        f"---{newline}title: Defensive Method{newline}description: Exact fixture.{newline}"
        f"category: {category}{newline}subcategory: {subcategory}{newline}difficulty: Intermediate{newline}"
        f"tags:{newline}{tag_lines}systems: []{newline}aliases: []{newline}acronyms: []{newline}"
        f"references:{newline}  - retained/reference{newline}last_updated: 2026-08-24{newline}"
        f"status: Draft{newline}unknown: exact{newline}---{newline}# Defensive Method{newline}{newline}Body unchanged.{newline}"
    )


class CategoryNormalizationBatch33vTests(unittest.TestCase):
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
        for index, (relative, (category, tags)) in enumerate(
            sorted(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3V.items())
        ):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(
                article_text(
                    category, tags, "\r\n" if index % 2 == 0 else "\n"
                ).encode()
            )
            result[relative] = path
        return result

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            [
                "repair-category-normalization-batch3-3v",
                "--root",
                str(self.root),
                *args,
            ],
        )

    def test_exact_selection_exclusion_and_two_family_census(self) -> None:
        self.assertEqual(len(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3V), 4)
        targets = self.targets()
        category, tags = next(iter(REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3V.values()))
        excluded = []
        for relative, other_category in {
            "bidding/conventions/defensive-methods/other.md": "bidding",
            "bidding/conventions/competitive/other.md": "Conventions",
            "bidding/systems/other.md": "Systems",
        }.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(article_text(other_category, tags).encode())
            excluded.append(path)
        paths = [*targets.values(), *excluded]
        before = {path: path.read_bytes() for path in paths}
        first, second = self.invoke(), self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET CATEGORY |"), 4)
        self.assertIn("Files selected      : 4", first.output)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)

        extra = self.root / "bidding/conventions/defensive-methods/extra.md"
        extra.write_bytes(article_text(category, tags).encode())
        with self.assertRaisesRegex(RuntimeError, "completeness mismatch"):
            build_category_normalization_batch3_3v_report(self.root)
        extra.unlink()
        targets[sorted(targets)[0]].unlink()
        with self.assertRaisesRegex(RuntimeError, "completeness mismatch"):
            build_category_normalization_batch3_3v_report(self.root)

    def test_category_only_lf_crlf_tags_and_subcategory(self) -> None:
        targets = self.targets()
        originals = {relative: path.read_bytes() for relative, path in targets.items()}
        report = build_category_normalization_batch3_3v_report(self.root)
        self.assertEqual(len(report.actions), 4)
        for action in report.actions:
            original = originals[action.article]
            ending = b"\r\n" if b"\r\n" in original else b"\n"
            expected = original.replace(
                f"category: {action.observed_category}".encode() + ending,
                b"category: bidding" + ending,
                1,
            )
            self.assertEqual(action.updated, expected)
            self.assertIn(b"subcategory: conventions" + ending, expected)
            tags = REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3V[action.article][1]
            positions = [expected.index(f"  - {tag}".encode()) for tag in tags]
            self.assertEqual(positions, sorted(positions))
            self.assertIn(
                f"  - {action.observed_category.casefold()}".encode() + ending,
                expected,
            )
            self.assertIn(b"  - conventions" + ending, expected)
            self.assertNotIn(b"  - bidding" + ending, expected)

    def test_stale_category_subcategory_and_tag_failures(self) -> None:
        targets = self.targets()
        relative = sorted(targets)[0]
        path = targets[relative]
        category, tags = REVIEWED_CATEGORY_NORMALIZATION_BATCH3_3V[relative]
        original = path.read_bytes()
        first, second = tags[:2]
        for old, new, message in (
            (
                f"category: {category}".encode(),
                b"category: Convention",
                "completeness mismatch",
            ),
            (
                f"category: {category}".encode(),
                f"category:  {category}".encode(),
                "Unsafe category line",
            ),
            (
                b"subcategory: conventions",
                b"subcategory: defensive-methods",
                "frozen-subcategory",
            ),
            (
                f"  - {category.casefold()}".encode(),
                b"  - changed",
                "frozen-tag",
            ),
            (b"  - conventions", b"  - bidding", "frozen-tag"),
            (
                f"  - {first}\r\n  - {second}".encode(),
                f"  - {second}\r\n  - {first}".encode(),
                "frozen-tag",
            ),
        ):
            path.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_category_normalization_batch3_3v_report(self.root)
            path.write_bytes(original)

    def test_stale_plan_apply_and_backup_guards(self) -> None:
        targets = self.targets()
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)
        report = build_category_normalization_batch3_3v_report(self.root)
        stale = targets[sorted(targets)[-1]]
        stale.write_bytes(stale.read_bytes() + b"stale body change\n")
        before = {path: path.read_bytes() for path in targets.values()}
        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_category_normalization_batch3_3v_report(
                report, self.root, self.backup
            )
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, before)
        self.assertFalse(self.backup.exists())
        stale.write_bytes(report.actions[-1].original)
        self.backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_category_normalization_batch3_3v_report(
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
            "metadata.category_normalization_batch3_3v._atomic_write",
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
            build_category_normalization_batch3_3v_report(self.root).actions, ()
        )
        self.assertEqual(self.invoke("--apply").exit_code, 0)
        self.assertEqual({path: path.read_bytes() for path in targets.values()}, after)
        help_result = self.runner.invoke(
            app, ["repair-category-normalization-batch3-3v", "--help"]
        )
        self.assertEqual(help_result.exit_code, 0, help_result.output)


if __name__ == "__main__":
    unittest.main()

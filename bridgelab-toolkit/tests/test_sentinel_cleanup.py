from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from main import app
from metadata.sentinel_cleanup import apply_cleanup, build_cleanup_report


def article_text(
    *,
    difficulty: str = "Intermediate",
    subcategory: str = "conventions",
    tags: tuple[str, ...] = ("opening", "none", "slam"),
    date_line: str = "last_updated: 2026-07-23",
    newline: str = "\n",
) -> str:
    tag_lines = "".join(f"  - {tag}{newline}" for tag in tags)
    return (
        f"---{newline}"
        f"title: Exact Title{newline}"
        f"description: Exact description remains byte-for-byte unchanged.{newline}"
        f"category: bidding{newline}"
        f"subcategory: {subcategory}{newline}"
        f"difficulty: {difficulty}{newline}"
        f"tags:{newline}{tag_lines}"
        f"systems:{newline}  - precision{newline}"
        f"aliases:{newline}  - Existing Alias{newline}"
        f"acronyms: []{newline}"
        f"references:{newline}  - bidding/target{newline}"
        f"{date_line}{newline}"
        f"status: Draft{newline}"
        f"custom_field: preserve me{newline}"
        f"---{newline}"
        f"# Exact Title{newline}{newline}"
        f"Body  with  spacing.{newline}"
    )


class SentinelCleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary_directory.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.backup = self.base / "backup"
        self.runner = CliRunner()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode("utf-8"))
        return path

    def invoke(self, *arguments: str):
        return self.runner.invoke(
            app,
            [
                "sentinel-cleanup",
                "--root",
                str(self.root),
                "--backup",
                str(self.backup),
                *arguments,
            ],
        )

    def test_dry_run_requires_apply_and_changes_no_bytes(self) -> None:
        source = self.write("bidding/topic.md", article_text())
        original = source.read_bytes()

        result = self.invoke()

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Pass --apply", result.output)
        self.assertEqual(source.read_bytes(), original)
        self.assertFalse(self.backup.exists())

    def test_apply_removes_only_exact_lowercase_tags_in_existing_order(self) -> None:
        source = self.write(
            "bidding/topic.md",
            article_text(tags=("opening", "None", "none", "slam", "none")),
        )
        original = source.read_bytes()

        result = self.invoke("--apply")

        self.assertEqual(result.exit_code, 0, result.output)
        updated = source.read_text(encoding="utf-8")
        self.assertIn("  - opening\n  - None\n  - slam\n", updated)
        self.assertNotIn("  - none\n", updated)
        self.assertEqual((self.backup / "bidding/topic.md").read_bytes(), original)

    def test_unindented_yaml_tag_items_are_supported(self) -> None:
        original = article_text().replace(
            "tags:\n  - opening\n  - none\n  - slam\n",
            "tags:\n- opening\n- none\n- slam\n",
        )
        source = self.write("bidding/topic.md", original)

        result = self.invoke("--apply")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("tags:\n- opening\n- slam\n", source.read_text(encoding="utf-8"))

    def test_exempt_difficulty_is_cleared_but_non_exempt_is_report_only(self) -> None:
        exempt = self.write(
            "references/terms.md",
            article_text(difficulty="None", tags=("reference",)),
        )
        non_exempt = self.write(
            "bidding/topic.md",
            article_text(difficulty="None", tags=("bidding",)),
        )

        result = self.invoke("--apply")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("difficulty: ''\n", exempt.read_text(encoding="utf-8"))
        self.assertIn("difficulty: None\n", non_exempt.read_text(encoding="utf-8"))
        self.assertIn("not exempt", result.output)

    def test_subcategory_is_reported_and_never_changed(self) -> None:
        source = self.write(
            "acronyms.md",
            article_text(
                difficulty="None",
                subcategory="None",
                tags=("reference", "none"),
            ),
        )

        result = self.invoke("--apply")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("REPORT ONLY | acronyms.md | subcategory", result.output)
        self.assertIn("subcategory: None\n", source.read_text(encoding="utf-8"))

    def test_dates_unrelated_yaml_body_and_metadata_are_byte_preserved(self) -> None:
        original = article_text(newline="\r\n")
        source = self.write("bidding/topic.md", original)

        result = self.invoke("--apply")

        self.assertEqual(result.exit_code, 0, result.output)
        expected = original.replace("  - none\r\n", "")
        self.assertEqual(source.read_bytes(), expected.encode("utf-8"))
        for value in (
            "last_updated: 2026-07-23\r\n",
            "systems:\r\n  - precision\r\n",
            "references:\r\n  - bidding/target\r\n",
            "status: Draft\r\n",
            "custom_field: preserve me\r\n",
            "Body  with  spacing.\r\n",
        ):
            self.assertIn(value.encode("utf-8"), source.read_bytes())

    def test_stale_precondition_aborts_before_backup_or_repair(self) -> None:
        source = self.write("bidding/topic.md", article_text())
        report = build_cleanup_report(self.root)
        stale = source.read_bytes() + b"external change\n"
        source.write_bytes(stale)

        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_cleanup(report, self.root, self.backup)

        self.assertEqual(source.read_bytes(), stale)
        self.assertFalse(self.backup.exists())

    def test_apply_is_idempotent(self) -> None:
        source = self.write("bidding/topic.md", article_text())
        first = self.invoke("--apply")
        after_first = source.read_bytes()

        second_report = build_cleanup_report(self.root)
        second = self.invoke("--apply")

        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(second.exit_code, 0, second.output)
        self.assertEqual(second_report.actions, ())
        self.assertIn("Files to update              : 0", second.output)
        self.assertEqual(source.read_bytes(), after_first)

    def test_help_and_explicit_root(self) -> None:
        source = self.write("bidding/topic.md", article_text())

        help_result = self.runner.invoke(app, ["sentinel-cleanup", "--help"])
        dry_run = self.invoke()

        self.assertEqual(help_result.exit_code, 0, help_result.output)
        self.assertIn("--apply", help_result.output)
        self.assertEqual(dry_run.exit_code, 0, dry_run.output)
        self.assertIn("bidding/topic.md", dry_run.output)
        self.assertTrue(source.exists())

    def test_reviewed_subcategory_mode_changes_only_two_approved_files(self) -> None:
        approved_root = self.write(
            "bridge-lab-index.md",
            article_text(subcategory="None", tags=("reference",)),
        )
        approved_index = self.write(
            "duplicates/duplicates-index.md",
            article_text(subcategory="None", tags=("duplicate",)),
        )
        unresolved = self.write(
            "acronyms.md",
            article_text(subcategory="None", tags=("reference",)),
        )
        unrelated = self.write(
            "bidding/topic.md",
            article_text(tags=("none",), difficulty="None"),
        )
        originals = {
            path: path.read_bytes()
            for path in (approved_root, approved_index, unresolved, unrelated)
        }

        dry_run = self.invoke("--only-reviewed-empty-subcategories")

        self.assertEqual(dry_run.exit_code, 0, dry_run.output)
        self.assertIn("Files to update              : 2", dry_run.output)
        self.assertIn("Reviewed subcategories clear : 2", dry_run.output)
        self.assertIn("REPORT ONLY | acronyms.md", dry_run.output)
        self.assertNotIn("REMOVE TAG", dry_run.output)
        for path, original in originals.items():
            self.assertEqual(path.read_bytes(), original)

        applied = self.invoke("--only-reviewed-empty-subcategories", "--apply")

        self.assertEqual(applied.exit_code, 0, applied.output)
        for path in (approved_root, approved_index):
            self.assertIn("subcategory: ''\n", path.read_text(encoding="utf-8"))
            self.assertEqual(
                (self.backup / path.relative_to(self.root)).read_bytes(),
                originals[path],
            )
        self.assertEqual(unresolved.read_bytes(), originals[unresolved])
        self.assertEqual(unrelated.read_bytes(), originals[unrelated])

    def test_reviewed_subcategory_preserves_bytes_and_is_idempotent(self) -> None:
        original = article_text(
            subcategory="None",
            tags=("reference",),
            newline="\r\n",
        )
        source = self.write("bridge-lab-index.md", original)

        first = self.invoke("--only-reviewed-empty-subcategories", "--apply")
        expected = original.replace(
            "subcategory: None\r\n",
            "subcategory: ''\r\n",
        )
        second_report = build_cleanup_report(
            self.root,
            only_reviewed_empty_subcategories=True,
        )

        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(source.read_bytes(), expected.encode("utf-8"))
        self.assertIn(b"last_updated: 2026-07-23\r\n", source.read_bytes())
        self.assertIn(b"Body  with  spacing.\r\n", source.read_bytes())
        self.assertEqual(second_report.actions, ())

    def test_reviewed_subcategory_stale_precondition_aborts_before_backup(self) -> None:
        source = self.write(
            "bridge-lab-index.md",
            article_text(subcategory="None", tags=("reference",)),
        )
        report = build_cleanup_report(
            self.root,
            only_reviewed_empty_subcategories=True,
        )
        stale = source.read_bytes() + b"external change\n"
        source.write_bytes(stale)

        with self.assertRaisesRegex(RuntimeError, "precondition mismatch"):
            apply_cleanup(report, self.root, self.backup)

        self.assertEqual(source.read_bytes(), stale)
        self.assertFalse(self.backup.exists())


if __name__ == "__main__":
    unittest.main()

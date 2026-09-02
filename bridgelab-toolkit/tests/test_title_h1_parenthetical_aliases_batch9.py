from __future__ import annotations

import hashlib
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from typer.testing import CliRunner

from main import app
from metadata.sentinel_cleanup import _atomic_write as real_atomic_write
from metadata.title_h1_parenthetical_aliases_batch9 import (
    REVIEWED_ALIASES,
    REVIEWED_POST_SHA256,
    REVIEWED_SOURCE_SHA256,
    REVIEWED_TITLE_H1,
    apply_title_h1_parenthetical_aliases_batch9_report,
    build_title_h1_parenthetical_aliases_batch9_report,
)


def article_text(title: str, h1: str, *, newline: str = "\n") -> bytes:
    return (
        f"---{newline}title: {title}{newline}description: Exact Batch 9A fixture."
        f"{newline}category: bidding{newline}subcategory: conventions{newline}"
        f"difficulty: Advanced{newline}tags:{newline}  - bidding{newline}"
        f"systems: []{newline}aliases: []{newline}acronyms: []{newline}"
        f"references: []{newline}last_updated: '2026-07-27'{newline}"
        f"status: Draft{newline}---{newline}{newline}# {h1}{newline}{newline}"
        f"Opening prose unchanged.{newline}{newline}## Existing Child{newline}{newline}"
        f"Body unchanged.{newline}"
    ).encode("utf-8")


def expected_post(original: bytes, aliases: tuple[str, ...]) -> bytes:
    newline = b"\r\n" if b"\r\n" in original else b"\n"
    replacement = b"aliases:" + newline + newline.join(
        b"  - " + alias.encode("utf-8") for alias in aliases
    )
    return original.replace(b"aliases: []", replacement, 1)


def front_data(content: bytes) -> dict[str, object]:
    text = content.decode("utf-8")
    front = text.split("---", 2)[1]
    return yaml.safe_load(front)


class TitleH1ParentheticalAliasesBatch9Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "knowledge"
        self.root.mkdir()
        self.runner = CliRunner()
        self.paths, source_hashes, post_hashes = self.write_family()
        self.source_patch = patch(
            "metadata.title_h1_parenthetical_aliases_batch9.REVIEWED_SOURCE_SHA256",
            source_hashes,
        )
        self.post_patch = patch(
            "metadata.title_h1_parenthetical_aliases_batch9.REVIEWED_POST_SHA256",
            post_hashes,
        )
        self.source_patch.start()
        self.post_patch.start()

    def tearDown(self) -> None:
        self.post_patch.stop()
        self.source_patch.stop()
        self.temp.cleanup()

    def write_family(
        self, *, newline: str = "\n"
    ) -> tuple[dict[str, Path], dict[str, str], dict[str, str]]:
        paths: dict[str, Path] = {}
        source_hashes: dict[str, str] = {}
        post_hashes: dict[str, str] = {}
        for article, aliases in REVIEWED_ALIASES.items():
            title, h1 = REVIEWED_TITLE_H1[article]
            path = self.root / article
            path.parent.mkdir(parents=True, exist_ok=True)
            content = article_text(title, h1, newline=newline)
            path.write_bytes(content)
            paths[article] = path
            source_hashes[article] = hashlib.sha256(content).hexdigest()
            post_hashes[article] = hashlib.sha256(
                expected_post(content, aliases)
            ).hexdigest()
        return paths, source_hashes, post_hashes

    def invoke(self, *args: str):
        return self.runner.invoke(
            app,
            [
                "repair-title-h1-parenthetical-aliases-batch9",
                "--root",
                str(self.root),
                *args,
            ],
        )

    def test_exact_allowlist_aliases_and_canonical_hash_table_census(self) -> None:
        self.assertEqual(len(REVIEWED_ALIASES), 15)
        self.assertEqual(set(REVIEWED_ALIASES), set(REVIEWED_TITLE_H1))
        self.assertEqual(set(REVIEWED_ALIASES), set(REVIEWED_SOURCE_SHA256))
        self.assertEqual(set(REVIEWED_ALIASES), set(REVIEWED_POST_SHA256))
        self.assertEqual(
            REVIEWED_ALIASES["bidding/systems/benjamin-acol.md"],
            ("Benjaminised Acol", "Benji Acol"),
        )
        report = build_title_h1_parenthetical_aliases_batch9_report(self.root)
        self.assertEqual(
            [action.article for action in report.actions], list(REVIEWED_ALIASES)
        )
        self.assertTrue(
            all(front_data(path.read_bytes())["aliases"] == [] for path in self.paths.values())
        )

    def test_deterministic_dry_run_is_immutable_and_requires_explicit_apply(self) -> None:
        unrelated = self.root / "play/unrelated.md"
        unrelated.parent.mkdir(exist_ok=True)
        unrelated.write_bytes(article_text("Unrelated", "Different"))
        before = {path: path.read_bytes() for path in (*self.paths.values(), unrelated)}
        first, second = self.invoke(), self.invoke()
        self.assertEqual(first.exit_code, 0, first.output)
        self.assertEqual(first.output, second.output)
        self.assertEqual(first.output.count("SET ALIASES |"), 15)
        for expected in (
            "Files selected  : 15",
            "Files to update : 15",
            "Alias fields    : 15",
            "Alias values    : 16",
            "Acronym changes : 0",
            "Title changes   : 0",
            "H1 changes      : 0",
            "Files to back up: 15",
        ):
            self.assertIn(expected, first.output)
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        self.assertFalse((self.base / "backup").exists())
        self.assertNotEqual(self.invoke("--apply").exit_code, 0)

    def test_exact_byte_local_lf_crlf_mutation_freezes_all_other_content(self) -> None:
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                self.paths, source_hashes, post_hashes = self.write_family(newline=newline)
                with (
                    patch(
                        "metadata.title_h1_parenthetical_aliases_batch9."
                        "REVIEWED_SOURCE_SHA256",
                        source_hashes,
                    ),
                    patch(
                        "metadata.title_h1_parenthetical_aliases_batch9."
                        "REVIEWED_POST_SHA256",
                        post_hashes,
                    ),
                ):
                    report = build_title_h1_parenthetical_aliases_batch9_report(self.root)
                for action in report.actions:
                    self.assertEqual(action.updated, expected_post(action.original, action.aliases))
                    original_data = front_data(action.original)
                    updated_data = front_data(action.updated)
                    self.assertEqual(updated_data["aliases"], list(action.aliases))
                    self.assertEqual(updated_data["acronyms"], original_data["acronyms"])
                    self.assertEqual(updated_data["title"], original_data["title"])
                    heading_re = re.compile(rb"^#{1,6}\s+.*$", re.MULTILINE)
                    self.assertEqual(
                        heading_re.findall(action.updated), heading_re.findall(action.original)
                    )
                    self.assertEqual(
                        action.updated.replace(
                            b"aliases:"
                            + (b"\r\n" if newline == "\r\n" else b"\n")
                            + (b"\r\n" if newline == "\r\n" else b"\n").join(
                                b"  - " + alias.encode("utf-8")
                                for alias in action.aliases
                            ),
                            b"aliases: []",
                            1,
                        ),
                        action.original,
                    )

    def test_missing_extra_and_exact_field_value_preconditions(self) -> None:
        article = next(iter(REVIEWED_ALIASES))
        path = self.paths[article]
        original = path.read_bytes()
        path.unlink()
        with self.assertRaisesRegex(RuntimeError, "census mismatch"):
            build_title_h1_parenthetical_aliases_batch9_report(self.root)
        path.write_bytes(original)

        extra = self.root / "play/extra.md"
        extra.parent.mkdir(exist_ok=True)
        extra.write_bytes(article_text("Extra", "Extra (Alias)"))
        with self.assertRaisesRegex(RuntimeError, "census mismatch"):
            build_title_h1_parenthetical_aliases_batch9_report(self.root)
        extra.unlink()

        replacements = (
            (b"aliases: []", b"aliases:\n  - Stale", "aliases precondition|complete-byte"),
            (b"acronyms: []", b"acronyms:\n  - Frozen", "acronyms precondition"),
            (b"title: ", b"title: Stale ", "census mismatch|title precondition"),
            (b"# ", b"# Stale ", "census mismatch|first-H1"),
            (b"Body unchanged.", b"Body changed.", "complete-byte source"),
        )
        for old, new, message in replacements:
            path.write_bytes(original.replace(old, new, 1))
            with self.assertRaisesRegex(RuntimeError, message):
                build_title_h1_parenthetical_aliases_batch9_report(self.root)
            path.write_bytes(original)

    def test_complete_batch_preflight_backup_and_overwrite_guards(self) -> None:
        report = build_title_h1_parenthetical_aliases_batch9_report(self.root)
        backup = self.base / "backup"
        stale = report.actions[-1]
        stale.path.write_bytes(stale.original + b"stale\n")
        with self.assertRaisesRegex(RuntimeError, "complete-byte"):
            apply_title_h1_parenthetical_aliases_batch9_report(report, self.root, backup)
        self.assertFalse(backup.exists())
        self.assertTrue(
            all(
                action.path.read_bytes() == action.original
                for action in report.actions[:-1]
            )
        )
        stale.path.write_bytes(stale.original)
        backup.mkdir()
        with self.assertRaisesRegex(RuntimeError, "already exists"):
            apply_title_h1_parenthetical_aliases_batch9_report(report, self.root, backup)
        backup.rmdir()
        with self.assertRaisesRegex(RuntimeError, "outside canonical knowledge"):
            apply_title_h1_parenthetical_aliases_batch9_report(
                report, self.root, self.root / "backup"
            )

    def test_apply_path_preserving_backup_rollback_and_idempotence(self) -> None:
        report = build_title_h1_parenthetical_aliases_batch9_report(self.root)
        backup = self.base / "rollback-backup"
        calls = 0

        def fail_second(path: Path, content: bytes) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("atomic failure")
            real_atomic_write(path, content)

        with patch(
            "metadata.title_h1_parenthetical_aliases_batch9._atomic_write",
            side_effect=fail_second,
        ):
            with self.assertRaisesRegex(OSError, "atomic failure"):
                apply_title_h1_parenthetical_aliases_batch9_report(
                    report, self.root, backup
                )
        self.assertTrue(
            all(action.path.read_bytes() == action.original for action in report.actions)
        )
        self.assertEqual(
            sorted(path.relative_to(backup).as_posix() for path in backup.rglob("*.md")),
            sorted(REVIEWED_ALIASES),
        )
        for action in report.actions:
            self.assertEqual((backup / action.article).read_bytes(), action.original)

        fresh = self.base / "fresh/knowledge"
        fresh.mkdir(parents=True)
        self.root = fresh
        self.paths, source_hashes, post_hashes = self.write_family()
        final_backup = self.base / "fresh-backup"
        with (
            patch(
                "metadata.title_h1_parenthetical_aliases_batch9.REVIEWED_SOURCE_SHA256",
                source_hashes,
            ),
            patch(
                "metadata.title_h1_parenthetical_aliases_batch9.REVIEWED_POST_SHA256",
                post_hashes,
            ),
        ):
            result = self.invoke("--apply", "--backup", str(final_backup))
            self.assertEqual(result.exit_code, 0, result.output)
            after = {path: path.read_bytes() for path in self.paths.values()}
            idempotent = self.invoke()
        self.assertIn("Files to update : 0", idempotent.output)
        self.assertEqual({path: path.read_bytes() for path in self.paths.values()}, after)

    def test_wrong_roots_help_and_backup_copy_failure_cleanup(self) -> None:
        wrong = self.base / "knowladge"
        wrong.mkdir()
        with self.assertRaisesRegex(RuntimeError, "non-canonical knowledge root"):
            build_title_h1_parenthetical_aliases_batch9_report(wrong)
        stale = self.base / "OneDrive/knowledge"
        stale.mkdir(parents=True)
        with self.assertRaisesRegex(RuntimeError, "outside OneDrive"):
            build_title_h1_parenthetical_aliases_batch9_report(stale)
        help_result = self.runner.invoke(
            app, ["repair-title-h1-parenthetical-aliases-batch9", "--help"]
        )
        self.assertEqual(help_result.exit_code, 0, help_result.output)
        report = build_title_h1_parenthetical_aliases_batch9_report(self.root)
        backup = self.base / "failed-backup"
        with patch(
            "metadata.title_h1_parenthetical_aliases_batch9.shutil.copy2",
            side_effect=OSError("copy failure"),
        ):
            with self.assertRaisesRegex(OSError, "copy failure"):
                apply_title_h1_parenthetical_aliases_batch9_report(
                    report, self.root, backup
                )
        self.assertFalse(backup.exists())
        self.assertTrue(
            all(action.path.read_bytes() == action.original for action in report.actions)
        )


if __name__ == "__main__":
    unittest.main()

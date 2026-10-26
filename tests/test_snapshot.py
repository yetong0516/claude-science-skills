"""Fault-injection checks for the export boundary; no upstream services run."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_snapshot", ROOT / "scripts/verify_snapshot.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class ExportBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("skills", "docs", "catalogs"):
            shutil.copytree(ROOT / name, self.root / name)
        shutil.copy2(ROOT / "SNAPSHOT.json", self.root / "SNAPSHOT.json")

    def manifest(self):
        return json.loads((self.root / "SNAPSHOT.json").read_text())

    def save(self, manifest):
        (self.root / "SNAPSHOT.json").write_text(json.dumps(manifest))

    def first_file(self):
        return self.root / self.manifest()["files"][0]["file"]

    def test_unmodified_snapshot(self):
        self.assertEqual(CHECK.verify(self.root)["skill_packages"], 29)

    def test_same_size_tampering_rejected(self):
        path = self.first_file()
        data = path.read_bytes()
        path.write_bytes(bytes([data[0] ^ 1]) + data[1:])
        with self.assertRaisesRegex(CHECK.SnapshotError, "hash mismatch"):
            CHECK.verify(self.root)

    def test_missing_file_rejected(self):
        self.first_file().unlink()
        with self.assertRaisesRegex(CHECK.SnapshotError, "missing file"):
            CHECK.verify(self.root)

    def test_unlisted_file_rejected(self):
        (self.root / "skills/unexpected.txt").write_text("unexpected")
        with self.assertRaisesRegex(CHECK.SnapshotError, "unlisted file"):
            CHECK.verify(self.root)

    def test_symlink_even_with_identical_bytes_rejected(self):
        path = self.first_file()
        outside = self.root / "outside.txt"
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)
        with self.assertRaisesRegex(CHECK.SnapshotError, "symlink refused"):
            CHECK.verify(self.root)

    def test_traversal_entry_rejected(self):
        manifest = self.manifest()
        manifest["files"][0]["file"] = "skills/../outside.txt"
        self.save(manifest)
        with self.assertRaisesRegex(CHECK.SnapshotError, "unsafe snapshot path"):
            CHECK.verify(self.root)

    def test_duplicate_entry_rejected(self):
        manifest = self.manifest()
        manifest["files"].append(manifest["files"][0])
        self.save(manifest)
        with self.assertRaisesRegex(CHECK.SnapshotError, "duplicate snapshot entry"):
            CHECK.verify(self.root)

    def test_package_count_drift_rejected(self):
        manifest = self.manifest()
        manifest["scope"]["skill_packages"] += 1
        self.save(manifest)
        with self.assertRaisesRegex(CHECK.SnapshotError, "skill package count"):
            CHECK.verify(self.root)

    def test_syntax_error_with_updated_hash_rejected(self):
        manifest = self.manifest()
        row = next(row for row in manifest["files"] if row["file"].endswith(".py"))
        data = b"def invalid(:\n"
        (self.root / row["file"]).write_bytes(data)
        row.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        self.save(manifest)
        with self.assertRaises(SyntaxError):
            CHECK.verify(self.root)

    def test_account_field_in_catalog_rejected(self):
        path = self.root / "catalogs/bundled-mcp.json"
        catalog = json.loads(path.read_text())
        catalog["servers"][0]["account_id"] = "synthetic-test-account"
        path.write_text(json.dumps(catalog))
        with self.assertRaisesRegex(CHECK.SnapshotError, "unexpected catalog fields"):
            CHECK.verify(self.root)


if __name__ == "__main__":
    unittest.main()

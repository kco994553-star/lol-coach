"""Actual dual-SQLite manual draft archives; no game analysis or inference."""
from contextlib import closing
import sqlite3
from pathlib import Path
import tempfile
import unittest

from coach_v1 import backup as recovery
from coach_v1.research import ResearchStore
from coach_v1.storage import Store


# Independent literal fixture from the agreed interface, before backup support.
RAW_DRAFT_SCHEMAS = (
    'CREATE TABLE draft_captures (id TEXT PRIMARY KEY,title TEXT NOT NULL,revision INTEGER NOT NULL)',
    'CREATE TABLE draft_snapshots (id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES draft_captures(id) ON DELETE CASCADE,revision INTEGER NOT NULL,parent_id TEXT,payload TEXT NOT NULL,UNIQUE(session_id,revision),UNIQUE(session_id,id),FOREIGN KEY(session_id,parent_id) REFERENCES draft_snapshots(session_id,id))',
)


class DraftBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.main = self.root / 'personal.sqlite'
        self.research_path = Path(str(self.main) + '.research.sqlite')
        self.archive = self.root / 'personal.zip'
        self.destination = self.root / 'restored'
        self.store = Store(self.main)
        self.store.create_session('기존 합성 사례', 'SYNTHETIC-1')
        ResearchStore(self.research_path)

    def make_main_v2(self):
        with sqlite3.connect(self.main) as db:
            for sql in RAW_DRAFT_SCHEMAS:
                db.execute(sql)
            db.execute('PRAGMA user_version=2')

    def version(self, path):
        with closing(sqlite3.connect(path)) as db:
            return db.execute('PRAGMA user_version').fetchone()[0]

    def test_actual_empty_main_v2_roundtrip_keeps_two_database_format1(self):
        self.make_main_v2()
        original = self.main.read_bytes(), self.research_path.read_bytes()
        try:
            result = recovery.backup(self.main, self.archive)
        except recovery.BackupError as error:
            self.fail('A genuine exact main-v2 database must back up; got ' + error.code)
        self.assertEqual(result['version'], 1)
        self.assertEqual(result['files'][recovery.MAIN]['schema_version'], 2)
        self.assertEqual(result['files'][recovery.RESEARCH]['schema_version'], 1)
        recovery.restore(self.archive, self.destination)
        self.assertEqual(self.version(self.destination / recovery.MAIN), 2)
        self.assertEqual(sorted(path.name for path in self.destination.iterdir()), sorted([recovery.MAIN, recovery.RESEARCH]))
        self.assertEqual((self.main.read_bytes(), self.research_path.read_bytes()), original)

    def test_main_v2_claim_without_physical_draft_tables_never_publishes(self):
        with sqlite3.connect(self.main) as db:
            db.execute('PRAGMA user_version=2')
        original = self.main.read_bytes(), self.research_path.read_bytes()
        with self.assertRaises(recovery.BackupError) as caught:
            recovery.backup(self.main, self.archive)
        self.assertEqual(caught.exception.code, 'INCOMPATIBLE_SCHEMA')
        self.assertFalse(self.archive.exists())
        self.assertEqual((self.main.read_bytes(), self.research_path.read_bytes()), original)


if __name__ == '__main__':
    unittest.main()

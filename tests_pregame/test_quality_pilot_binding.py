import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest


class PilotBindingTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('scripts.verify_quality_pilot'),'pilot verifier missing')
        from scripts import verify_quality_pilot
        return verify_quality_pilot

    def test_changed_bytes_are_not_accepted_by_original_hash(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'file.json').write_bytes(b'original')
            hashes={'file.json':hashlib.sha256(b'original').hexdigest()}
            self.assertTrue(module.check_hashes(root,hashes))
            (root/'file.json').write_bytes(b'changed')
            self.assertFalse(module.check_hashes(root,hashes))

    def test_paths_cannot_escape_root_or_follow_symlinks(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'original').write_bytes(b'x');(root/'link').symlink_to(root/'original')
            digest=hashlib.sha256(b'x').hexdigest()
            for name in ('../original','/original','link'):
                self.assertFalse(module.check_hashes(root,{name:digest}))

    def test_new_source_authority_cannot_be_added_by_seal(self):
        module=self.module()
        binding={'current_sha256':{p:'0'*64 for p in module.CURRENT}}
        self.assertTrue(module.exact_source_authority(binding))
        binding['current_sha256']['unexpected.py']='0'*64
        self.assertFalse(module.exact_source_authority(binding))


if __name__=='__main__':unittest.main()

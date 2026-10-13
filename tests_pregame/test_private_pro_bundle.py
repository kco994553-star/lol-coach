import tempfile
import unittest
from pathlib import Path


class PrivateProBundleTests(unittest.TestCase):
    def test_roundtrip_ciphertext_and_permissions(self):
        from coach_v1.private_pro_bundle import encrypt_directory, decrypt_directory
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'private';root.mkdir()
            secret_payload=b'{"puuid":"private-identity","raw":"original"}'
            (root/'accounts.json').write_bytes(secret_payload)
            bundle=Path(tmp)/'bundle.bin'
            encrypt_directory(root,bundle,'private-test-seed')
            self.assertNotIn(secret_payload,bundle.read_bytes())
            target=Path(tmp)/'restored'
            decrypt_directory(bundle,target,'private-test-seed')
            self.assertEqual((target/'accounts.json').read_bytes(),secret_payload)
            self.assertEqual((target/'accounts.json').stat().st_mode & 0o777,0o600)
            self.assertEqual(target.stat().st_mode & 0o777,0o700)

    def test_wrong_key_or_tamper_never_creates_private_plaintext(self):
        from coach_v1.private_pro_bundle import encrypt_directory, decrypt_directory
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'private';root.mkdir();(root/'accounts.json').write_text('secret')
            bundle=Path(tmp)/'bundle.bin';encrypt_directory(root,bundle,'private-test-seed')
            target=Path(tmp)/'restored'
            with self.assertRaises(ValueError):decrypt_directory(bundle,target,'changed-key')
            self.assertFalse(target.exists())
            b=bytearray(bundle.read_bytes());b[-1]^=1;bundle.write_bytes(b)
            with self.assertRaises(ValueError):decrypt_directory(bundle,target,'private-test-seed')
            self.assertFalse(target.exists())

    def test_symlink_or_nonempty_destination_is_rejected(self):
        from coach_v1.private_pro_bundle import encrypt_directory, decrypt_directory
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'private';root.mkdir();outside=Path(tmp)/'outside';outside.write_text('secret')
            (root/'link').symlink_to(outside)
            with self.assertRaises(ValueError):encrypt_directory(root,Path(tmp)/'bundle.bin','seed')
            (root/'link').unlink();(root/'accounts.json').write_text('secret')
            bundle=Path(tmp)/'bundle.bin';encrypt_directory(root,bundle,'seed')
            target=Path(tmp)/'restored';target.mkdir();(target/'old').write_text('old')
            with self.assertRaises(ValueError):decrypt_directory(bundle,target,'seed')
            self.assertEqual((target/'old').read_text(),'old')

    def test_traversal_in_authenticated_archive_is_rejected(self):
        import io,zipfile
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from coach_v1.private_pro_bundle import decrypt_directory,_key,AAD,MAGIC
        with tempfile.TemporaryDirectory() as tmp:
            content=io.BytesIO()
            with zipfile.ZipFile(content,'w') as archive:archive.writestr('../escape','private')
            nonce=b'123456789012';bundle=Path(tmp)/'bundle.bin'
            bundle.write_bytes(MAGIC+nonce+AESGCM(_key('seed')).encrypt(nonce,content.getvalue(),AAD))
            with self.assertRaises(ValueError):decrypt_directory(bundle,Path(tmp)/'restore','seed')
            self.assertFalse((Path(tmp)/'escape').exists())

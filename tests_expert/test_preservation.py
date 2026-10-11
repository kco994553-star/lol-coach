"""Exact new amendment cannot exempt unrelated or broken historical bytes."""
from copy import deepcopy
import unittest
from unittest.mock import patch
from scripts import verify_mvp_experts as verifier

class AmendmentTests(unittest.TestCase):
    def test_current_version_has_exact_original_and_current_bindings(self):
        self.assertEqual(verifier.korean_binding()['status'],'PASS')

    def test_only_bound_korean_source_is_exempt(self):
        base=dict(frozen_payload_files=27,frozen_errors=[],other_historical_byte_errors=['coach_intake/video.py'],
            r7_source_errors=[],old_test_file_set_errors=[],mvp_authorized_changed_paths=[])
        self.assertEqual(verifier.amended_preservation(base)['status'],'PASS')
        for field,error in [('frozen_errors','frozen'),('other_historical_byte_errors','unrelated.py'),
                            ('r7_source_errors','old-source'),('old_test_file_set_errors','old-test')]:
            bad=deepcopy(base);bad[field].append(error)
            self.assertEqual(verifier.amended_preservation(bad)['status'],'FAIL')

    def test_broken_version_cannot_authorize_source(self):
        base=dict(frozen_payload_files=27,frozen_errors=[],other_historical_byte_errors=['coach_intake/video.py'],
            r7_source_errors=[],old_test_file_set_errors=[],mvp_authorized_changed_paths=[])
        with patch.object(verifier,'korean_binding',return_value={'status':'FAIL'}):
            result=verifier.amended_preservation(base)
        self.assertEqual(result['status'],'FAIL');self.assertEqual(result['other_historical_byte_errors'],['coach_intake/video.py'])

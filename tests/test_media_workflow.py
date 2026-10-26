"""Synthetic fixtures test ledger behavior, never image-model quality."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/media-workflow/scripts/media_workflow.py'
SPEC = importlib.util.spec_from_file_location('media_workflow', SCRIPT)
mw = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mw)


def png(width=2, height=3, colour=0):
    def chunk(kind, value):
        return struct.pack('>I', len(value)) + kind + value + struct.pack('>I', zlib.crc32(kind + value))
    rows = (b'\x00' + bytes([colour, 0, 0]) * width) * height
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b'')


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / 'project'
        self.project.mkdir()
        (self.project / 'records').mkdir()
        (self.project / 'originals').mkdir()
        (self.project / 'delivery').mkdir()
        data = png()
        (self.project / 'originals/beans-0001.png').write_bytes(data)
        (self.project / 'delivery/beans.png').write_bytes(data)
        self.sha = hashlib.sha256(data).hexdigest()
        prompt = 'Synthetic checker fixture: beans.\nNo media model was called.'
        self.manifest = {
            'schemaVersion': 1,
            'project': {'name': 'Fixture', 'site': 'https://example.test', 'repository': 'https://github.com/example/fixture', 'visibility': 'private'},
            'inventoryComplete': True,
            'sources': [],
            'jobs': [{'id': 'beans', 'kind': 'image', 'mode': 'generated', 'subject': 'Synthetic beans fixture',
                      'sourceIds': [], 'prompt': prompt, 'promptSha256': mw.prompt_hash(prompt), 'references': [],
                      'outputs': [{'path': 'delivery/beans.png', 'format': 'png', 'width': 2, 'height': 3, 'maxBytes': 5000}],
                      'owner': 'unittest'}]}
        self.record = {'jobId': 'beans', 'status': 'approved', 'selectedAttempt': 1,
                       'attempts': [{'attempt': 1, 'status': 'approved', 'tool': 'unittest synthetic fixture',
                                     'jobSha256': mw.job_hash(self.manifest['jobs'][0]),
                                     'prompt': prompt, 'promptSha256': mw.prompt_hash(prompt),
                                     'createdAt': '2026-10-26T18:00:00Z',
                                     'original': {'path': 'originals/beans-0001.png', 'sha256': self.sha},
                                     'review': {'decision': 'approved', 'reviewer': 'unittest fixture',
                                                'reviewedAt': '2026-10-26T18:01:00Z', 'method': 'synthetic-test-only',
                                                'notes': 'Fixture tests record validation; no visual approval occurred.', 'originalSha256': self.sha},
                                     'outputs': [{'path': 'delivery/beans.png', 'sha256': self.sha, 'format': 'png', 'width': 2, 'height': 3}]}]}
        self.save()

    def save(self):
        (self.project / 'manifest.json').write_text(json.dumps(self.manifest), encoding='utf-8')
        (self.project / 'records/beans.json').write_text(json.dumps(self.record), encoding='utf-8')

    def assert_invalid(self, phrase, complete=True, require_originals=False):
        self.save()
        with self.assertRaisesRegex(mw.Invalid, phrase):
            mw.verify(self.project, complete, require_originals)

    def test_complete_fixture_and_readonly(self):
        before = {str(p): p.read_bytes() for p in self.project.rglob('*') if p.is_file()}
        report = mw.verify(self.project, complete=True, require_originals=True)
        self.assertEqual(report['states'], {'approved': 1})
        self.assertEqual(report['notices'], [])
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.project.rglob('*') if p.is_file()})

    def test_prompt_hash_is_exact_utf8(self):
        self.manifest['jobs'][0]['prompt'] += '\n'
        self.assert_invalid('prompt hash mismatch')

    def test_actual_correction_prompt_can_differ(self):
        attempt = self.record['attempts'][0]
        attempt['prompt'] = 'Corrected synthetic prompt: red beans.'
        attempt['promptSha256'] = mw.prompt_hash(attempt['prompt'])
        self.save()
        self.assertEqual(mw.verify(self.project, True)['states'], {'approved': 1})

    def test_review_binds_exact_original(self):
        self.record['attempts'][0]['review']['originalSha256'] = 'f' * 64
        self.assert_invalid('different original')

    def test_approved_requires_review(self):
        del self.record['attempts'][0]['review']
        self.assert_invalid('requires review evidence')

    def test_selected_attempt_must_exist(self):
        self.record['selectedAttempt'] = 2
        self.assert_invalid('does not exist')

    def test_selected_attempt_cannot_be_boolean(self):
        self.record['selectedAttempt'] = True
        self.assert_invalid('does not exist')

    def test_missing_original_is_explicit_optional_archive_limit(self):
        (self.project / 'originals/beans-0001.png').unlink()
        report = mw.verify(self.project, True)
        self.assertIn('Not verified (archive absent)', report['notices'][0])
        with self.assertRaisesRegex(mw.Invalid, 'missing file'):
            mw.verify(self.project, True, True)

    def test_present_original_must_match_even_without_flag(self):
        (self.project / 'originals/beans-0001.png').write_bytes(png(colour=1))
        with self.assertRaisesRegex(mw.Invalid, 'file hash mismatch'):
            mw.verify(self.project)

    def test_delivery_hash_and_measured_dimensions(self):
        self.manifest['jobs'][0]['outputs'][0]['width'] = 100
        self.assert_invalid('Actual image dimensions mismatch')

    def test_claimed_dimensions_cannot_override_bytes(self):
        self.record['attempts'][0]['outputs'][0]['height'] = 100
        self.assert_invalid('Recorded image dimensions mismatch')

    def test_delivery_size_limit(self):
        self.manifest['jobs'][0]['outputs'][0]['maxBytes'] = 1
        self.assert_invalid('exceeds size')

    def test_metadata_without_delivery_is_incomplete(self):
        self.record['attempts'][0]['outputs'] = []
        self.assert_invalid('incomplete delivery')

    def test_wrong_delivery_bytes_fail(self):
        (self.project / 'delivery/beans.png').write_bytes(png(colour=2))
        with self.assertRaisesRegex(mw.Invalid, 'file hash mismatch'):
            mw.verify(self.project)

    def test_inflight_and_missing_results_resume_without_claiming_complete(self):
        self.record['status'] = 'in_progress'
        self.record['selectedAttempt'] = None
        self.record['attempts'] = [{'attempt': 1, 'status': 'in_flight', 'tool': 'synthetic fixture',
                                   'jobSha256': mw.job_hash(self.manifest['jobs'][0]),
                                   'createdAt': '2026-10-26T18:00:00Z', 'prompt': 'Synthetic',
                                   'promptSha256': mw.prompt_hash('Synthetic'), 'outputs': []}]
        self.save()
        self.assertEqual(mw.verify(self.project)['states'], {'in_progress': 1})
        with self.assertRaisesRegex(mw.Invalid, 'not approved'):
            mw.verify(self.project, True)
        (self.project / 'records/beans.json').unlink()
        self.assertEqual(mw.verify(self.project)['states'], {'planned': 1})

    def test_inventory_cannot_claim_complete_when_empty_or_partial(self):
        self.manifest['inventoryComplete'] = False
        self.assert_invalid('Complete inventory')
        self.manifest['inventoryComplete'] = True
        self.manifest['jobs'] = []
        self.assert_invalid('Complete inventory')

    def test_path_escape_and_windows_ambiguity(self):
        for path in ('../secret.png', '/tmp/secret.png', 'C:/secret.png', 'delivery\\secret.png',
                     'delivery/../secret.png', 'delivery/CON.png', 'delivery/file.png:stream', 'delivery/file.png.'):
            with self.subTest(path=path):
                self.manifest['jobs'][0]['outputs'][0]['path'] = path
                self.assert_invalid('path')

    def test_symlink_path_is_rejected(self):
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        try:
            (self.project / 'linked').symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('Symlink creation not permitted on this machine')
        self.manifest['jobs'][0]['outputs'][0]['path'] = 'linked/beans.png'
        self.assert_invalid('Link/junction')

    def test_case_insensitive_duplicate_delivery_paths(self):
        job = copy.deepcopy(self.manifest['jobs'][0])
        job['id'] = 'other-beans'
        job['outputs'][0]['path'] = 'delivery/BEANS.png'
        self.manifest['jobs'].append(job)
        self.assert_invalid('Duplicate output path')

    def test_reference_modes_require_provenance(self):
        self.manifest['jobs'][0]['mode'] = 'reference-edit'
        self.assert_invalid('require references')

    def test_reference_hash_and_source_mapping(self):
        self.manifest['sources'] = [{'id': 'official', 'url': 'https://example.test/beans',
                                     'retrievedAt': '2026-10-26T18:00:00Z', 'notes': 'Synthetic official-source fixture'}]
        self.manifest['jobs'][0].update(mode='format-only', sourceIds=['official'], references=[{
            'path': 'originals/beans-0001.png', 'sha256': self.sha,
            'sourceUrl': 'https://example.test/beans.png', 'rightsStatus': 'synthetic fixture only'}])
        self.record['attempts'][0]['jobSha256'] = mw.job_hash(self.manifest['jobs'][0])
        self.save()
        self.assertEqual(mw.verify(self.project, True, True)['jobs'], 1)
        self.manifest['jobs'][0]['sourceIds'] = ['invented']
        self.assert_invalid('Unknown source')

    def reference_fixture(self):
        return {'path': 'originals/reference.png', 'sha256': self.sha,
                'sourceUrl': 'https://example.test/reference.png', 'rightsStatus': 'synthetic fixture'}

    def test_selected_attempt_references_match_bound_job(self):
        ref = self.reference_fixture()
        (self.project / ref['path']).write_bytes(png())
        self.manifest['jobs'][0]['references'] = [ref]
        self.record['attempts'][0]['references'] = [copy.deepcopy(ref)]
        self.record['attempts'][0]['jobSha256'] = mw.job_hash(self.manifest['jobs'][0])
        self.save()
        self.assertEqual(mw.verify(self.project, True, True)['states'], {'approved': 1})
        self.record['attempts'][0]['references'][0]['sourceUrl'] = 'https://example.test/different.png'
        self.assert_invalid('references differ from its bound job')

    def test_attempt_reference_paths_and_schema_are_validated(self):
        for field, value, error in (('path', '../secret.png', 'Unsafe path'),
                                    ('sourceUrl', '', 'nonempty text'),
                                    ('rightsStatus', None, 'nonempty text'),
                                    ('sha256', 'bad', 'invalid SHA-256')):
            with self.subTest(field=field):
                ref = self.reference_fixture()
                ref[field] = value
                self.record['attempts'][0]['references'] = [ref]
                self.assert_invalid(error)

    def test_attempt_reference_actual_hash_is_verified(self):
        ref = self.reference_fixture()
        (self.project / ref['path']).write_bytes(png(colour=5))
        self.record['attempts'][0]['references'] = [ref]
        self.assert_invalid('attempt reference: file hash mismatch')

    def test_historical_reference_archives_are_checked_independently(self):
        ref = self.reference_fixture()
        (self.project / ref['path']).write_bytes(png())
        old = self.record['attempts'][0]
        old['jobSha256'] = 'a' * 64
        old['references'] = [ref]
        new = copy.deepcopy(old)
        new.update(attempt=2, jobSha256=mw.job_hash(self.manifest['jobs'][0]), references=[])
        new['original']['path'] = 'originals/beans-0002.png'
        (self.project / new['original']['path']).write_bytes(png())
        self.record['attempts'].append(new)
        self.record['selectedAttempt'] = 2
        self.save()
        self.assertEqual(mw.verify(self.project, True, True)['states'], {'approved': 1})
        (self.project / ref['path']).unlink()
        report = mw.verify(self.project, True)
        self.assertTrue(any('reference.png' in item for item in report['notices']))
        with self.assertRaisesRegex(mw.Invalid, 'attempt reference: missing file'):
            mw.verify(self.project, True, True)

    def test_duplicate_json_keys_rejected(self):
        (self.project / 'manifest.json').write_text('{"schemaVersion":1,"schemaVersion":2}', encoding='utf-8')
        with self.assertRaisesRegex(mw.Invalid, 'Duplicate JSON key'):
            mw.verify(self.project)

    def test_unknown_record_rejected(self):
        (self.project / 'records/unknown.json').write_text('{}', encoding='utf-8')
        with self.assertRaisesRegex(mw.Invalid, 'Unmapped record'):
            mw.verify(self.project)

    def test_superseded_delivery_paths_keep_prior_original_evidence(self):
        old = self.record['attempts'][0]
        old['outputs'][0]['sha256'] = 'a' * 64
        new = copy.deepcopy(old)
        new['attempt'] = 2
        new['outputs'][0]['sha256'] = self.sha
        new['original']['path'] = 'originals/beans-0002.png'
        (self.project / new['original']['path']).write_bytes(png())
        self.record['attempts'].append(new)
        self.record['selectedAttempt'] = 2
        self.save()
        self.assertEqual(mw.verify(self.project, True, True)['states'], {'approved': 1})

    def test_new_revision_can_rename_and_reformat_delivery(self):
        old = copy.deepcopy(self.record['attempts'][0])
        for fmt in ('png', 'webp'):
            with self.subTest(format=fmt):
                data = png()
                if fmt == 'webp':
                    # Metadata fixture only, not a complete encoded image.
                    payload = b'\x00' * 4 + (1).to_bytes(3, 'little') + (2).to_bytes(3, 'little')
                    content = b'WEBPVP8X' + (10).to_bytes(4, 'little') + payload
                    data = b'RIFF' + len(content).to_bytes(4, 'little') + content
                path = f'delivery/beans-renamed.{fmt}'
                (self.project / path).write_bytes(data)
                job = self.manifest['jobs'][0]
                job['outputs'][0].update(path=path, format=fmt)
                new = copy.deepcopy(old)
                new.update(attempt=2, jobSha256=mw.job_hash(job))
                new['original']['path'] = 'originals/beans-0002.png'
                (self.project / new['original']['path']).write_bytes(png())
                new['outputs'][0].update(path=path, format=fmt, sha256=hashlib.sha256(data).hexdigest())
                self.record.update(attempts=[copy.deepcopy(old), new], selectedAttempt=2)
                self.save()
                self.assertEqual(mw.verify(self.project, True, True)['states'], {'approved': 1})
                self.assertEqual((self.project / 'delivery/beans.png').read_bytes(), png())

    def test_historical_delivery_metadata_remains_strict(self):
        old = copy.deepcopy(self.record['attempts'][0])
        new = copy.deepcopy(old)
        new['attempt'] = 2
        new['original']['path'] = 'originals/beans-0002.png'
        (self.project / new['original']['path']).write_bytes(png())
        self.record.update(attempts=[old, new], selectedAttempt=2)
        original_output = copy.deepcopy(old['outputs'][0])
        for field, value, error in (('path', '../escaped.png', 'Unsafe path'),
                                    ('format', 'webp', 'extension and format disagree'),
                                    ('sha256', 'bad', 'invalid SHA-256'),
                                    ('width', -1, 'positive integer')):
            with self.subTest(field=field):
                old['outputs'] = [dict(original_output, **{field: value})]
                self.assert_invalid(error)
        old['outputs'] = [original_output, copy.deepcopy(original_output)]
        old['outputs'][1]['path'] = old['outputs'][1]['path'].upper()
        self.assert_invalid('Duplicate delivery path')

    def test_webp_dimensions(self):
        # Minimal header fixture validates metadata only; not an encoder output.
        payload = b'\x00' * 4 + (1).to_bytes(3, 'little') + (2).to_bytes(3, 'little')
        content = b'WEBPVP8X' + (10).to_bytes(4, 'little') + payload
        path = self.project / 'header.webp'
        path.write_bytes(b'RIFF' + len(content).to_bytes(4, 'little') + content)
        self.assertEqual(mw.image_info(path), ('webp', 2, 3))

    def test_job_revision_changes_invalidate_approval(self):
        original = copy.deepcopy(self.manifest['jobs'][0])
        for changed in ('product', 'prompt', 'references', 'outputs', 'subject'):
            with self.subTest(changed=changed):
                job = copy.deepcopy(original)
                if changed == 'product':
                    job['product'] = {'brand': 'Fixture', 'sku': 'BEANS-2', 'packSize': '500 g'}
                elif changed == 'prompt':
                    job['prompt'] += ' Different label.'
                    job['promptSha256'] = mw.prompt_hash(job['prompt'])
                elif changed == 'references':
                    job['references'] = [{'path': 'originals/beans-0001.png', 'sha256': self.sha,
                                           'sourceUrl': 'https://example.test/beans.png', 'rightsStatus': 'synthetic fixture'}]
                elif changed == 'outputs':
                    job['outputs'][0]['maxBytes'] = 6000
                elif changed == 'subject':
                    job['subject'] = 'A different product'
                self.manifest['jobs'][0] = job
                self.assert_invalid('different job revision')

    def test_owner_reassignment_preserves_job_revision(self):
        before = mw.job_hash(self.manifest['jobs'][0])
        self.manifest['jobs'][0]['owner'] = 'second-reviewer'
        self.save()
        self.assertEqual(mw.job_hash(self.manifest['jobs'][0]), before)
        self.assertEqual(mw.verify(self.project, True)['states'], {'approved': 1})

    def test_malformed_job_hash_is_rejected(self):
        self.record['attempts'][0]['jobSha256'] = 'not-a-hash'
        self.assert_invalid('invalid SHA-256')

    def test_historical_job_revision_is_valid_but_cannot_be_selected(self):
        old = self.record['attempts'][0]
        old['jobSha256'] = 'a' * 64
        new = copy.deepcopy(old)
        new.update(attempt=2, jobSha256=mw.job_hash(self.manifest['jobs'][0]))
        new['original']['path'] = 'originals/beans-0002.png'
        (self.project / new['original']['path']).write_bytes(png())
        self.record['attempts'].append(new)
        self.record['selectedAttempt'] = 2
        self.save()
        self.assertEqual(mw.verify(self.project, True)['states'], {'approved': 1})
        self.record['selectedAttempt'] = 1
        self.assert_invalid('different job revision')

    def test_original_path_cannot_be_reused_by_attempts_or_jobs(self):
        duplicate = copy.deepcopy(self.record['attempts'][0])
        duplicate['attempt'] = 2
        self.record['attempts'].append(duplicate)
        self.assert_invalid('Original path reused')
        self.record['attempts'].pop()
        new_job = copy.deepcopy(self.manifest['jobs'][0])
        new_job['id'] = 'other-beans'
        new_job['outputs'][0]['path'] = 'delivery/other-beans.png'
        self.manifest['jobs'].append(new_job)
        new_record = copy.deepcopy(self.record)
        new_record['jobId'] = 'other-beans'
        new_record['attempts'][0]['jobSha256'] = mw.job_hash(new_job)
        new_record['attempts'][0]['outputs'][0]['path'] = 'delivery/other-beans.png'
        (self.project / 'delivery/other-beans.png').write_bytes(png())
        (self.project / 'records/other-beans.json').write_text(json.dumps(new_record), encoding='utf-8')
        self.assert_invalid('Original path reused')

    def test_job_hash_command_uses_canonical_definition(self):
        expected = hashlib.sha256(json.dumps(
            {k: v for k, v in self.manifest['jobs'][0].items() if k != 'owner'},
            sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest()
        run = subprocess.run([sys.executable, str(SCRIPT), 'job-hash', str(self.project), 'beans'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0)
        self.assertEqual(run.stdout.strip(), expected)

    def test_jpeg_dimensions(self):
        path = self.project / 'header.jpg'
        path.write_bytes(b'\xff\xd8\xff\xc0\x00\x08\x08\x00\x03\x00\x02\x00\xff\xd9')
        self.assertEqual(mw.image_info(path), ('jpeg', 2, 3))

    def test_cli_exits_nonzero_on_invalid_project(self):
        self.record['selectedAttempt'] = 88
        self.save()
        run = subprocess.run([sys.executable, str(SCRIPT), 'verify', str(self.project), '--complete'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 1)
        self.assertIn('Selected attempt', run.stderr)

    def test_init_and_resume_never_overwrite_existing_project(self):
        destination = Path(self.temp.name) / 'new-project'
        mw.initialize(destination, 'Example', 'https://example.test', 'https://github.com/example/private-media')
        report = mw.verify(destination)
        self.assertEqual(report['jobs'], 0)
        self.assertIn('originals/', (destination / '.gitignore').read_text())
        before = (destination / 'brief.md').read_bytes()
        with self.assertRaisesRegex(mw.Invalid, 'never overwrites'):
            mw.initialize(destination, 'Changed', 'https://example.test', 'https://github.com/example/changed')
        self.assertEqual(before, (destination / 'brief.md').read_bytes())


if __name__ == '__main__':
    unittest.main()

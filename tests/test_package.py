import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('package_builder', ROOT / 'tools/build_package.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PackageTests(unittest.TestCase):
    def test_installable_layout(self):
        manifest = json.loads((ROOT / 'plugin.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['name'], 'media-workflow')
        self.assertEqual(manifest['$schema'], 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json')
        self.assertNotIn('skills', manifest)
        self.assertTrue(manifest['extensions']['com.openai']['requires_local_executor'])
        skill = ROOT / 'skills/media-workflow'
        text = (skill / 'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(text.startswith('---\nname: media-workflow\n'))
        for name in ('references/workflow.md', 'references/product-images.md',
                     'references/records.md', 'scripts/media_workflow.py',
                     'assets/brief.template.md', 'assets/workflow.template.md',
                     'assets/manifest.template.json'):
            self.assertTrue((skill / name).is_file(), name)
        marketplace = json.loads((ROOT / '.agents/plugins/marketplace.json').read_text(encoding='utf-8'))
        self.assertEqual(marketplace['plugins'][0]['source']['path'], './')

    def test_zip_contains_skill_and_no_private_work(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'package.zip'
            first = builder.build(ROOT, output)
            self.assertGreater(first['files'], 10)
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                self.assertIn('skills/media-workflow/scripts/media_workflow.py', names)
                self.assertIn('plugin.json', names)
                self.assertIn('docs/VALIDATION.md', names)
                self.assertIn('security/BASELINE.md', names)
                self.assertIn('tools/build_package.py', names)
                self.assertIn('tests/test_media_workflow.py', names)
                self.assertFalse(any(p.startswith(('.git/', '.local/', 'dist/', 'media-work/')) for p in names))
            second = builder.build(ROOT, Path(temporary) / 'second.zip')
            self.assertEqual(first['sha256'], second['sha256'])
            with self.assertRaises(FileExistsError):
                builder.build(ROOT, output)


if __name__ == '__main__':
    unittest.main()

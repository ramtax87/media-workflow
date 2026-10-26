#!/usr/bin/env python3
"""Initialize and verify a media ledger. No network, generation or media edits.

Hashes establish byte identity. Review entries are attestations, not proof that a
person or model inspected the work. Keep the originals for independent review.
"""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import struct
import sys


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def text(value, label):
    require(isinstance(value, str) and bool(value.strip()), f'{label}: expected nonempty text')
    return value


def integer(value, label):
    require(type(value) is int and value > 0, f'{label}: expected positive integer')
    return value


def digest(value, label):
    require(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value), f'{label}: invalid SHA-256')
    return value


def timestamp(value, label):
    text(value, label)
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise Invalid(f'{label}: invalid ISO timestamp') from error
    require(parsed.tzinfo is not None, f'{label}: timezone required')


def object_value(value, label):
    require(isinstance(value, dict), f'{label}: expected object')
    return value


def array(value, label):
    require(isinstance(value, list), f'{label}: expected array')
    return value


def sha256_file(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def prompt_hash(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def job_hash(job):
    """Bind an attempt to its planned job revision, excluding assignment only."""
    revision = {key: value for key, value in job.items() if key != 'owner'}
    canonical = json.dumps(revision, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def no_links(path):
    for item in (path, *path.parents):
        require(not item.is_symlink() and not getattr(item, 'is_junction', lambda: False)(),
                f'Link/junction path is not allowed: {item}')


def confined(root, value):
    text(value, 'path')
    require('\\' not in value and ':' not in value, f'Unsafe path: {value}')
    parts = value.split('/')
    require(not PurePosixPath(value).is_absolute() and all(p not in ('', '.', '..') for p in parts),
            f'Unsafe path: {value}')
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}
    require(all(not p.endswith((' ', '.')) and p.split('.')[0].upper() not in reserved for p in parts),
            f'Nonportable path: {value}')
    path = root.joinpath(*parts)
    no_links(path)
    require(path.resolve().is_relative_to(root.resolve()), f'Path escapes project: {value}')
    return path


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def read_json(path):
    no_links(path)
    require(path.is_file(), f'Missing JSON file: {path.name}')
    require(path.stat().st_size <= 5 * 1024 * 1024, f'JSON file too large: {path.name}')
    try:
        return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object,
                          parse_constant=lambda value: (_ for _ in ()).throw(Invalid(f'Invalid JSON number: {value}')))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise Invalid(f'Invalid JSON: {path.name}') from error


def image_info(path):
    """Read PNG, WebP and JPEG dimensions; never decode or execute the content."""
    with path.open('rb') as stream:
        header = stream.read(32)
        if header.startswith(b'\x89PNG\r\n\x1a\n') and len(header) >= 24 and header[12:16] == b'IHDR':
            return 'png', *struct.unpack('>II', header[16:24])
        if header[:4] == b'RIFF' and header[8:12] == b'WEBP':
            stream.seek(12)
            limit = path.stat().st_size
            while stream.tell() + 8 <= limit:
                kind = stream.read(4)
                size = int.from_bytes(stream.read(4), 'little')
                require(stream.tell() + size <= limit, f'Truncated WebP: {path.name}')
                data = stream.read(min(size, 10))
                if kind == b'VP8X' and len(data) >= 10:
                    return 'webp', int.from_bytes(data[4:7], 'little') + 1, int.from_bytes(data[7:10], 'little') + 1
                if kind == b'VP8L' and len(data) >= 5 and data[0] == 0x2f:
                    bits = int.from_bytes(data[1:5], 'little')
                    return 'webp', (bits & 0x3fff) + 1, ((bits >> 14) & 0x3fff) + 1
                if kind == b'VP8 ' and len(data) >= 10 and data[3:6] == b'\x9d\x01\x2a':
                    return 'webp', int.from_bytes(data[6:8], 'little') & 0x3fff, int.from_bytes(data[8:10], 'little') & 0x3fff
                stream.seek(size - len(data) + size % 2, 1)
        if header[:2] == b'\xff\xd8':
            stream.seek(2)
            while stream.tell() < path.stat().st_size:
                require(stream.read(1) == b'\xff', f'Malformed JPEG: {path.name}')
                marker = stream.read(1)
                while marker == b'\xff':
                    marker = stream.read(1)
                if marker in (b'', b'\xda', b'\xd9'):
                    break
                if marker == b'\x01' or b'\xd0' <= marker <= b'\xd7':
                    continue
                raw = stream.read(2)
                require(len(raw) == 2, f'Truncated JPEG: {path.name}')
                size = int.from_bytes(raw, 'big')
                require(size >= 2 and stream.tell() + size - 2 <= path.stat().st_size,
                        f'Malformed JPEG segment: {path.name}')
                if marker[0] in (0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf):
                    data = stream.read(5)
                    require(size >= 7 and len(data) == 5, f'Truncated JPEG dimensions: {path.name}')
                    return 'jpeg', int.from_bytes(data[3:5], 'big'), int.from_bytes(data[1:3], 'big')
                stream.seek(size - 2, 1)
    return None


def file_record(root, value, label, notices, required=True):
    object_value(value, label)
    path = confined(root, value.get('path'))
    expected = digest(value.get('sha256'), f'{label}.sha256')
    if not path.exists():
        require(not required, f'{label}: missing file {value["path"]}')
        notices.add(f'Not verified (archive absent): {value["path"]}')
        return None
    require(path.is_file(), f'{label}: not a file')
    require(sha256_file(path) == expected, f'{label}: file hash mismatch')
    return path


def check_prompt(item, label):
    value = text(item.get('prompt'), f'{label}.prompt')
    require(digest(item.get('promptSha256'), f'{label}.promptSha256') == prompt_hash(value),
            f'{label}: prompt hash mismatch')


def output_spec(root, output):
    object_value(output, 'output')
    confined(root, output.get('path'))
    fmt = text(output.get('format'), 'output.format').lower()
    require(re.fullmatch('[a-z0-9]+', fmt), 'Invalid output format')
    suffix = PurePosixPath(output['path']).suffix[1:].lower()
    require(suffix == fmt or {suffix, fmt} <= {'jpg', 'jpeg'}, 'Output extension and format disagree')
    for key in ('width', 'height', 'maxBytes'):
        if key in output:
            integer(output[key], 'output.' + key)


def reference_specs(root, values, label):
    """Validate the same provenance contract for planned and actual references."""
    references = array(values, label)
    for ref in references:
        object_value(ref, label + ' entry')
        confined(root, ref.get('path'))
        digest(ref.get('sha256'), label + '.sha256')
        text(ref.get('sourceUrl'), label + '.sourceUrl')
        text(ref.get('rightsStatus'), label + '.rightsStatus')
    return references


def load_manifest(root):
    root = Path(root).absolute()
    no_links(root)
    manifest = object_value(read_json(root / 'manifest.json'), 'manifest')
    require(type(manifest.get('schemaVersion')) is int and manifest['schemaVersion'] == 1, 'Unsupported schemaVersion')
    project = object_value(manifest.get('project'), 'project')
    for key in ('name', 'site', 'repository'):
        text(project.get(key), 'project.' + key)
    require(project.get('visibility') == 'private', 'This version requires private project visibility')
    require(type(manifest.get('inventoryComplete')) is bool, 'inventoryComplete must be boolean')
    source_ids = set()
    for source in array(manifest.get('sources'), 'sources'):
        object_value(source, 'source')
        identifier = text(source.get('id'), 'source.id')
        require(identifier not in source_ids, 'Duplicate source ID')
        source_ids.add(identifier)
        text(source.get('url'), 'source.url')
        timestamp(source.get('retrievedAt'), 'source.retrievedAt')
        text(source.get('notes'), 'source.notes')
    jobs = {}
    paths = set()
    for job in array(manifest.get('jobs'), 'jobs'):
        object_value(job, 'job')
        identifier = text(job.get('id'), 'job.id')
        require(re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*', identifier), 'Job IDs must be lowercase slugs')
        require(identifier not in jobs, 'Duplicate job ID')
        jobs[identifier] = job
        require(job.get('kind') in ('image', 'video', 'audio', 'vector'), 'Invalid media kind')
        require(job.get('mode') in ('generated', 'reference-edit', 'format-only', 'licensed-source'), 'Invalid job mode')
        text(job.get('subject'), 'job.subject')
        text(job.get('owner'), 'job.owner')
        if 'product' in job:
            object_value(job['product'], 'job.product')
            for key, value in job['product'].items():
                require(isinstance(value, str), f'product.{key}: expected text')
        check_prompt(job, identifier)
        refs = array(job.get('sourceIds'), 'job.sourceIds')
        require(all(isinstance(ref, str) and ref in source_ids for ref in refs), 'Unknown source ID')
        references = reference_specs(root, job.get('references'), 'job.references')
        require(job['mode'] == 'generated' or bool(references), 'Source/edit jobs require references')
        outputs = array(job.get('outputs'), 'job.outputs')
        require(bool(outputs), 'Every job requires an output')
        for output in outputs:
            output_spec(root, output)
            path = output['path'].casefold()
            require(path not in paths, 'Duplicate output path')
            paths.add(path)
    return root, manifest, jobs


def verify(project_dir, complete=False, require_originals=False):
    root, manifest, jobs = load_manifest(project_dir)
    notices = set()
    counts = Counter()
    original_paths = set()
    if complete:
        require(manifest['inventoryComplete'] and bool(jobs), 'Complete inventory with at least one job required')
    records_dir = confined(root, 'records')
    if records_dir.exists():
        require(records_dir.is_dir(), 'records must be a directory')
        for path in records_dir.iterdir():
            no_links(path)
            require(path.is_file() and path.suffix == '.json' and path.stem in jobs, f'Unmapped record: {path.name}')
    for identifier, job in jobs.items():
        for ref in job['references']:
            file_record(root, ref, 'reference', notices, require_originals)
        record_path = confined(root, f'records/{identifier}.json')
        if not record_path.exists():
            counts['planned'] += 1
            require(not complete, f'{identifier}: no result record')
            continue
        record = object_value(read_json(record_path), 'record')
        require(record.get('jobId') == identifier, 'Record jobId mismatch')
        state = record.get('status')
        require(state in ('in_progress', 'pending_review', 'approved', 'rejected', 'blocked'), 'Invalid record status')
        counts[state] += 1
        selected = record.get('selectedAttempt')
        attempts = {}
        for attempt in array(record.get('attempts'), 'attempts'):
            object_value(attempt, 'attempt')
            number = integer(attempt.get('attempt'), 'attempt number')
            require(number not in attempts, 'Duplicate attempt number')
            attempts[number] = attempt
            digest(attempt.get('jobSha256'), 'attempt.jobSha256')
            ast = attempt.get('status')
            require(ast in ('in_flight', 'pending_review', 'approved', 'rejected', 'failed'), 'Invalid attempt status')
            text(attempt.get('tool'), 'attempt.tool')
            timestamp(attempt.get('createdAt'), 'attempt.createdAt')
            check_prompt(attempt, f'{identifier} attempt {number}')
            if 'references' in attempt:
                for ref in reference_specs(root, attempt['references'], 'attempt.references'):
                    file_record(root, ref, 'attempt reference', notices, require_originals)
            original = attempt.get('original')
            if original is not None:
                file_record(root, original, 'original', notices, require_originals)
                original_path = original['path'].casefold()
                require(original_path not in original_paths, 'Original path reused by another attempt/job')
                original_paths.add(original_path)
            require(ast not in ('pending_review', 'approved', 'rejected') or original is not None, 'Saved attempt requires original')
            review = attempt.get('review')
            if review is not None:
                object_value(review, 'review')
                require(original is not None, 'Review requires original')
                require(review.get('decision') in ('approved', 'rejected') and review['decision'] == ast, 'Review/status mismatch')
                for key in ('reviewer', 'method', 'notes'):
                    text(review.get(key), 'review.' + key)
                timestamp(review.get('reviewedAt'), 'review.reviewedAt')
                require(review.get('originalSha256') == original['sha256'], 'Review is for a different original')
            require(ast not in ('approved', 'rejected') or review is not None, 'Reviewed status requires review evidence')
            outputs = array(attempt.get('outputs'), 'attempt.outputs')
            require(not outputs or ast == 'approved', 'Only approved attempts may have delivery outputs')
            seen = set()
            expected_outputs = {out['path']: out for out in job['outputs']}
            for output in outputs:
                output_spec(root, output)
                name = output['path']
                require(name.casefold() not in seen, 'Duplicate delivery path')
                seen.add(name.casefold())
                digest(output.get('sha256'), 'delivery.sha256')
                if number != selected:
                    # A new job revision may rename/reformat final derivatives.
                    # Preserve historical metadata and original/review evidence.
                    continue
                require(name in expected_outputs, 'Unexpected delivery path')
                spec = expected_outputs[name]
                require(output.get('format') == spec['format'], 'Delivery format mismatch')
                path = file_record(root, output, 'delivery', notices)
                require(path.stat().st_size > 0, 'Empty delivery file')
                require('maxBytes' not in spec or path.stat().st_size <= spec['maxBytes'], 'Delivery exceeds size limit')
                info = image_info(path)
                if info:
                    fmt, width, height = info
                    require(width > 0 and height > 0, 'Invalid image dimensions')
                    require(fmt == spec['format'] or {fmt, spec['format']} <= {'jpg', 'jpeg'}, 'Actual image format mismatch')
                    for key, actual in (('width', width), ('height', height)):
                        if key in spec:
                            require(actual == spec[key], 'Actual image dimensions mismatch')
                        if key in output:
                            require(actual == output[key], 'Recorded image dimensions mismatch')
                else:
                    require(spec['format'] not in ('png', 'jpg', 'jpeg', 'webp'), 'Unrecognized/corrupt raster header')
                    notices.add(f'Format/dimensions not binary-inspected: {name}')
                    for key in ('width', 'height'):
                        if key in spec:
                            require(output.get(key) == spec[key], 'Declared dimensions mismatch')
        if selected is not None:
            require(type(selected) is int and selected in attempts, 'Selected attempt does not exist')
            require(attempts[selected]['status'] == 'approved' and state == 'approved', 'Selected attempt must be approved')
            require(attempts[selected]['jobSha256'] == job_hash(job),
                    f'{identifier}: selected approval belongs to a different job revision')
            if 'references' in attempts[selected]:
                require(attempts[selected]['references'] == job['references'],
                        f'{identifier}: selected attempt references differ from its bound job; update the job and review a new attempt')
        if state == 'approved':
            require(selected is not None, 'Approved record needs selectedAttempt')
        if complete:
            require(state == 'approved' and selected is not None, f'{identifier}: not approved')
            require({out['path'] for out in attempts[selected]['outputs']} == {out['path'] for out in job['outputs']},
                    f'{identifier}: incomplete delivery')
    return {'jobs': len(jobs), 'states': dict(sorted(counts.items())), 'completeCheck': complete,
            'originalsRequired': require_originals, 'notices': sorted(notices),
            'limits': 'Hashes and raster headers verified where available; review attestations and visual/audio quality are not independently verified.'}


def initialize(project_dir, name, site, repository):
    root = Path(project_dir).absolute()
    no_links(root)
    require(not root.exists(), 'Destination already exists; initialization never overwrites a project')
    assets = Path(__file__).resolve().parents[1] / 'assets'
    manifest = object_value(read_json(assets / 'manifest.template.json'), 'manifest template')
    manifest['project'] = {'name': name, 'site': site, 'repository': repository, 'visibility': 'private'}
    manifest['inventoryComplete'] = False
    replacements = {'{{PROJECT_NAME}}': name, '{{SITE_URL}}': site, '{{REPOSITORY_URL}}': repository}
    content = {}
    for filename in ('brief', 'workflow'):
        value = (assets / f'{filename}.template.md').read_text(encoding='utf-8')
        for key, replacement in replacements.items():
            value = value.replace(key, replacement)
        content[filename + '.md'] = value
    root.mkdir(parents=True, exist_ok=False)
    for filename, value in content.items():
        (root / filename).write_text(value, encoding='utf-8')
    (root / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (root / '.gitignore').write_text('originals/\n.local/\n', encoding='utf-8')
    (root / 'records').mkdir()
    return {'project': str(root), 'status': 'initialized; inventory and generation not performed'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init', help='Create a new empty project from bundled templates')
    init.add_argument('project_dir')
    for key in ('name', 'site', 'repository'):
        init.add_argument('--' + key, required=True)
    hash_parser = sub.add_parser('hash', help='Print SHA-256 of exact file bytes')
    hash_parser.add_argument('file')
    job_hash_parser = sub.add_parser('job-hash', help='Hash a planned job revision, excluding its owner assignment')
    job_hash_parser.add_argument('project_dir')
    job_hash_parser.add_argument('job_id')
    for command in ('status', 'verify'):
        item = sub.add_parser(command)
        item.add_argument('project_dir')
        if command == 'verify':
            item.add_argument('--complete', action='store_true')
            item.add_argument('--require-originals', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'init':
            result = initialize(args.project_dir, args.name, args.site, args.repository)
        elif args.command == 'hash':
            path = Path(args.file).absolute()
            no_links(path)
            print(sha256_file(path))
            return 0
        elif args.command == 'job-hash':
            _, _, jobs = load_manifest(args.project_dir)
            require(args.job_id in jobs, 'Unknown job ID')
            print(job_hash(jobs[args.job_id]))
            return 0
        else:
            result = verify(args.project_dir, getattr(args, 'complete', False), getattr(args, 'require_originals', False))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (Invalid, OSError, TypeError, KeyError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

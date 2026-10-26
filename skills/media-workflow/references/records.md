# Working files and verification

Create one job directory in the destination repository, normally
`media-work/<project>/`. Paths in JSON are relative to this directory and use `/`.
Do not use absolute paths, `..`, symlinks or secrets in tracked records.

```text
brief.md
workflow.md
manifest.json
records/<job-id>.json
delivery/<job-id>.webp
delivery/<job-id>-thumb.webp
originals/<job-id>/attempt-0001.png
originals/<job-id>/reference-0001.jpg
.local/                 temporary provider/debug data; never commit
```

`originals/` is ignored by the initializer. Preserve it locally and copy it to an
authorized private archive when backup is requested. Record and verify its hashes
there. Git can carry delivery assets, manifests and review records without that
archive; report the resulting verification limit. Inspect the target repository's
own ignore rules: if it ignores all of `media-work/`, deliberately choose another
tracked delivery location or a narrow ignore exception. Never force-add secrets.

## Manifest

`schemaVersion` is `1`. `project` contains `name`, `site`, `repository` and private
`visibility`. `inventoryComplete` starts false. `sources` records `{id, url,
retrievedAt, notes}` for actual examined sources. A source may describe catalogue
facts without granting rights to use its images. A local source can be described
in the brief; do not invent a public URL.

Each `jobs` entry has:

| Field | Meaning |
| --- | --- |
| `id` | Stable lowercase letters/digits/hyphen identifier; filename stem |
| `kind` | `image`, `vector`, `audio` or `video` |
| `mode` | `generated`, `reference-edit`, `format-only` or `licensed-source` |
| `subject` | Exact content being depicted |
| `sourceIds` | Source inventory IDs supporting this job |
| `product` | Optional `{brand, sku, gtin, packSize}`; retain leading zeroes as strings |
| `prompt` | Exact planned generation/edit prompt or deterministic transformation instruction |
| `promptSha256` | SHA-256 of that exact UTF-8 string, without adding/trimming whitespace |
| `references` | `{path, sha256, sourceUrl, rightsStatus}` for each inspected reference |
| `outputs` | Expected `{path, format, width?, height?, maxBytes?}` delivery files |
| `owner` | Agent/operator responsible for this ID |

Use an explicit rights status such as `owner-supplied`, `permission-confirmed`,
`licensed:<reference>`, `unknown` or `restricted`. `unknown` is an unresolved reuse
decision, not a licence. In `licensed-source` mode the AI must verify actual terms;
a status string is not evidence. Keep detailed source-match and permissions notes
in the workflow. Never call a generated output “official”.

Choose sizes per placement. A square catalogue image might use WebP at 1024×1024
and a 480×480 thumbnail, but those are examples, not requirements for every job.
Do not distort or crop a product to satisfy a template. Preserve transparency when
the request requires it.

## Attempt records

One `records/<id>.json` holds `jobId`, `status`, `selectedAttempt` and `attempts`.
Job status is `in_progress`, `pending_review`, `approved`, `rejected` or `blocked`.
`selectedAttempt` is null until an approved attempt is selected for delivery.

Each attempt holds `attempt` (positive integer), `status`, `jobSha256`, `tool`, optional
`model`, exact actual `prompt`, its `promptSha256`, and `createdAt`. Attempt
status is `in_flight`, `pending_review`, `approved`, `rejected` or `failed`.
Every attempt also requires `outputs`, initially an empty array `[]`. Start from
[`attempt.template.json`](../assets/attempt.template.json) and replace its
placeholders with actual job facts; it is not a completed record.

Before an attempt, run `job-hash <project-dir> <job-id>` and save its result in
`jobSha256`. This binds the attempt to the exact product facts, planned prompt,
references and output requirements. The selected approval must match the current
job. A changed job requires a new reviewed attempt; prior attempts remain in the
ledger. Reassigning `owner` alone does not change the job hash. Canonical input is
the job object without `owner`, serialized as sorted-key, compact JSON with UTF-8
characters preserved (`ensure_ascii=False`, separators `,` and `:`).

Persist the in-flight attempt **before** requesting media. After capture, add
`original: {path, sha256}` and set `pending_review`. The actual prompt may differ
from the manifest after a correction; hash and preserve both honestly. Keep the
tool/provider request ID and relevant settings as extra provenance where available.
Optionally snapshot actual references in `attempt.references`, using the same
fields as `job.references`. The checker validates their paths, provenance and
archive hashes too. A selected attempt's references must match the bound job;
when references change, update the job, compute its new hash and create a new
reviewed attempt. Historical snapshots may differ and remain in the ledger.

After inspecting that exact original, add:

```json
{
  "decision": "approved",
  "reviewer": "actual reviewer identity",
  "reviewedAt": "actual ISO-8601 review time",
  "method": "individual visual inspection",
  "notes": "Specific observed subject, text, count, identity and composition findings",
  "originalSha256": "hash of the exact original that was reviewed"
}
```

This is a field illustration, not a completed review. Use `rejected` with concrete
reasons for failed attempts and retain their files. Do not backfill fictional
times or approvals. Machines can check record consistency but cannot prove the
reviewer actually inspected the work.

Record delivery files as `outputs: [{path, sha256, format, width?, height?}]`
on the selected attempt. Output hashes cover delivered bytes, not the original.
Record derivative encoder/options and inspection notes alongside them. The helper
measures supported raster headers; it cannot replace visual inspection or a full
decoder. Other media require the host's format/duration/playback tools.

Approved old attempts may retain historical delivery paths, formats and hashes
after a newer attempt changes the delivery requirements. Keep their
attempt-specific originals. The
checker verifies current delivery files for `selectedAttempt`, and validates
historical record/original integrity separately.

## Commands

Run from any directory using the installed skill's actual script path:

```text
python <skill-folder>/scripts/media_workflow.py init <new-project-dir> --name <project-name> --site <website-url> --repository <repository-url>
python <skill-folder>/scripts/media_workflow.py hash <file>
python <skill-folder>/scripts/media_workflow.py job-hash <project-dir> <job-id>
python <skill-folder>/scripts/media_workflow.py status <project-dir>
python <skill-folder>/scripts/media_workflow.py verify <project-dir>
python <skill-folder>/scripts/media_workflow.py verify <project-dir> --complete --require-originals
```

`init` refuses an existing destination so it cannot erase ongoing work. The AI
edits the templates and writes records with ordinary file tools. The helper has
no media-provider call, network fetch, approval command, Git push or deployment.

`verify` checks the current partial state and does not claim completion.
`--complete` also requires a nonempty finished inventory and approved delivery
coverage. `--require-originals` also requires the original/reference archive to be
present. A missing archive without that flag is explicitly reported as unverified;
an existing file with a wrong hash fails either way. Do not rewrite hashes to
silence a failure. Investigate the changed file and re-review if necessary.

Completion also needs the AI's semantic review, source-identity/rights decisions,
and the intended integration/preview checks. Keep these in `workflow.md`. Neither
status totals nor a successful checker establishes source rights, exact product
truth, backup restoration, successful hosting or the absence of visual duplicates.

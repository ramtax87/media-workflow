# Media Workflow

Turn a short request into a complete, reviewable media job. The AI reads your
website or item list, plans the assets, produces or prepares them, checks every
result, and saves the evidence in your Git repository.

**Private preview · 0.1.0.** This repository is a private GitHub template. It has
not been published to a plugin directory. No public redistribution licence has
been selected. Image providers and source assets keep their own terms.

## Start with a prompt

Paste this into an AI assistant that can read files, browse and generate images:

> Use Media Workflow from this repository. I need photorealistic images for my
> website https://example.de. Read its public pages and catalogue, work out which
> images are needed, and create a consistent set. Use my private Git repository
> `<owner/site-repository>` for the work. Save the plan, exact prompts, originals,
> reviews and optimized delivery images. Keep the work private and prepare a
> reviewed branch; do not publish the website.

`example.de` is an example input, not a site this toolkit has crawled.
Replace the URL and repository. The assistant fills out the working files; you
do not need to author JSON. [Copy the prompt template](templates/START-HERE.md).

For existing products:

> Use Media Workflow. Here is my product list, including brand and pack size.
> Find the exact official product pictures and prepare square WebP files and
> smaller thumbnails for my private site repository. Preserve packaging text,
> logos and quantities. Use reference-based AI edits only where needed for the
> requested presentation, and keep the source beside each edited result. Flag
> uncertain matches and missing images instead of guessing.

The assistant can convert a source image, edit it with a supplied reference, or
generate an illustration. It records which happened. A generated photorealistic
image is not a camera photograph or an official manufacturer asset.

## What the AI produces

1. **Brief and inventory:** pages/items examined, exact subjects, placements,
   source links, missing facts, reuse decisions and image count.
2. **A workflow:** available tools, art direction, sizes/formats, assignments,
   budget/retry bounds and acceptance criteria.
3. **Durable job records:** exact prompts, source references, original files,
   attempts, reviews, corrections and hashes.
4. **Delivery:** approved assets, thumbnails/variants, page mapping, alt text and
   validation results. Website publication only when included in your request.

Interruptions are resumable. The AI reads saved attempts and approved work before
generating more. A valid checksum never counts as visual approval.

## Three ways to use it

| Route | What you do |
| --- | --- |
| **Any capable AI — simplest** | Clone/download this private repository, give the AI access to it, and tell it to read [SKILL.md](skills/media-workflow/SKILL.md). Then provide your prompt and destination repository. |
| **Standalone skill** | Copy the complete `skills/media-workflow` folder into a skill location supported by your assistant. Current Codex documentation uses `~/.agents/skills/` or `<target-repository>/.agents/skills/`. Invoke `$media-workflow`. |
| **Private plugin** | Use the included `plugin.json` and local marketplace. Follow [INSTALL.md](INSTALL.md). Installation remains separate from public publication. |

This package supplies instructions, templates and a small Python helper. The host
must provide website access, media generation/editing and visual/audio inspection.
It includes **no API key, image model, crawler, paid service subscription or
automatic deployment**. If generation is unavailable, the AI can prepare the
inventory and prompts and report the missing capability. It must not claim that
files were generated. Audio/video follow the same record process only when the
host has suitable generation and review tools; they are not bundled features.

## Files and checks

- [General workflow](skills/media-workflow/references/workflow.md)
- [Exact product images](skills/media-workflow/references/product-images.md)
- [Record format and helper commands](skills/media-workflow/references/records.md)
- [Prompt template](templates/START-HERE.md)
- [Product list template](templates/product-list.csv)
- [Security policy](security/BASELINE.md)

Python 3.11+ runs the optional helper and tests with no third-party dependencies:

```text
python skills/media-workflow/scripts/media_workflow.py --help
python -m unittest discover -s tests -v
python security/check_dependencies.py
python tools/build_package.py
```

For checks against a finished job, use `verify <project-dir> --complete`. Add
`--require-originals` when verifying the original archive too. The normal Git
handoff can omit that private archive, but it must say so. See the record guide.

Repository protection requires a pull request, the secret/dependency boundary
check, and application tests on Linux and Windows. No public service is deployed
by this toolkit. [Validation and limitations](docs/VALIDATION.md).

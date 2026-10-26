# Media Workflow

Read `security/BASELINE.md` before development. This is a private, portable media
workflow toolkit. Keep examples fictional and independent of any customer, lab,
hosting vendor or generation provider. Do not change repository visibility.

The single maintained skill lives in `skills/media-workflow/`. Keep it portable:
all its required instructions, templates and helpers belong inside that folder.
The host assistant supplies browsing, generation and visual/audio review tools;
the Python helper does not generate media, crawl websites or deploy projects.

Require `security-baseline` and `application-tests` on pull requests. Do not bypass
checks. Exercise path confinement, provenance, incomplete work and resume behavior
with disposable synthetic fixtures. Never mark synthetic fixtures as produced or
reviewed by a media model. Preserve originals, attempts and exact prompts.

# Validation scope — private preview 0.1.0

The implementation is an instruction/skill package with an optional standard-
library Python helper. It does not expose a server, authenticate customers, hold
provider credentials, crawl sites, generate media or deploy websites by itself.
The host assistant supplies those capabilities within the user's authorization.

Required repository checks are `security-baseline`,
`application-tests (ubuntu-24.04)` and `application-tests (windows-latest)`.
The active default-branch ruleset requires a pull request and passing checks,
prevents force-push/deletion, and has no bypass actors. It does not require a
separate human approving review.

The dependency check enforces no third-party runtime/test imports or dependency
declarations. With no third-party dependency graph, there are no package pins to
submit to a vulnerability service. If dependencies are introduced, the check
fails until pinned dependency auditing is configured. Gitleaks scans full Git
history with redacted findings. Python and OS security updates remain the host's
responsibility.

## Evidence

Executed on 26 October 2026 before the initial private pull request:

- Windows, Python 3.14.9: 42 unit tests completed successfully; one symlink test
  was skipped because the local account cannot create symlinks. Linux CI runs
  the same test without that Windows limitation.
- The dependency boundary check passed: the helper, tests and package builder
  require only Python's standard library.
- The skill-creator `quick_validate.py` check passed, using PyYAML 6.0.3 in an
  ignored validation environment outside the distributed runtime.
- `plugin.json` passed the Agent Plugins 1.0.0 JSON Schema using jsonschema
  4.26.0 in that environment. The retrieved schema's SHA-256 is
  `0a4aad95ce337878ad38802ebf0daa3fde76abe3f65400c86bcbb1ec0b3ab883`.
- An independent synthetic workflow exercise checked initialization, resume,
  completion, changed product facts, mismatched reviews and missing deliveries.
  It also extracted the archive and ran the installed helper. Its findings led
  to explicit attempt-reference checks and clearer pack-size guidance.
- Regression tests cover job revision binding, preserved historical attempts,
  changing delivery formats/paths, original archive checks, unsafe paths and
  deterministic package contents. Archive tests include the acceptance and
  security documents linked from its README.

GitHub's protected pull request supplies the secret scan and Linux/Windows test
results for the committed revision. Passing local checks alone does not replace
those gates. Automated fixtures use synthetic file bytes and workflow records;
they are not real generated pictures or evidence of successful visual review.

## Remaining acceptance

- Fresh plugin installation/discovery in the intended desktop client.
- A real generation/editing run using the host's available media tool.
- Exact product-source matching and actual-image inspection on a supplied list.
- Real audio/video generation and full-content review, if those modes are used.
- A destination website's own integration and deployment checks.

Until these are exercised, describe the result as a validated toolkit package,
not a proven end-to-end media service or a published plugin.

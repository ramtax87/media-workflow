# Private installation

The repository works as a readable guide without installation. Its skill is
self-contained, so copy the whole folder, including references, assets and
scripts. Do not install several copies into the same assistant.

## Download or clone

Sign into a GitHub account with access to this private repository. Use GitHub's
**Code → Download ZIP**, or:

```text
git clone https://github.com/ramtax87/media-workflow.git
```

Open the folder in your AI's workspace and ask it to read
`skills/media-workflow/SKILL.md`. The toolkit repository supplies the workflow;
your prompt identifies the separate destination repository for your website and
media. Do not accidentally push project assets into this toolkit.

The Python helper needs Python 3.11+; plain guide use does not. Browsing and media
generation/review are supplied by your assistant and may have their own fees.
The toolkit neither purchases credits nor enables another provider automatically.

## Standalone skill

Current Codex documentation discovers skills under `~/.agents/skills/` and
`<repository>/.agents/skills/`. Copy `skills/media-workflow` into one of those
directories. Reopen the assistant if it does not discover the new skill, then
invoke `$media-workflow`. Other assistants have their own supported locations;
use their documented mechanism or the plain-file route above.

The skill-creator tooling in some existing installations also uses
`~/.codex/skills/`. Use the location supported by your installed client rather
than creating duplicate copies. This repository does not alter global settings.

## Private Codex plugin

The root `plugin.json` follows the portable Agent Plugins manifest. Skills are
discovered in `skills/`; there is no MCP server or installation hook.

For clients with repository marketplaces, the included
`.agents/plugins/marketplace.json` points to the plugin at repository root `./`.
After cloning, use the local marketplace in the desktop Plugins directory; a
restart may be needed. Current documentation also provides:

```text
codex plugin marketplace add ramtax87/media-workflow --ref main
```

This registers the private marketplace; complete installation in the desktop
Plugins interface. GitHub access is still required. Availability and UI labels
depend on the client. If the marketplace command is unavailable, use the
standalone skill or plain guide. Do not change the repository to public to work
around installation access.

`python tools/build_package.py` creates a local install archive under `dist/`.
It includes only the package's documented source files, not `.git`, credentials,
working jobs, source images or build leftovers. The manifest requests a local
executor because workflow records and the optional helper use local files.
Private packaging does not publish to a universal directory.

## Verification scope

Automated tests check package structure and helper behavior. A fresh desktop
plugin installation and a real media-provider run are separate acceptance steps.
See `docs/VALIDATION.md` for what this version actually verified.

Documentation checked 26 October 2026:

- [Package a plugin](https://developers.openai.com/plugins/build/plugins)
- [Build and install skills](https://learn.chatgpt.com/docs/build-skills)
- [Desktop-only plugins](https://developers.openai.com/plugins/deploy/desktop-only)
- [Plugin testing](https://developers.openai.com/plugins/deploy/connect-chatgpt)

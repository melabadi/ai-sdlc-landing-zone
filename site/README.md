# The guide on GitHub Pages

[melabadi.github.io/ai-sdlc-landing-zone](https://melabadi.github.io/ai-sdlc-landing-zone/) walks through the landing zone's end-to-end run of 17 November 2026. For each of the seven phases it shows the steps with their screenshots, the artifacts with links, the acceptance criteria and how each was checked, and the next step. The same run, in Markdown, is [`docs/see-it-work/README.md`](../docs/see-it-work/README.md).

## Build it and look at it

```powershell
python site/build.py --serve 8000
```

Then open `http://127.0.0.1:8000/`. The build needs Python 3.12 or later and nothing else. It writes `_site/`, and fails if a link, an anchor, an `[#N]` reference, a repository path, or a screenshot doesn't exist. `python site/build.py --help` lists its options.

## Present the lifecycle

[Open the slideshow on GitHub Pages](https://melabadi.github.io/ai-sdlc-landing-zone/walkthrough/),
or select **Slideshow** in the guide's navigation. Locally, open `http://127.0.0.1:8000/walkthrough/`.
This is the browser presentation of **how we add AI to each SDLC phase**, not a replay of the recorded demo
and not a PowerPoint export. It names the exact capability—Copilot CLI, Copilot cloud agent, custom agents,
Agent Skills, Copilot code review, or GitHub Agentic Workflows—and explains how we use it.
The presentation has exactly one slide per phase (seven slides total). Each slide opens with its input.
Advance through three technology spotlights, one at a time:
each names the tool, explains how it is used, and shows a command, trigger, or customization example.
The fifth step reveals the checks, the human decision, and what the next team receives.
The phase title stays put during these reveals; a sideways transition marks a change of phase.
Select any numbered step to revisit it without replaying the phase.

The collapsed technology references link current official product guidance, including Microsoft Learn.
The slides describe this repository's implementation choices, not capabilities enabled automatically for every repository.
For example, our CI-investigation workflow is restricted to eligible Test lab pull requests, and the recorded
Test/Secure labs never merge; the presentation describes how the same test and remediation patterns fit a real lifecycle.
Agentic Workflows must be configured and compiled with gh-aw and an allowed engine; the deck is not a live monitor.

Use **EN / FR** to switch every presentation label and step between English and French without losing your place.
**Autoslide** starts paused and advances at a configurable 3–20 seconds per step; it stops at the last step.
Changing steps manually pauses it, and hidden browser tabs suspend the timer. **Full screen** uses the browser's
Fullscreen API; Escape exits. Arrow keys navigate, Home/End jump to the beginning/end, and Space toggles autoplay
when focus is outside a control. Reduced-motion preferences disable slide and timer animations.

Edit [`walkthrough.html`](walkthrough.html) for the shell, [`assets/walkthrough.css`](assets/walkthrough.css)
for the presentation styling, and [`assets/walkthrough.js`](assets/walkthrough.js) for the paired English/French
content and controls. Icons reuse the local, MIT-licensed Octicons; there are no external scripts or services.

Run the site integration checks with `python -m unittest discover -s site -p "test_*.py"`.
After building, `python site/check_walkthrough.py` also checks every technology spotlight, bilingual content,
navigation, playback, and responsive layout.
This optional browser check needs Python Playwright and its Chromium browser; the site build needs neither.

## Where things are

| Path | What it holds |
| --- | --- |
| [`site.toml`](site.toml) | The title, the repository, the order of the pages, and the Issues and pull requests that `[#N]` links to |
| [`pages/`](pages/) | One TOML file per page: [`home.toml`](pages/home.toml), the seven phases from [`plan.toml`](pages/plan.toml) to [`operate.toml`](pages/operate.toml), and [`results.toml`](pages/results.toml) |
| [`build.py`](build.py) | Renders the pages, draws the diagrams, copies the assets and the screenshots, and checks everything |
| [`layout.html`](layout.html) | The page shell: the head, the header, and the footer |
| [`assets/`](assets/) | The stylesheet, the screenshot viewer's script, the favicon, and the Mona Sans fonts with their licence, [`OFL.txt`](assets/fonts/OFL.txt) |
| [`icons/`](icons/) | The Octicons the pages use, with their [licence](icons/LICENSE) |

The screenshots come from [`docs/see-it-work/images/`](../docs/see-it-work/images/): the build copies them, so the guide and the Markdown walkthrough show the same files.

## Change it

- **Text:** edit the page's TOML file. Text fields take `code`, bold, emphasis, links, and `[#N]`; the docstring of [`build.py`](build.py) lists the link prefixes, such as `blob:path` for a file on `main` and `run:id` for a workflow run.
- **A step:** each `[[steps]]` entry has a lane (`person`, `copilot`, or `check`), a short label and reference for the diagram, a title, its text, and its screenshots. The phase's diagram and its list of steps both come from it.
- **The look:** [`assets/site.css`](assets/site.css). Its colors and type follow the GitHub Copilot Dev Days deck: green for a person, purple for Copilot, and gray for a deterministic check.
- **A new screenshot:** capture it with the source repository's `tools/screenshot.mjs` into `docs/see-it-work/images/`, and run its `tools/redact.py check` before you push it.

## Publish it

[`pages.yml`](../.github/workflows/pages.yml) builds the guide on every pull request that changes it, and builds and deploys it on every push to `main`. Pages must deploy from GitHub Actions, set once:

```powershell
gh api -X POST 'repos/{owner}/{repo}/pages' -f build_type=workflow
```

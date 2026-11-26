#!/usr/bin/env python3
"""Build the guide to the landing zone's end-to-end run, and publish it with GitHub Pages.

The guide walks through the recorded run of the seven accelerators on 17 November 2026, phase by phase: the steps,
each with its screenshots; the artifacts the phase produced; its acceptance criteria, how each was checked, and the
result; and its next step. Every artifact links to the real Issue, pull request, workflow run, commit, file, or
release on GitHub. The same run, in Markdown, is docs/see-it-work/README.md.

What it reads
  site/site.toml            the title, the repository, the order of the pages, and the Issues and pull requests
                            that [#N] links to
  site/pages/*.toml         one file per page: the home page, the seven phases, and the results
  site/layout.html          the page shell: the head, the header, and the footer
  site/assets/              the stylesheet, the script, the favicon, and the Mona Sans fonts (SIL Open Font License)
  site/icons/               the Octicons the pages use (MIT License)
  docs/see-it-work/images/  the screenshots of the run

What it writes
  --out (default _site/): index.html, a folder per page (plan/index.html, ...), 404.html, assets/, and images/.

What it checks, exiting with 1 when anything fails
  Every [#N] is listed in site.toml. Every blob: and tree: link names a file or folder that exists in the
  repository. Every link inside the site points at a page, a file, and an id that exist. Every screenshot exists,
  and every image has alt text. No markup is left unconverted.

Text fields take a little Markdown: `code`, **bold**, *emphasis* (shown in white, the way the deck emphasizes),
[label](target), and [#N] for an Issue or a pull request. A target is a URL, #id on the same page, or one of:
  page:plan#steps   a page of the guide, with an optional id
  blob:path         a file on main         tree:path      a folder on main
  commit:sha        a commit               prc:34/sha     a commit of a pull request
  run:id            a workflow run         release:tag    a release
  readme:#anchor    a heading of the repository's README
  source:path       a folder in the source repository of the accelerators
Blank lines separate paragraphs, and lines that start with "- " make a list.

Usage
  python site/build.py                          build into _site/
  python site/build.py --serve 8000             build, then serve the site at http://127.0.0.1:8000/
  python site/build.py --base-path /my-repo/    the path GitHub Pages publishes the site under, for 404.html
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import html
import http.server
import re
import shutil
import struct
import sys
import tomllib
from pathlib import Path
from string import Template
from urllib.parse import urljoin, urlsplit

import qr

SITE = Path(__file__).resolve().parent
REPO = SITE.parent
LANES = {"person": "A person", "copilot": "Copilot", "check": "A check"}
RESULT_ICONS = {"met": "check-circle", "fixed": "alert", "info": "eye", "fail": "x-circle"}
KIND_ICONS = {
    "Issue": "issue-opened", "Epic": "issue-tracked-by", "Pull request": "git-pull-request",
    "Merged pull request": "git-merge", "File": "file", "Folder": "file-directory", "Commit": "git-commit",
    "Workflow run": "workflow", "Release": "tag", "Images": "package", "Comment": "comment", "Branch": "git-branch",
    "Variable": "gear", "Label": "tag", "Scan": "shield-check",
}
PROBLEMS: list[str] = []


def problem(where: str, message: str) -> None:
    PROBLEMS.append(f"{where}: {message}")


def esc(text: str) -> str:
    return html.escape(text, quote=True)


@functools.cache
def icon_paths(name: str) -> str:
    path = SITE / "icons" / f"{name}-16.svg"
    if not path.is_file():
        problem("site/icons", f"no icon {name}-16.svg")
        return ""
    match = re.search(r"<svg[^>]*>(.*)</svg>", path.read_text(encoding="utf-8"), re.S)
    if not match:
        problem("site/icons", f"{name}-16.svg is not an SVG")
        return ""
    return match.group(1).strip()


def icon(name: str, cls: str = "") -> str:
    classes = f"octicon {cls}".strip()
    return (f'<svg class="{classes}" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" '
            f'focusable="false">{icon_paths(name)}</svg>')


def glyph(lane: str) -> str:
    return f'<span class="glyph glyph-{lane}" aria-hidden="true"></span>'


class Ctx:
    """Where a page lives, so its links resolve: root is the relative (or, for 404.html, absolute) site root."""

    def __init__(self, config: dict, root: str, where: str):
        self.config, self.root, self.where = config, root, where

    def gh(self, path: str = "") -> str:
        return f"https://github.com/{self.config['repository']}{path}"

    def page(self, slug: str, anchor: str = "") -> str:
        url = (self.root or "./") + ("" if slug == "home" else f"{slug}/")
        return url + (f"#{anchor}" if anchor else "")

    def ref(self, number: int) -> str:
        refs = self.config["refs"]
        if number in refs["issues"]:
            return self.gh(f"/issues/{number}")
        if number in refs["pulls"]:
            return self.gh(f"/pull/{number}")
        problem(self.where, f"#{number} is in neither refs.issues nor refs.pulls in site/site.toml")
        return "#"

    def url(self, target: str) -> str:
        if re.match(r"https?://", target) or target.startswith("#"):
            return target
        kind, sep, rest = target.partition(":")
        if not sep:
            problem(self.where, f"link target {target!r} is neither a URL, an #id, nor a known prefix")
            return "#"
        if kind == "page":
            slug, _, anchor = rest.partition("#")
            if slug not in self.config["slugs"]:
                problem(self.where, f"{target}: no page {slug!r}")
            return self.page(slug, anchor)
        if kind in ("blob", "tree"):
            path = REPO / rest
            if not (path.is_file() if kind == "blob" else path.is_dir()):
                problem(self.where, f"{target}: no such {'file' if kind == 'blob' else 'folder'} in the repository")
            return self.gh(f"/{kind}/main/{rest}")
        simple = {"commit": "/commit/{}", "run": "/actions/runs/{}", "release": "/releases/tag/{}",
                  "issue": "/issues/{}", "pr": "/pull/{}"}
        if kind in simple:
            return self.gh(simple[kind].format(rest))
        if kind == "prc":
            number, _, sha = rest.partition("/")
            return self.gh(f"/pull/{number}/commits/{sha}")
        if kind == "readme":
            return self.gh(rest)
        if kind == "source":
            return f"https://github.com/{self.config['source']}/tree/main/{rest}"
        problem(self.where, f"link target {target!r} has an unknown prefix {kind!r}")
        return "#"


TOKEN = re.compile(r"`([^`]+)`|\[([^\]]+)\]\(([^)\s]+)\)|\[#(\d+)\]|\*\*(.+?)\*\*|\*([^*\s][^*]*?)\*")


def inline(text: str, ctx: Ctx, links: bool = True) -> str:
    """Convert the inline Markdown of one line or paragraph to HTML. links=False inside an element that is a link."""
    out, pos = [], 0
    for match in TOKEN.finditer(text):
        plain = text[pos:match.start()]
        leftover(plain, ctx)
        out.append(esc(plain))
        code, label, target, ref, bold, emphasis = match.groups()
        if code is not None:
            out.append(f"<code>{esc(code)}</code>")
        elif label is not None:
            if not links:
                problem(ctx.where, f"no link allowed here, inside another link: {match.group(0)}")
                out.append(inline(label, ctx, links=False))
            else:
                out.append(f'<a href="{esc(ctx.url(target))}">{inline(label, ctx, links=False)}</a>')
        elif ref is not None:
            out.append(f'<a href="{esc(ctx.ref(int(ref)))}">#{ref}</a>' if links else f"#{ref}")
        elif bold is not None:
            out.append(f"<strong>{inline(bold, ctx, links)}</strong>")
        else:
            out.append(f"<em>{inline(emphasis, ctx, links)}</em>")
        pos = match.end()
    tail = text[pos:]
    leftover(tail, ctx)
    out.append(esc(tail))
    return "".join(out)


def leftover(plain: str, ctx: Ctx) -> None:
    if re.search(r"\]\(|\[#\d|\*\*|`", plain):
        problem(ctx.where, f"unconverted markup in: {plain.strip()[:90]}")


def plain_text(text: str) -> str:
    """Inline Markdown without its markup, for the description meta tag."""
    text = re.sub(r"\[([^\]]+)\]\([^)\s]+\)", r"\1", " ".join(text.split()))
    return re.sub(r"\*\*|\*|`", "", re.sub(r"\[#(\d+)\]", r"#\1", text))


def blocks(text: str, ctx: Ctx) -> str:
    """Paragraphs separated by blank lines; a block whose lines all start with "- " is a list."""
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if lines and all(line.startswith("- ") for line in lines):
            out.append("<ul>" + "".join(f"<li>{inline(line[2:], ctx)}</li>" for line in lines) + "</ul>")
        elif lines:
            out.append(f"<p>{inline(' '.join(lines), ctx)}</p>")
    return "\n".join(out)


def png_size(path: Path) -> tuple[int, int]:
    head = path.read_bytes()[:24]
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        problem(str(path.relative_to(REPO)), "not a PNG file")
        return (0, 0)
    return struct.unpack(">II", head[16:24])


def figure(image: dict, ctx: Ctx, images: Path) -> str:
    path = images / image["file"]
    if not path.is_file():
        problem(ctx.where, f"no screenshot {image['file']} in {images.relative_to(REPO).as_posix()}")
        return ""
    width, height = png_size(path)
    # The screenshots are 2x captures: show them at their CSS pixel size, never larger.
    tall = height > width
    src = f"{ctx.root}images/{image['file']}"
    return (f'<figure class="shot{" shot-tall" if tall else ""}">'
            f'<a class="shot-link" href="{esc(src)}" title="Open full size">'
            f'<img src="{esc(src)}" alt="{esc(image["alt"])}" width="{width // 2}" height="{height // 2}" '
            f'loading="lazy" decoding="async"></a></figure>')


# ---------------------------------------------------------------------------------------------------------------
# Pieces shared by the pages


def section_head(eyebrow: str, title: str, anchor: str, ctx: Ctx, lead: str = "") -> str:
    lead_html = f'<div class="section-lead">{blocks(lead, ctx)}</div>' if lead else ""
    return (f'<header class="section-head"><p class="eyebrow eyebrow-green">{inline(eyebrow, ctx)}</p>'
            f'<h2 id="{anchor}-title">{inline(title, ctx)}</h2>{lead_html}</header>')


def legend() -> str:
    return ('<ul class="legend" aria-label="Who does what">'
            f'<li>{glyph("person")}<strong>A person</strong> decides</li>'
            f'<li>{glyph("copilot")}<strong>Copilot</strong> proposes</li>'
            f'<li>{glyph("check")}<strong>A check</strong> decides it is complete</li></ul>')


def flow(steps: list[dict], ctx: Ctx) -> str:
    """The phase's steps as a row of role-colored cards, like the deck's CODE and AGENT boxes."""
    items = []
    for number, step in enumerate(steps, 1):
        lane = step["lane"]
        role = step.get("role", LANES[lane])
        gate = ""
        if "gate" in step:
            state = step["gate"]["state"]
            gate = (f'<span class="gate gate-{state}">{icon("check-circle" if state == "pass" else "x-circle")}'
                    f'{inline(step["gate"]["text"], ctx, links=False)}</span>')
        items.append(
            f'<li class="node lane-{lane}"><a class="node-card" href="#step-{number}">'
            f'<span class="node-role">{glyph(lane)}{esc(role)}</span>'
            f'<span class="node-num">{number:02d}</span>'
            f'<span class="node-label">{inline(step["label"], ctx, links=False)}</span>'
            f'<span class="node-ref">{inline(step["ref"], ctx, links=False)}</span></a>{gate}</li>')
    return f'<ol class="flow" style="--nodes: {len(steps)}">{"".join(items)}</ol>'


def pager(prev: tuple[str, str, str], nxt: tuple[str, str, str], ctx: Ctx) -> str:
    """prev and nxt are (slug, small label, title)."""
    def link(item: tuple[str, str, str], cls: str, direction: str) -> str:
        slug, small, title = item
        arrow = icon("arrow-left") if cls == "prev" else icon("arrow-right")
        label = f"{arrow}{esc(direction)} · {esc(small)}" if cls == "prev" else f"{esc(direction)} · {esc(small)}{arrow}"
        return (f'<a class="pager-link pager-{cls}" href="{esc(ctx.page(slug))}">'
                f'<span class="pager-dir">{label}</span><span class="pager-title">{esc(title)}</span></a>')
    return (f'<nav class="pager" aria-label="Previous and next">{link(prev, "prev", "Previous")}'
            f'{link(nxt, "next", "Next")}</nav>')


def neighbours(pages: list[dict], page: dict) -> tuple[tuple[str, str, str], tuple[str, str, str]]:
    def describe(p: dict) -> tuple[str, str, str]:
        if p["kind"] == "phase":
            return (p["slug"], f"Phase {p['number']:02d}", p["name"])
        return (p["slug"], "Overview" if p["kind"] == "home" else "Results", p.get("nav_title", p["title"]))
    i = pages.index(page)
    return describe(pages[i - 1]), describe(pages[(i + 1) % len(pages)])


# ---------------------------------------------------------------------------------------------------------------
# The home page


def chain_svg(phases: list[dict], ctx: Ctx) -> str:
    """The seven accelerators in order, each linking to its phase, and Operate's follow-up looping back to Develop."""
    width, count, node_w, node_h, top = 1120, len(phases), 132, 112, 6
    gap = (width - count * node_w) / (count - 1)

    def x(i: int) -> float:
        return i * (node_w + gap)

    middle = top + node_h / 2
    bottom = top + node_h
    loop_y = bottom + 46
    parts = [
        # No role="img": it would hide the phases' links from screen readers.
        f'<svg class="chain" viewBox="0 0 {width} {loop_y + 34}" aria-labelledby="chain-title chain-desc">',
        '<title id="chain-title">The seven accelerators, in order</title>',
        '<desc id="chain-desc">Plan, Design, Develop, Test, Secure, Release, and Operate, each handing its output to '
        'the next. A follow-up Issue from Operate goes back to Copilot in Develop, through the same checks.</desc>',
        '<defs><marker id="chain-head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto"><path class="chain-head" d="M0 0L10 5L0 10z"/></marker>'
        '<marker id="loop-head" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto"><path class="loop-head" d="M0 0L10 5L0 10z"/></marker></defs>',
    ]
    for i in range(count - 1):
        parts.append(f'<line class="chain-arrow" x1="{x(i) + node_w + 5:.1f}" y1="{middle}" '
                     f'x2="{x(i + 1) - 7:.1f}" y2="{middle}" marker-end="url(#chain-head)"/>')
    develop = next(i for i, p in enumerate(phases) if p["slug"] == "develop")
    out_x, in_x = x(count - 1) + node_w / 2, x(develop) + node_w / 2
    parts.append(f'<path class="chain-loop" d="M{out_x:.1f} {bottom + 4} V{loop_y - 12} Q{out_x:.1f} {loop_y} '
                 f'{out_x - 12:.1f} {loop_y} H{in_x + 12:.1f} Q{in_x:.1f} {loop_y} {in_x:.1f} {loop_y - 12} '
                 f'V{bottom + 9}" marker-end="url(#loop-head)"/>')
    parts.append(f'<text class="chain-loop-label" x="{(out_x + in_x) / 2:.1f}" y="{loop_y + 24}" '
                 f'text-anchor="middle">A follow-up Issue goes back to Copilot, through the same checks</text>')
    for i, phase in enumerate(phases):
        left = x(i)
        lines = "".join(f'<text class="chain-out" x="{left + 16:.1f}" y="{top + 82 + 18 * n}">{esc(line)}</text>'
                        for n, line in enumerate(phase["overview"]["output"]))
        parts.append(
            f'<a class="chain-node" href="{esc(ctx.page(phase["slug"]))}">'
            f'<title>Phase {phase["number"]:02d}: {esc(phase["name"])}</title>'
            f'<rect x="{left:.1f}" y="{top}" width="{node_w}" height="{node_h}" rx="10"/>'
            f'<text class="chain-num" x="{left + 16:.1f}" y="{top + 28}">{phase["number"]:02d}</text>'
            f'<text class="chain-name" x="{left + 16:.1f}" y="{top + 56}">{esc(phase["name"])}</text>{lines}</a>')
    parts.append("</svg>")
    return "".join(parts)


def principle_glyph(lane: str) -> str:
    """Small node drawings, like the deck's Single, Cascade, and Critique cards."""
    drawings = {
        "copilot": '<circle cx="9" cy="9" r="8" class="g-copilot"/><path d="M24 9h20" class="g-line"/>'
                   '<path d="M40 5l5 4-5 4" class="g-line"/><circle cx="60" cy="9" r="7.5" class="g-ring"/>',
        "check": '<circle cx="9" cy="9" r="7.5" class="g-ring"/><path d="M24 9h16" class="g-line"/>'
                 '<rect x="47" y="3" width="12" height="12" transform="rotate(45 53 9)" class="g-diamond"/>'
                 '<path d="M66 9h16" class="g-line"/><circle cx="97" cy="9" r="7.5" class="g-ring"/>',
        "person": '<circle cx="9" cy="9" r="7.5" class="g-ring"/><path d="M24 9h20" class="g-line"/>'
                  '<path d="M40 5l5 4-5 4" class="g-line"/><circle cx="60" cy="9" r="8" class="g-person"/>'
                  '<path d="M56 9l3 3 5-6" class="g-tick"/>',
    }
    return f'<svg class="principle-glyph" viewBox="0 0 106 18" aria-hidden="true">{drawings[lane]}</svg>'


def render_home(page: dict, ctx: Ctx, phases: list[dict], pages: list[dict]) -> str:
    stats = "".join(f'<div class="stat"><dt>{inline(s["label"], ctx)}</dt><dd>{esc(s["value"])}</dd></div>'
                    for s in page["stats"])
    hero = (f'<section class="hero hero-home"><div class="wrap">'
            f'<p class="eyebrow">{inline(page["eyebrow"], ctx)}</p><h1>{inline(page["title"], ctx)}</h1>'
            f'<div class="lead">{blocks(page["lead"], ctx)}</div>'
            f'<p class="actions"><a class="button button-primary" href="{esc(ctx.page("plan"))}">Walk through the run'
            f'{icon("arrow-right")}</a><a class="button" href="{esc(ctx.gh())}">{icon("mark-github")}'
            f'View the repository</a></p><dl class="stats">{stats}</dl></div></section>')

    how = page["how"]
    principles = "".join(
        f'<li class="principle lane-{p["lane"]}">{principle_glyph(p["lane"])}<h3>{inline(p["title"], ctx)}</h3>'
        f'{blocks(p["text"], ctx)}</li>' for p in how["principles"])

    def layer(item: dict) -> str:
        chips = "".join(f"<li>{inline(chip, ctx)}</li>" for chip in item.get("chips", []))
        text = blocks(item["text"], ctx) if "text" in item else ""
        return (f'<div class="layer layer-{item["kind"]}"><p class="layer-name">{inline(item["name"], ctx)}</p>'
                f'{f"<ul class=chips>{chips}</ul>" if chips else ""}{text}</div>')

    above = "".join(layer(item) for item in how["layers"] if item["kind"] == "gov")
    below = "".join(layer(item) for item in how["layers"] if item["kind"] != "gov")
    # On a phone the diagram would need sideways scrolling, so the same chain is also a list, shown instead.
    chain_list = "".join(
        f'<li><a href="{esc(ctx.page(p["slug"]))}"><span class="chain-list-num">{p["number"]:02d}</span>'
        f'<span class="chain-list-name">{esc(p["name"])}</span>'
        f'<span class="chain-list-out">{esc(" · ".join(p["overview"]["output"]))}</span></a></li>' for p in phases)
    landscape = (f'<figure class="landscape">{above}<div class="layer layer-acc">'
                 f'<p class="layer-name">{inline(how["accelerators"], ctx)}</p>'
                 f'<div class="chain-scroll">{chain_svg(phases, ctx)}</div>'
                 f'<ol class="chain-list">{chain_list}</ol>'
                 f'<p class="chain-list-loop">From Operate, a follow-up Issue goes back to Copilot in Develop, '
                 f'through the same checks.</p></div>{below}'
                 f'<figcaption>{inline(how["caption"], ctx)}</figcaption></figure>')
    how_html = (f'<section class="section" id="how-it-works" aria-labelledby="how-it-works-title"><div class="wrap">'
                f'{section_head(how["eyebrow"], how["title"], "how-it-works", ctx, how["lead"])}'
                f'<ul class="principles">{principles}</ul>{landscape}</div></section>')

    run = page["run"]
    cards = []
    for phase in phases:
        o = phase["overview"]
        facts = "".join(f"<div><dt>{label}</dt><dd>{inline(o[key], ctx)}</dd></div>" for key, label in
                        (("starts", "Starts with"), ("copilot", "Copilot"), ("gate", "Decides it is complete"),
                         ("person", "A person")))
        cards.append(
            f'<li class="phase-card"><a class="phase-card-head" href="{esc(ctx.page(phase["slug"]))}">'
            f'<span class="phase-card-num">{phase["number"]:02d}</span>'
            f'<span class="phase-card-name">{esc(phase["name"])}</span>'
            f'<span class="phase-card-title">{inline(phase["title"], ctx, links=False)}</span></a>'
            f'<dl class="phase-card-facts">{facts}</dl>'
            f'<a class="phase-card-more" href="{esc(ctx.page(phase["slug"]))}" aria-label="Walk through phase '
            f'{phase["number"]}, {esc(phase["name"])}">Walk through it{icon("arrow-right")}</a></li>')
    run_html = (f'<section class="section" id="the-run" aria-labelledby="the-run-title"><div class="wrap">'
                f'{section_head(run["eyebrow"], run["title"], "the-run", ctx, run["lead"])}'
                f'<ol class="phase-cards">{"".join(cards)}</ol></div></section>')

    setup = page["setup"]
    governance = "".join(
        f'<div class="gov-row"><dt>{inline(g["name"], ctx)}</dt><dd><p class="gov-value">{inline(g["value"], ctx)}</p>'
        f'<p class="gov-why">{inline(g["why"], ctx)}</p></dd></div>' for g in setup["governance"])
    foundation = "".join(f'<li><strong>{inline(f["name"], ctx)}</strong> {inline(f["text"], ctx)}</li>'
                         for f in setup["foundation"])
    setup_html = (f'<section class="section" id="set-once" aria-labelledby="set-once-title"><div class="wrap">'
                  f'{section_head(setup["eyebrow"], setup["title"], "set-once", ctx, setup["lead"])}'
                  f'<div class="setup"><div class="card"><h3>Governance</h3><dl class="gov">{governance}</dl></div>'
                  f'<div class="card"><h3>What the accelerators share</h3><ul class="foundation">{foundation}</ul>'
                  f'</div></div></div></section>')

    build = page["build"]
    build_steps = "".join(
        f'<li><span class="build-num">{n:02d}</span><h3><a href="{esc(ctx.url(s["href"]))}">'
        f'{inline(s["title"], ctx, links=False)}</a></h3>{blocks(s["text"], ctx)}</li>'
        for n, s in enumerate(build["steps"], 1))
    build_html = (f'<section class="section" id="build-your-own" aria-labelledby="build-your-own-title">'
                  f'<div class="wrap">{section_head(build["eyebrow"], build["title"], "build-your-own", ctx, build["lead"])}'
                  f'<ol class="build-steps">{build_steps}</ol></div></section>')

    about = page["about"]
    about_html = (f'<section class="section section-quiet" id="about-the-run" aria-labelledby="about-the-run-title">'
                  f'<div class="wrap narrow"><h2 id="about-the-run-title" class="h3">{inline(about["title"], ctx)}</h2>'
                  f'{blocks(about["text"], ctx)}</div></section>')
    return hero + how_html + run_html + setup_html + build_html + about_html


# ---------------------------------------------------------------------------------------------------------------
# A phase page


def render_phase(page: dict, ctx: Ctx, phases: list[dict], pages: list[dict]) -> str:
    facts = page["facts"]
    facts_html = "".join(f"<div><dt>{label}</dt><dd>{inline(facts[key], ctx)}</dd></div>" for key, label in
                         (("starts", "Starts with"), ("produces", "Copilot produces"),
                          ("complete", "Complete when"), ("decides", "A person decides")))
    accelerator = page["accelerator"]
    hero = (f'<section class="hero hero-phase"><div class="wrap">'
            f'<p class="eyebrow">Phase {page["number"]:02d} · {esc(page["name"])}</p>'
            f'<h1>{inline(page["title"], ctx)}</h1><div class="lead">{blocks(page["lead"], ctx)}</div>'
            f'<p class="hero-link"><a href="{esc(ctx.url("source:" + accelerator))}">{icon("book")}'
            f'The accelerator: {esc(accelerator.rsplit("/", 1)[-1])}{icon("link-external")}</a></p>'
            f'<dl class="facts">{facts_html}</dl>'
            f'<nav class="on-page" aria-label="On this page"><ul>'
            f'<li><a href="#steps">Steps</a></li><li><a href="#artifacts">Artifacts</a></li>'
            f'<li><a href="#acceptance-criteria">Acceptance criteria</a></li><li><a href="#next-step">Next step</a></li>'
            f'</ul></nav></div></section>')

    images = REPO / ctx.config["images"]
    steps = []
    for number, step in enumerate(page["steps"], 1):
        lane = step["lane"]
        shots = "".join(figure(image, ctx, images) for image in step.get("images", []))
        steps.append(
            f'<li class="step lane-{lane}" id="step-{number}">'
            f'<div class="step-marker" aria-hidden="true"><span class="step-dot">{number:02d}</span></div>'
            f'<div class="step-body"><p class="step-role">{glyph(lane)}{esc(step.get("role", LANES[lane]))}</p>'
            f'<h3><span class="visually-hidden">Step {number}. </span>{inline(step["title"], ctx)}</h3>'
            f'{blocks(step["text"], ctx)}{shots}</div></li>')
    steps_html = (f'<section class="section" id="steps" aria-labelledby="steps-title"><div class="wrap">'
                  f'{section_head("Who did what", "Steps", "steps", ctx)}'
                  f'<div class="flow-wrap">{flow(page["steps"], ctx)}{legend()}</div>'
                  f'<ol class="steps">{"".join(steps)}</ol></div></section>')

    cards = []
    for artifact in page["artifacts"]:
        kind = artifact["kind"]
        href = ctx.url(artifact["href"]) if "href" in artifact else ""
        name = inline(artifact["name"], ctx, links=False)
        name_html = (f'<a class="artifact-name" href="{esc(href)}">{name}</a>' if href
                     else f'<span class="artifact-name">{name}</span>')
        note = f'<p class="artifact-note">{inline(artifact["note"], ctx)}</p>' if "note" in artifact else ""
        cards.append(f'<li class="artifact{" artifact-link" if href else ""}">'
                     f'<span class="artifact-icon">{icon(KIND_ICONS.get(kind, "file"))}</span>'
                     f'<div class="artifact-text"><p class="artifact-kind">{esc(kind)}</p>{name_html}{note}</div></li>')
        if kind not in KIND_ICONS:
            problem(ctx.where, f"artifact kind {kind!r} has no icon in KIND_ICONS")
    artifacts_html = (f'<section class="section" id="artifacts" aria-labelledby="artifacts-title"><div class="wrap">'
                      f'{section_head("What the phase produced", "Artifacts", "artifacts", ctx)}'
                      f'<ul class="artifacts">{"".join(cards)}</ul></div></section>')

    source = page.get("criteria_source")
    head = f"Criterion, from {inline(source, ctx)}" if source else "Criterion"
    rows = []
    for row in page["criteria"]:
        state = row["state"]
        if state not in RESULT_ICONS:
            problem(ctx.where, f"criterion state {state!r} is not one of {', '.join(RESULT_ICONS)}")
        rows.append(f'<tr><td>{inline(row["criterion"], ctx)}</td><td>{inline(row["check"], ctx)}</td>'
                    f'<td><span class="result result-{state}">{icon(RESULT_ICONS.get(state, "eye"))}'
                    f'<span>{inline(row["result"], ctx)}</span></span></td></tr>')
    intro = blocks(page["criteria_intro"], ctx) if "criteria_intro" in page else ""
    criteria_html = (f'<section class="section" id="acceptance-criteria" aria-labelledby="acceptance-criteria-title">'
                     f'<div class="wrap">{section_head("What decided it was complete", "Acceptance criteria", "acceptance-criteria", ctx)}'
                     f'{intro}<div class="table-wrap"><table class="criteria"><thead><tr><th scope="col">{head}</th>'
                     f'<th scope="col">How it was checked</th><th scope="col">Result</th></tr></thead>'
                     f'<tbody>{"".join(rows)}</tbody></table></div></div></section>')

    prev, nxt = neighbours(pages, page)
    next_html = (f'<section class="section section-next" id="next-step" aria-labelledby="next-step-title">'
                 f'<div class="wrap"><div class="next-card"><p class="eyebrow eyebrow-green">What it hands on</p>'
                 f'<h2 id="next-step-title">Next step</h2>{blocks(page["next"], ctx)}</div>'
                 f'{pager(prev, nxt, ctx)}</div></section>')
    return hero + steps_html + artifacts_html + criteria_html + next_html


# ---------------------------------------------------------------------------------------------------------------
# The results page


def table(columns: list[str], rows: list[list[str]], ctx: Ctx, total: list[str] | None = None) -> str:
    head = "".join(f'<th scope="col">{esc(c)}</th>' for c in columns)
    body = "".join("<tr>" + "".join(f"<td>{inline(cell, ctx)}</td>" for cell in row) + "</tr>" for row in rows)
    foot = ("<tfoot><tr>" + "".join(f"<td>{inline(cell, ctx)}</td>" for cell in total) + "</tr></tfoot>"
            if total else "")
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody>{foot}</table></div>'


def render_results(page: dict, ctx: Ctx, phases: list[dict], pages: list[dict]) -> str:
    hero = (f'<section class="hero hero-phase"><div class="wrap"><p class="eyebrow">{inline(page["eyebrow"], ctx)}</p>'
            f'<h1>{inline(page["title"], ctx)}</h1><div class="lead">{blocks(page["lead"], ctx)}</div>'
            f'<nav class="on-page" aria-label="On this page"><ul><li><a href="#findings">Findings</a></li>'
            f'<li><a href="#cost">What it cost</a></li><li><a href="#run-it-again">Run it again</a></li></ul></nav>'
            f'</div></section>')
    findings = "".join(f'<li class="finding"><span class="finding-num">{n:02d}</span>'
                       f'<h3>{inline(f["title"], ctx)}</h3>{blocks(f["text"], ctx)}</li>'
                       for n, f in enumerate(page["findings"], 1))
    findings_html = (f'<section class="section" id="findings" aria-labelledby="findings-title"><div class="wrap">'
                     f'{section_head("What the run found", "Seven findings", "findings", ctx, page["findings_lead"])}'
                     f'<ol class="findings">{findings}</ol></div></section>')

    cost = page["cost"]
    details = "".join(f'<div class="cost-detail"><h3>{esc(d["title"])}</h3>'
                      f'{table(d["columns"], d["rows"], ctx)}</div>' for d in cost["details"])
    cost_html = (f'<section class="section" id="cost" aria-labelledby="cost-title"><div class="wrap">'
                 f'{section_head("AI credits and runner minutes", "What it cost", "cost", ctx, cost["lead"])}'
                 f'{table(cost["columns"], cost["rows"], ctx, cost["total"])}'
                 f'<details class="cost-details"><summary>Each session, review, and agentic workflow</summary>'
                 f'<div class="cost-grid">{details}</div></details>'
                 f'<div class="note">{blocks(cost["note"], ctx)}</div></div></section>')

    again = page["again"]
    items = "".join(f'<li class="card"><h3>{inline(i["title"], ctx)}</h3>{blocks(i["text"], ctx)}</li>'
                    for i in again["items"])
    prev, nxt = neighbours(pages, page)
    again_html = (f'<section class="section section-next" id="run-it-again" aria-labelledby="run-it-again-title">'
                  f'<div class="wrap">{section_head("Before you repeat a phase", "Run it again", "run-it-again", ctx, again["lead"])}'
                  f'<ul class="again">{items}</ul><div class="note">{blocks(again["closing"], ctx)}</div>'
                  f'{pager(prev, nxt, ctx)}</div></section>')
    return hero + findings_html + cost_html + again_html


def render_404(ctx: Ctx) -> str:
    return (f'<section class="hero hero-phase"><div class="wrap"><p class="eyebrow">404</p>'
            f'<h1>This page is not part of the guide.</h1><div class="lead"><p>It may have moved. Start from the '
            f'overview, or go straight to the first phase of the run.</p></div>'
            f'<p class="actions"><a class="button button-primary" href="{esc(ctx.page("home"))}">The overview'
            f'{icon("arrow-right")}</a><a class="button" href="{esc(ctx.page("plan"))}">Phase 01 · Plan</a></p>'
            f'</div></section>')


RENDERERS = {"home": render_home, "phase": render_phase, "results": render_results}


# ---------------------------------------------------------------------------------------------------------------
# The shell, the build, and the checks


def stepper(phases: list[dict], current: dict, ctx: Ctx) -> str:
    items = []
    for phase in phases:
        state = ("current" if phase is current else
                 "done" if phase["number"] < current["number"] else "todo")
        aria = ' aria-current="step"' if phase is current else ""
        items.append(f'<li class="{state}"><a href="{esc(ctx.page(phase["slug"]))}"{aria}>'
                     f'<span class="stepper-num">{phase["number"]:02d}</span>{esc(phase["name"])}</a></li>')
    return f'<nav class="stepper" aria-label="The seven phases"><ol class="wrap">{"".join(items)}</ol></nav>'


def nav(section: str, ctx: Ctx) -> str:
    entries = [("how", "How it works", ctx.page("home", "how-it-works")), ("run", "The run", ctx.page("plan")),
               ("walkthrough", "Slideshow", ctx.page("walkthrough")),
               ("results", "Results", ctx.page("results"))]
    items = [f'<li><a href="{esc(href)}"{" aria-current=page" if key == section else ""}>{label}</a></li>'
             for key, label, href in entries]
    items.append(f'<li><a href="{esc(ctx.gh())}">{icon("mark-github")}Repository</a></li>')
    return "".join(items)


def shell(layout: Template, ctx: Ctx, title: str, description: str, content: str, section: str = "",
          steps: str = "", body_class: str = "") -> str:
    return layout.substitute(
        title=esc(title), description=esc(description), root=ctx.root, home=esc(ctx.page("home")),
        nav=nav(section, ctx), stepper=steps, content=content, body_class=body_class,
        repo_url=esc(ctx.gh()), source_url=esc(f"https://github.com/{ctx.config['source']}"),
        license_url=esc(ctx.gh("/blob/main/LICENSE")), octocat=icon("mark-github", "octicon-mark"))


def load() -> tuple[dict, list[dict]]:
    config = tomllib.loads((SITE / "site.toml").read_text(encoding="utf-8"))
    pages = []
    for name in config["pages"]:
        page = tomllib.loads((SITE / "pages" / name).read_text(encoding="utf-8"))
        page["file"] = f"site/pages/{name}"
        pages.append(page)
    config["slugs"] = {page["slug"] for page in pages} | {"walkthrough"}
    return config, pages


def render(config: dict, pages: list[dict], base_path: str) -> dict[str, str]:
    layout = Template((SITE / "layout.html").read_text(encoding="utf-8"))
    phases = [page for page in pages if page["kind"] == "phase"]
    site_title = config["title"]
    out = {}
    for page in pages:
        home = page["kind"] == "home"
        ctx = Ctx(config, "" if home else "../", page["file"])
        content = RENDERERS[page["kind"]](page, ctx, phases, pages)
        if home:
            title, section, steps = f"{site_title}: {page['nav_title']}", "how", ""
        elif page["kind"] == "phase":
            title, section = f"{page['number']:02d} {page['name']}: {page['title']} · {site_title}", "run"
            steps = stepper(phases, page, ctx)
        else:
            title, section, steps = f"{page['title']} · {site_title}", "results", ""
        description = plain_text(page["lead"].strip().split("\n\n")[0])
        out["index.html" if home else f"{page['slug']}/index.html"] = shell(
            layout, ctx, title, description, content, section, steps, f"page-{page['kind']}")
    ctx = Ctx(config, base_path, "404.html")
    out["404.html"] = shell(layout, ctx, f"Not found · {site_title}", config["description"], render_404(ctx))
    presentation = Template((SITE / "walkthrough.html").read_text(encoding="utf-8"))
    names = ("mark-github", "issue-opened", "git-branch", "git-pull-request", "check-circle",
             "shield-check", "package", "workflow", "comment", "arrow-left", "arrow-right", "book",
             "gear", "git-merge", "file", "eye", "copilot", "terminal", "code-review")
    symbols = "".join(f'<symbol id="icon-{name}" viewBox="0 0 16 16">{icon_paths(name)}</symbol>'
                      for name in names)
    out["walkthrough/index.html"] = presentation.substitute(
        symbols=symbols, repo_url=esc(ctx.gh()),
        qr_svg=qr.to_svg(qr.encode(ctx.gh())),
        style_version=hashlib.sha256((SITE / "assets" / "walkthrough.css").read_bytes()).hexdigest()[:12],
        script_version=hashlib.sha256((SITE / "assets" / "walkthrough.js").read_bytes()).hexdigest()[:12])
    return out


def check(rendered: dict[str, str], out: Path, base_path: str) -> None:
    ids = {}
    for rel, doc in rendered.items():
        found = re.findall(r'\sid="([^"]+)"', doc)
        for dupe in sorted({i for i in found if found.count(i) > 1}):
            problem(rel, f"id {dupe!r} is used more than once")
        ids[rel] = set(found)
        for tag in re.findall(r"<img\b[^>]*>", doc):
            if not re.search(r'\salt="[^"]+"', tag):
                problem(rel, f"an image has no alt text: {tag[:80]}")
    for rel, doc in rendered.items():
        page_path = base_path + ("" if rel == "index.html" else rel.removesuffix("index.html"))
        for attr, value in re.findall(r'\s(href|src)="([^"]*)"', doc):
            value = html.unescape(value)
            if re.match(r"(https?:|mailto:)", value):
                continue
            parts = urlsplit(urljoin("https://site.invalid" + page_path, value))
            if not parts.path.startswith(base_path):
                problem(rel, f"{attr}={value} leaves the site")
                continue
            target = parts.path[len(base_path):]
            if target == "" or target.endswith("/"):
                target += "index.html"
            if not (out / target).is_file():
                problem(rel, f"{attr}={value}: nothing at {target}")
            elif parts.fragment and target in ids and parts.fragment not in ids[target]:
                problem(rel, f"{attr}={value}: no id {parts.fragment!r} in {target}")


def build(out: Path, base_path: str) -> int:
    config, pages = load()
    rendered = render(config, pages, base_path)
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(SITE / "assets", out / "assets")
    images = REPO / config["images"]
    shutil.copytree(images, out / "images", ignore=shutil.ignore_patterns("*.md"))
    for rel, doc in rendered.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(doc, encoding="utf-8", newline="\n")
    check(rendered, out, base_path)
    used = set(re.findall(r'images/([^"/]+\.png)"', "".join(rendered.values())))
    unused = sorted(p.name for p in images.glob("*.png") if p.name not in used)
    if unused:
        print(f"note: {len(unused)} screenshot(s) no page shows: {', '.join(unused)}")
    if PROBLEMS:
        print(f"FAILED: {len(PROBLEMS)} problem(s)")
        for line in PROBLEMS:
            print(f"  {line}")
        return 1
    print(f"OK: {len(rendered)} pages, {len(used)} screenshots, written to {out}")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="\n\n".join(__doc__.split("\n\n")[1:]))
    parser.add_argument("--out", type=Path, default=REPO / "_site",
                        help="the folder to write the site into, replacing it (default: _site/ at the repository root)")
    parser.add_argument("--base-path", default="/",
                        help="the path GitHub Pages serves the site under, with slashes at both ends, such as "
                             "/ai-sdlc-landing-zone/ for a project site; only 404.html uses it (default: /)")
    parser.add_argument("--serve", type=int, metavar="PORT",
                        help="after building, serve the site at http://127.0.0.1:PORT/ until Ctrl+C")
    args = parser.parse_args()
    if not (args.base_path.startswith("/") and args.base_path.endswith("/")):
        parser.error("--base-path must start and end with a slash, such as /ai-sdlc-landing-zone/")
    status = build(args.out.resolve(), args.base_path)
    if status or args.serve is None:
        return status
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(args.out.resolve()))
    with http.server.ThreadingHTTPServer(("127.0.0.1", args.serve), handler) as server:
        print(f"Serving at http://127.0.0.1:{args.serve}/ (Ctrl+C to stop)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

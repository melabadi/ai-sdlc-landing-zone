"""Check the built deck in Chromium. Requires the optional Playwright Python package and browser."""
from pathlib import Path
import re

from playwright.sync_api import expect, sync_playwright


def main():
    root = Path(__file__).resolve().parents[1] / "_site"
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(reduced_motion="reduce", viewport={"width": 1366, "height": 900})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto((root / "walkthrough" / "index.html").as_uri())
        frame = page.locator(".chapter:not([inert]) .build-frame:not([inert])")
        step_counter = frame.locator(".build-count")
        title = page.get_by_role("heading", level=1)
        for language in ("en", "fr"):
            expect(page.locator("html")).to_have_attribute("lang", language)
            expect(page.locator(".repo-qr")).to_have_accessible_name({"en": "Repository", "fr": "Dépôt"}[language])
            expect(page.locator(".chapter")).to_have_count(7)
            for phase_index, phase in enumerate(page.locator("#phase-nav button").all()):
                phase.click()
                phase_position = f"{phase_index + 1:02d} / 07"
                expect(page.locator("#position")).to_have_text(phase_position)
                expect(step_counter).to_have_text(re.compile(r"01 / 05$"))
                expect(frame).to_have_attribute("data-kind", "input")
                expect(title).to_have_count(1)
                expect(page.get_by_role("heading", level=2)).to_have_count(1)
                expect(frame.locator("h2")).not_to_be_empty()
                expect(page.locator(".handoff-gates:visible")).to_have_count(0)
                expect(page.locator(".technical-hook:visible")).to_have_count(0)
                expect(phase).to_be_focused()
                page.set_viewport_size({"width": 1280, "height": 720})
                check_qr(page)
                title_box = title.bounding_box()
                footer_box = page.locator(".slide-footer").bounding_box()
                assert footer_box["y"] + footer_box["height"] <= 720
                actions = set()
                for step_index in range(3):
                    page.locator("#next").click()
                    expect(page.locator("#position")).to_have_text(phase_position)
                    expect(step_counter).to_have_text(re.compile(rf"{step_index + 2:02d} / 05$"))
                    expect(frame).to_have_attribute("data-kind", "technology")
                    if phase_index < 2 and step_index == 0:
                        # Plan and Design start in the desktop app, not the CLI or a background workflow.
                        expect(frame).to_have_attribute("data-role", "app")
                        expect(frame.locator("h2")).to_contain_text("GitHub Copilot")
                    expect(frame.locator("h2")).not_to_be_empty()
                    expect(frame.locator(".build-action")).not_to_be_empty()
                    expect(frame.locator(".technical-hook")).not_to_be_empty()
                    expect(page.locator(".handoff-gates:visible")).to_have_count(0)
                    actions.add(frame.locator(".build-action").inner_text())
                    slide = frame.inner_text()
                    assert not re.search(r"#\d+|demo-v\d|SHA256SUMS|release-manifest\.json", slide)
                    assert "undefined" not in slide
                    assert title.bounding_box() == title_box
                    assert page.locator(".slide-footer").bounding_box() == footer_box
                    page.set_viewport_size({"width": 390, "height": 844})
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), slide
                    page.set_viewport_size({"width": 1280, "height": 720})
                assert len(actions) == 3, "Each tool must explain a distinct action"
                page.locator("#next").click()
                expect(page.locator("#position")).to_have_text(phase_position)
                expect(step_counter).to_have_text(re.compile(r"05 / 05$"))
                expect(frame).to_have_attribute("data-kind", "handoff")
                expect(frame.locator("h2")).to_contain_text("→")
                expect(frame.locator(".build-action")).not_to_be_empty()
                for gate in frame.locator(".handoff-copy p").all():
                    expect(gate).not_to_be_empty()
                expect(page.locator(".handoff-row:visible")).to_have_count(2)
            expect(page.locator("#next")).to_be_disabled()
            page.locator("#language").click()
            expect(page.locator("#next")).to_be_disabled()
        page.locator("#fullscreen").click()
        expect(page.locator("#fullscreen")).to_have_attribute("aria-pressed", "true")
        check_qr(page)
        page.locator("#fullscreen").click()
        expect(page.locator("#fullscreen")).to_have_attribute("aria-pressed", "false")
        page.set_viewport_size({"width": 390, "height": 844})
        check_qr(page)
        page.locator(".technology-sources summary").scroll_into_view_if_needed()
        check_qr(page)
        page.set_viewport_size({"width": 1280, "height": 720})
        page.clock.install()
        page.locator("#phase-nav button").first.click()
        page.locator("#speed").fill("3")
        page.locator("#autoplay").click()
        page.clock.run_for(3100)
        expect(page.locator("#position")).to_have_text("01 / 07")
        expect(step_counter).to_have_text(re.compile(r"02 / 05$"))
        page.locator("#speed").fill("20")
        page.clock.run_for(10000)
        expect(page.locator("#position")).to_have_text("01 / 07")
        expect(step_counter).to_have_text(re.compile(r"02 / 05$"))
        page.clock.run_for(10100)
        expect(page.locator("#position")).to_have_text("01 / 07")
        expect(step_counter).to_have_text(re.compile(r"03 / 05$"))
        page.locator("#next").click()
        expect(page.locator("#autoplay")).to_have_attribute("aria-pressed", "false")
        page.clock.run_for(30000)
        expect(page.locator("#position")).to_have_text("01 / 07")
        expect(step_counter).to_have_text(re.compile(r"04 / 05$"))
        page.locator("#language").click()
        expect(page.locator("#position")).to_have_text("01 / 07")
        expect(step_counter).to_have_text(re.compile(r"04 / 05$"))
        page.locator("#main").focus()
        page.keyboard.press("End")
        expect(page.locator("#next")).to_be_disabled()
        page.keyboard.press("Home")
        expect(page.locator("#previous")).to_be_disabled()
        page.locator("#phase-nav button").last.click()
        page.locator(".chapter:not([inert]) .build-stop").nth(3).click()
        page.locator("#speed").fill("3")
        page.locator("#autoplay").click()
        page.clock.run_for(3100)
        expect(page.locator("#next")).to_be_disabled()
        expect(page.locator("#autoplay")).to_have_attribute("aria-pressed", "false")
        # Inspect effects synchronously at navigation time, not after an arbitrary sleep.
        inspect_motion = """() => {
          document.getElementById('next').click();
          return document.getElementById('slide').getAnimations({subtree:true})
            .map(a => a.effect.target.className);
        }"""
        page.keyboard.press("Home")
        assert page.evaluate(inspect_motion) == []
        page.emulate_media(reduced_motion="no-preference")
        assert set(page.evaluate(inspect_motion)) == {"build-frame"}
        page.locator(".chapter:not([inert]) .build-stop").last.click()
        assert set(page.evaluate(inspect_motion)) == {"chapter"}
        expect(frame).to_have_attribute("data-kind", "input")
        page.keyboard.press("ArrowLeft")
        expect(frame).to_have_attribute("data-kind", "handoff")
        page.evaluate("() => { for (let i=0; i<4; i++) document.getElementById('next').click(); }")
        page.clock.run_for(600)
        expect(page.locator("#position")).to_have_text("02 / 07")
        expect(page.get_by_role("heading", level=2)).to_have_count(1)
        expect(page.locator(".build-frame:visible")).to_have_count(1)
        assert not errors, errors
        browser.close()


def check_qr(page):
    """The actual symbol, not a toggle, is visible and clickable at the viewport corner."""
    link = page.locator(".repo-qr")
    expect(link).to_have_attribute("href", page.locator(".repo-link").get_attribute("href"))
    code = link.locator("svg")
    expect(code).to_be_in_viewport(ratio=1)
    box = code.bounding_box()
    width, height = page.evaluate("[document.documentElement.clientWidth, innerHeight]")
    assert box["width"] == box["height"] and box["width"] >= 82, box
    assert 0 <= width - box["x"] - box["width"] <= 24, box
    assert 0 <= height - box["y"] - box["height"] <= 48, box
    assert code.evaluate("""svg => {
      const r = svg.getBoundingClientRect();
      return svg.contains(document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2));
    }""")


if __name__ == "__main__":
    main()

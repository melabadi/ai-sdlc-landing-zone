"""Site integration checks: python -m unittest discover -s site -p "test_*.py"."""
import re
import unittest
from urllib.parse import urlsplit

import build
import qr


class WalkthroughBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build.PROBLEMS.clear()
        config, pages = build.load()
        cls.rendered = build.render(config, pages, "/ai-sdlc-landing-zone/")

    def test_slideshow_is_linked_from_every_guide_page(self):
        for path, document in self.rendered.items():
            if path != "walkthrough/index.html":
                with self.subTest(page=path):
                    self.assertRegex(document, r'href="[^"]*walkthrough/">Slideshow</a>')

    def test_walkthrough_assets_and_inline_icons_resolve(self):
        document = self.rendered["walkthrough/index.html"]
        symbols = set(re.findall(r'<symbol id="([^"]+)"', document))
        uses = set(re.findall(r'<use href="#([^"]+)"', document))
        self.assertTrue(uses)
        self.assertLessEqual(uses, symbols)
        for asset in re.findall(r'(?:href|src)="\.\./assets/([^"]+)"', document):
            asset = urlsplit(asset).path
            with self.subTest(asset=asset):
                self.assertTrue((build.SITE / "assets" / asset).is_file())
        self.assertEqual([], build.PROBLEMS)

    def test_qr_code_encodes_the_configured_repository(self):
        document = self.rendered["walkthrough/index.html"]
        repository = f"https://github.com/{build.load()[0]['repository']}"
        self.assertIn(qr.to_svg(qr.encode(repository)), document)
        self.assertIn(f'<a href="{repository}">{repository.removeprefix("https://")}</a>', document)

    def test_project_site_paths_remain_relative(self):
        document = self.rendered["walkthrough/index.html"]
        self.assertIn('href="../"', document)
        self.assertNotRegex(document, r'(?:href|src)="/assets/')
        self.assertNotIn("${", document)


if __name__ == "__main__":
    unittest.main()

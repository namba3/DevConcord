from __future__ import annotations

import unittest
from html.parser import HTMLParser
from pathlib import Path


FIXTURE = (
    Path(__file__).resolve().parent
    / "integration"
    / "fixtures"
    / "ui-design-drift"
)


class MockupStructure(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.panels: set[str] = set()
        self.controls: set[str] = set()
        self.resources: list[str] = []
        self.has_svg = False
        self.has_live_region = False
        self.has_alert = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "svg":
            self.has_svg = True
        if attributes.get("data-state-panel"):
            self.panels.add(attributes["data-state-panel"] or "")
        if attributes.get("data-state-switch"):
            self.controls.add(attributes["data-state-switch"] or "")
        if tag in {"script", "link"}:
            resource = attributes.get("src") or attributes.get("href")
            if resource:
                self.resources.append(resource)
        if attributes.get("aria-live"):
            self.has_live_region = True
        if attributes.get("role") == "alert":
            self.has_alert = True


class UIDesignDriftFixtureTests(unittest.TestCase):
    def test_mockup_has_all_baseline_states_and_accessible_state_feedback(self) -> None:
        html = (FIXTURE / "mockup.html").read_text(encoding="utf-8")
        parser = MockupStructure()
        parser.feed(html)

        expected = {"idle", "loading", "error", "success"}
        self.assertEqual(parser.panels, expected)
        self.assertEqual(parser.controls, expected)
        self.assertTrue(parser.has_svg)
        self.assertTrue(parser.has_live_region)
        self.assertTrue(parser.has_alert)
        self.assertIn('aria-pressed="true"', html)
        self.assertIn("preview presentation", html)

    def test_mockup_resources_are_local_and_fixture_is_self_contained(self) -> None:
        html = (FIXTURE / "mockup.html").read_text(encoding="utf-8")
        parser = MockupStructure()
        parser.feed(html)

        for resource in parser.resources:
            self.assertFalse(resource.startswith(("http:", "https:", "//")))
            self.assertTrue((FIXTURE / resource).is_file())
        self.assertIn("@media (max-width: 40rem)", (FIXTURE / "mockup.css").read_text(encoding="utf-8"))
        self.assertIn(":focus-visible", (FIXTURE / "mockup.css").read_text(encoding="utf-8"))
        self.assertIn("do not implement archive transfer", (FIXTURE / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

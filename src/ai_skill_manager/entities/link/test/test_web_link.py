"""Tests for WebLink.

Тесты веб-ссылки.
"""

import unittest

from ai_skill_manager.entities.link import WebLink
from ai_skill_manager.entities.link.link_data import LinkData


class TestWebLink(unittest.TestCase):
    def _data(self, **overrides):
        defaults = dict(
            raw="[text](https://example.com)",
            text="text",
            format="markdown",
            start=0,
            end=1,
            raw_path="https://example.com",
            header=None,
            is_image=False,
        )
        defaults.update(overrides)
        return LinkData(**defaults)

    def test_simple_web_link(self):
        # EN: A plain Markdown web link must store the URL and not be an image.
        # RU: Обычная markdown веб-ссылка должна сохранять URL и не быть
        # изображением.
        link = WebLink(data=self._data(), url="https://example.com")
        self.assertEqual(link.url, "https://example.com")
        self.assertFalse(link.is_image)
        self.assertIsNone(link.header)

    def test_web_link_with_fragment(self):
        # EN: A web link with a URL fragment must keep the fragment in header.
        # RU: Веб-ссылка с фрагментом URL должна сохранять фрагмент в header.
        link = WebLink(data=self._data(header="#section"), url="https://example.com")
        self.assertEqual(link.url, "https://example.com")
        self.assertEqual(link.header, "#section")

    def test_image_web_link(self):
        # EN: An image web link must set is_image=True.
        # RU: Веб-ссылка на изображение должна иметь is_image=True.
        link = WebLink(
            data=self._data(
                raw="![alt](https://example.com/img.png)",
                text="alt",
                raw_path="https://example.com/img.png",
                is_image=True,
            ),
            url="https://example.com/img.png",
        )
        self.assertTrue(link.is_image)

    def test_wiki_format_web_link(self):
        # EN: A web link written in wiki format must preserve the wiki format.
        # RU: Веб-ссылка в формате wiki должна сохранять формат wiki.
        link = WebLink(
            data=self._data(raw="[[https://example.com|text]]", format="wikilink"),
            url="https://example.com",
        )
        self.assertEqual(link.format, "wikilink")

    def test_link_type_property(self):
        # EN: WebLink.link_type must return the WebLink class.
        # RU: WebLink.link_type должен возвращать класс WebLink.
        link = WebLink(data=self._data(), url="https://example.com")
        self.assertIs(link.link_type, WebLink)


if __name__ == "__main__":
    unittest.main()

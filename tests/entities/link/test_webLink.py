"""Tests for WebLink.

Тесты веб-ссылки.
"""

import unittest

from ai_skill_manager.entities.link import WebLink


class TestWebLink(unittest.TestCase):
    def test_simple_web_link(self):
        # EN: A plain Markdown web link must store the URL and not be an image.
        # RU: Обычная markdown веб-ссылка должна сохранять URL и не быть
        # изображением.
        link = WebLink(
            raw="[text](https://example.com)",
            text="text",
            path="https://example.com",
            format="markdown",
            start=0,
            end=1,
        )
        self.assertEqual(link.path, "https://example.com")
        self.assertEqual(link.target, "https://example.com")
        self.assertFalse(link.is_image)
        self.assertIsNone(link.header)

    def test_web_link_with_fragment(self):
        # EN: A web link with a URL fragment must keep the fragment in header.
        # RU: Веб-ссылка с фрагментом URL должна сохранять фрагмент в header.
        link = WebLink(
            raw="[text](https://example.com#section)",
            text="text",
            path="https://example.com",
            format="markdown",
            start=0,
            end=1,
            header_value="#section",
        )
        self.assertEqual(link.path, "https://example.com")
        self.assertEqual(link.header, "#section")

    def test_image_web_link(self):
        # EN: An image web link must set is_image=True.
        # RU: Веб-ссылка на изображение должна иметь is_image=True.
        link = WebLink(
            raw="![alt](https://example.com/img.png)",
            text="alt",
            path="https://example.com/img.png",
            format="markdown",
            start=0,
            end=1,
            is_image_value=True,
        )
        self.assertTrue(link.is_image)

    def test_wiki_format_web_link(self):
        # EN: A web link written in wiki format must preserve the wiki format.
        # RU: Веб-ссылка в формате wiki должна сохранять формат wiki.
        link = WebLink(
            raw="[[https://example.com|text]]",
            text="text",
            path="https://example.com",
            format="wiki",
            start=0,
            end=1,
        )
        self.assertEqual(link.format, "wiki")
        self.assertEqual(link.target, "https://example.com")

    def test_link_type_property(self):
        # EN: WebLink.link_type must return the WebLink class.
        # RU: WebLink.link_type должен возвращать класс WebLink.
        link = WebLink(
            raw="[text](https://example.com)",
            text="text",
            path="https://example.com",
            format="markdown",
            start=0,
            end=1,
        )
        self.assertIs(link.link_type, WebLink)


if __name__ == "__main__":
    unittest.main()

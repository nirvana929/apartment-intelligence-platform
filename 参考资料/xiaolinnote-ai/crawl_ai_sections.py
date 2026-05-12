#!/usr/bin/env python3
import hashlib
import html
import re
import sys
import time
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests


ROOT = Path(__file__).resolve().parent
SITEMAP = "https://xiaolinnote.com/sitemap.xml"
SECTIONS = {
    "01-agent": "/ai/agent/",
    "02-rag": "/ai/rag/",
    "03-tools": "/ai/tools/",
}


class MarkdownContentParser(HTMLParser):
    def __init__(self, page_url: str):
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.in_content = False
        self.content_depth = 0
        self.skip_depth = 0
        self.parts = []
        self.link_stack = []
        self.in_code = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if not self.in_content:
            if tag == "div" and attrs.get("id") == "markdown-content":
                self.in_content = True
                self.content_depth = 1
            return
        if self.skip_depth:
            self.skip_depth += 1
            return
        if tag == "div":
            self.content_depth += 1
        if tag in {"script", "style", "svg"}:
            self.skip_depth = 1
            return
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._break(2)
            self.parts.append("#" * int(tag[1]) + " ")
        elif tag == "p":
            self._break(2)
        elif tag == "br":
            self.parts.append("\n")
        elif tag == "li":
            self._break(1)
            self.parts.append("- ")
        elif tag == "strong":
            self.parts.append("**")
        elif tag == "em":
            self.parts.append("*")
        elif tag == "pre":
            self._break(2)
            self.parts.append("```\n")
            self.in_code = True
        elif tag == "code" and not self.in_code:
            self.parts.append("`")
        elif tag == "a":
            class_name = attrs.get("class", "")
            self.link_stack.append(None if "header-anchor" in class_name else attrs.get("href", ""))
        elif tag == "img":
            src = attrs.get("src", "")
            alt = attrs.get("alt", "")
            if src:
                self._break(1)
                self.parts.append(f"![{alt}]({urljoin(self.page_url, src)})")
                self._break(1)

    def handle_endtag(self, tag):
        if not self.in_content:
            return
        if self.skip_depth:
            self.skip_depth -= 1
            return
        if tag == "div":
            self.content_depth -= 1
            if self.content_depth == 0:
                self.in_content = False
            return
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6", "p"}:
            self._break(2)
        elif tag == "li":
            self._break(1)
        elif tag == "strong":
            self.parts.append("**")
        elif tag == "em":
            self.parts.append("*")
        elif tag == "pre":
            self.parts.append("\n```\n")
            self.in_code = False
        elif tag == "code" and not self.in_code:
            self.parts.append("`")
        elif tag == "a" and self.link_stack:
            href = self.link_stack.pop()
            if href:
                self.parts.append(f"({urljoin(self.page_url, href)})")

    def handle_data(self, data):
        if self.in_content and not self.skip_depth:
            self.parts.append(data if self.in_code else re.sub(r"\s+", " ", data))

    def markdown(self):
        text = "".join(self.parts)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"

    def _break(self, minimum):
        current = "".join(self.parts[-3:])
        existing = len(current) - len(current.rstrip("\n"))
        if existing < minimum:
            self.parts.append("\n" * (minimum - existing))


def filename_for(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    return Path(path).name or "index.html"


def title_from(html_text: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html_text, re.S | re.I)
    if not match:
        return ""
    title = html.unescape(re.sub(r"\s+", " ", match.group(1))).strip()
    return title.replace(" | 小林面试笔记", "")


def section_sort_key(url: str):
    name = filename_for(url)
    if name == "index.html":
        return (0, 0, name)
    if name.endswith("_info.html"):
        return (1, 0, name)
    match = re.match(r"(\d+)", name)
    return (2, int(match.group(1)) if match else 999, name)


def fetch_urls(session: requests.Session):
    response = session.get(SITEMAP, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"
    xml_root = ET.fromstring(response.text)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [node.text for node in xml_root.findall(".//sm:loc", ns) if node.text]
    grouped = {}
    for section, prefix in SECTIONS.items():
        grouped[section] = sorted(
            [url for url in urls if urlparse(url).path.startswith(prefix)],
            key=section_sort_key,
        )
    return grouped


def download_images(session: requests.Session, section_dir: Path, md_paths):
    asset_dir = section_dir / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    urls = set()
    for path in md_paths:
        urls.update(re.findall(r"!\[[^\]]*\]\((https?://[^)]+)\)", path.read_text(encoding="utf-8")))
    replacements = {}
    failed = []
    for i, image_url in enumerate(sorted(urls), 1):
        suffix = Path(urlparse(image_url).path).suffix or ".png"
        asset_name = f"{hashlib.sha1(image_url.encode('utf-8')).hexdigest()[:12]}{suffix}"
        asset_path = asset_dir / asset_name
        if not asset_path.exists():
            try:
                with session.get(image_url, timeout=(8, 15), stream=True) as response:
                    response.raise_for_status()
                    with asset_path.open("wb") as file:
                        for chunk in response.iter_content(chunk_size=1024 * 128):
                            if chunk:
                                file.write(chunk)
            except Exception as exc:
                failed.append(f"- {image_url} ({exc})")
                continue
        replacements[image_url] = f"../assets/{asset_name}"
        print(f"  image {i}/{len(urls)}")
    for path in md_paths:
        text = path.read_text(encoding="utf-8")
        for original, local in replacements.items():
            text = text.replace(original, local)
        path.write_text(text, encoding="utf-8")
    if failed:
        (section_dir / "FAILED_IMAGES.md").write_text("# Failed image downloads\n\n" + "\n".join(failed) + "\n", encoding="utf-8")


def crawl_section(session: requests.Session, section: str, urls):
    section_dir = ROOT / section
    html_dir = section_dir / "html"
    md_dir = section_dir / "md"
    html_dir.mkdir(parents=True, exist_ok=True)
    md_dir.mkdir(parents=True, exist_ok=True)
    index_lines = [f"# {section}", ""]
    combined = []
    md_paths = []
    for i, url in enumerate(urls, 1):
        response = session.get(url, timeout=30)
        response.raise_for_status()
        response.encoding = "utf-8"
        html_text = response.text
        name = filename_for(url)
        (html_dir / name).write_text(html_text, encoding="utf-8")
        parser = MarkdownContentParser(url)
        parser.feed(html_text)
        title = title_from(html_text) or name
        md_name = Path(name).with_suffix(".md").name
        md_path = md_dir / md_name
        body = parser.markdown()
        md_path.write_text(f"<!-- source: {url} -->\n\n{body}", encoding="utf-8")
        md_paths.append(md_path)
        index_lines.append(f"{i}. [{title}](md/{md_name}) - {url}")
        combined.append(f"\n\n---\n\n# {title}\n\n来源：{url}\n\n{body}")
        print(f"{section}: page {i}/{len(urls)} {url}")
        time.sleep(0.3)
    (section_dir / "INDEX.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    (section_dir / "all_pages.md").write_text("".join(combined).strip() + "\n", encoding="utf-8")
    download_images(session, section_dir, md_paths)


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 compatible content archiver"})
    grouped = fetch_urls(session)
    requested = sys.argv[1:] or list(SECTIONS)
    unknown = [section for section in requested if section not in SECTIONS]
    if unknown:
        raise SystemExit(f"Unknown section(s): {', '.join(unknown)}")
    for section in requested:
        urls = grouped[section]
        crawl_section(session, section, urls)


if __name__ == "__main__":
    main()

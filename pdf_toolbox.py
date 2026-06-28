"""Browser-based PDF toolbox and web file downloader."""

from __future__ import annotations

from html import escape
from email.parser import BytesParser
from email.policy import default as email_policy
from html.parser import HTMLParser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Any, NamedTuple
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import Request, urlopen
from zipfile import ZIP_DEFLATED, ZipFile
import re
import threading
import webbrowser

if TYPE_CHECKING:
    from pypdf import PdfReader, PdfWriter


class DownloadFileType(NamedTuple):
    """Display label and extensions for one selectable download type."""

    label: str
    extensions: tuple[str, ...]


DOWNLOAD_FILE_TYPES: dict[str, DownloadFileType] = {
    "pdf": DownloadFileType("PDF", (".pdf",)),
    "word": DownloadFileType("Word", (".doc", ".docx")),
    "excel": DownloadFileType("Excel", (".xls", ".xlsx", ".csv")),
    "powerpoint": DownloadFileType("PowerPoint", (".ppt", ".pptx")),
    "text": DownloadFileType("テキスト", (".txt",)),
    "image": DownloadFileType("画像", (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg")),
    "archive": DownloadFileType("圧縮ファイル", (".zip", ".rar", ".7z", ".tar", ".gz")),
    "audio": DownloadFileType("音声", (".mp3", ".wav")),
    "video": DownloadFileType("動画", (".mp4", ".mov", ".avi", ".wmv")),
    "installer": DownloadFileType("インストーラー", (".exe", ".dmg", ".iso")),
}

FILE_LINK_EXTENSIONS = {
    extension
    for file_type in DOWNLOAD_FILE_TYPES.values()
    for extension in file_type.extensions
}


class FileLinkParser(HTMLParser):
    """Collect href/src values that point to downloadable files."""

    def __init__(self, base_url: str, allowed_extensions: set[str] | None = None) -> None:
        super().__init__()
        self.base_url = base_url
        self.allowed_extensions = allowed_extensions
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_names = ("href", "src") if tag in {"a", "source", "video", "audio", "img"} else ("href",)
        values = dict(attrs)
        for attr_name in attr_names:
            value = values.get(attr_name)
            if value and is_file_link(value, self.allowed_extensions):
                absolute_url = urljoin(self.base_url, value)
                if absolute_url not in self.links:
                    self.links.append(absolute_url)


def is_file_link(url: str, allowed_extensions: set[str] | None = None) -> bool:
    """Return True when a URL path has one of the allowed file extensions."""
    extensions = allowed_extensions if allowed_extensions is not None else FILE_LINK_EXTENSIONS
    path = urlparse(url).path.lower()
    return Path(path).suffix in extensions


def normalize_extensions(extensions: set[str]) -> set[str]:
    """Normalize user-selected extensions for case-insensitive matching."""
    return {extension.lower() if extension.startswith(".") else f".{extension.lower()}" for extension in extensions}


def extract_file_links(html: str, base_url: str, allowed_extensions: set[str] | None = None) -> list[str]:
    """Extract unique absolute file links from an HTML document."""
    normalized_extensions = normalize_extensions(allowed_extensions) if allowed_extensions is not None else None
    parser = FileLinkParser(base_url, normalized_extensions)
    parser.feed(html)
    return parser.links


def safe_download_name(url: str, used_names: set[str]) -> str:
    """Create a filesystem-safe unique filename from a URL."""
    parsed = urlparse(url)
    name = unquote(Path(parsed.path).name) or "download"
    name = re.sub(r'[^\w.()\- ]+', "_", name).strip(" .") or "download"
    stem = Path(name).stem or "download"
    suffix = Path(name).suffix
    candidate = name
    counter = 2
    while candidate in used_names:
        candidate = f"{stem}_{counter}{suffix}"
        counter += 1
    used_names.add(candidate)
    return candidate


def format_extensions_for_status(extensions: set[str]) -> str:
    """Format selected extensions for status messages."""
    return ", ".join(sorted(normalize_extensions(extensions)))


def download_file_links(page_url: str, output_dir: Path, allowed_extensions: set[str]) -> int:
    """Download direct file links matching allowed_extensions into output_dir."""
    request = Request(page_url, headers={"User-Agent": "PDF-Toolbox-Web-Downloader/1.0"})
    with urlopen(request, timeout=30) as response:  # noqa: S310 - user-provided web utility URL
        charset = response.headers.get_content_charset() or "utf-8"
        html = response.read().decode(charset, errors="replace")

    links = extract_file_links(html, page_url, allowed_extensions)
    used_names: set[str] = set()
    for link in links:
        target = output_dir / safe_download_name(link, used_names)
        file_request = Request(link, headers={"User-Agent": "PDF-Toolbox-Web-Downloader/1.0"})
        with urlopen(file_request, timeout=60) as response, target.open("wb") as output_file:  # noqa: S310
            output_file.write(response.read())
    return len(links)


def parse_page_ranges(range_text: str, page_count: int) -> list[tuple[int, int]]:
    """Parse one-based page ranges such as ``1-3,5,8-10``."""
    ranges: list[tuple[int, int]] = []
    for raw_part in range_text.split(","):
        part = raw_part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start = int(start_text.strip())
            end = int(end_text.strip())
        else:
            start = end = int(part)
        if start < 1 or end < start or end > page_count:
            raise ValueError(f"ページ範囲が不正です: {part}")
        ranges.append((start, end))
    if not ranges:
        raise ValueError("ページ範囲を入力してください。")
    return ranges


def write_pdf_to_bytes(writer: Any) -> BytesIO:
    """Serialize a pypdf writer to an in-memory byte stream."""
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output


def zip_directory(directory: Path) -> BytesIO:
    """Zip every file directly under directory and return the archive stream."""
    archive = BytesIO()
    with ZipFile(archive, "w", ZIP_DEFLATED) as zip_file:
        for path in sorted(directory.iterdir()):
            if path.is_file():
                zip_file.write(path, arcname=path.name)
    archive.seek(0)
    return archive


def build_download_type_checkboxes(selected_keys: set[str] | None = None) -> str:
    """Build checkbox HTML for selectable download file types."""
    selected_keys = selected_keys or {"pdf", "word"}
    checkboxes = []
    for type_key, file_type in DOWNLOAD_FILE_TYPES.items():
        checked = " checked" if type_key in selected_keys else ""
        label = f"{file_type.label} ({', '.join(file_type.extensions)})"
        checkboxes.append(
            f'<label class="checkbox"><input type="checkbox" name="file_types" value="{type_key}"{checked}> '
            f"{escape(label)}</label>"
        )
    return "\n".join(checkboxes)


def render_page(message: str = "") -> str:
    """Render the browser UI."""
    safe_message = f'<p class="message">{escape(message)}</p>' if message else ""
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PDF Toolbox Web</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 0; background: #f6f8fb; color: #1f2937; }}
    main {{ max-width: 980px; margin: 0 auto; padding: 28px; }}
    section {{ background: white; border: 1px solid #d7dde8; border-radius: 12px; padding: 20px; margin: 18px 0; }}
    h1, h2 {{ margin-top: 0; }}
    label {{ display: block; margin: 10px 0 6px; font-weight: 600; }}
    input[type="text"], input[type="url"] {{ width: 100%; box-sizing: border-box; padding: 10px; }}
    input[type="file"] {{ margin: 8px 0; }}
    button {{ padding: 10px 16px; border: 0; border-radius: 8px; background: #2563eb; color: white; font-weight: 700; cursor: pointer; }}
    .checkbox-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 8px; margin: 10px 0; }}
    .checkbox {{ font-weight: 500; margin: 0; }}
    .message {{ border-left: 4px solid #2563eb; background: #eff6ff; padding: 10px 12px; }}
    .hint {{ color: #4b5563; font-size: 0.95rem; }}
  </style>
</head>
<body>
<main>
  <h1>PDF Toolbox Web</h1>
  <p class="hint">ブラウザ上で PDF の統合・分割と Web ファイル保存を実行できます。</p>
  {safe_message}

  <section>
    <h2>PDF 統合</h2>
    <form action="/merge" method="post" enctype="multipart/form-data">
      <label>統合する PDF（複数選択可）</label>
      <input type="file" name="pdfs" accept="application/pdf,.pdf" multiple required>
      <button type="submit">統合 PDF をダウンロード</button>
    </form>
  </section>

  <section>
    <h2>PDF 分割</h2>
    <form action="/split" method="post" enctype="multipart/form-data">
      <label>分割する PDF</label>
      <input type="file" name="pdf" accept="application/pdf,.pdf" required>
      <label><input type="radio" name="split_mode" value="pages" checked> 1ページずつ分割</label>
      <label><input type="radio" name="split_mode" value="ranges"> ページ範囲で分割</label>
      <label>範囲（例: 1-3,5,8-10）</label>
      <input type="text" name="range_text" value="1-3,5">
      <button type="submit">分割 PDF ZIP をダウンロード</button>
    </form>
  </section>

  <section>
    <h2>Web ファイル保存</h2>
    <form action="/download" method="post">
      <label>ファイルリンクがある Web ページ URL</label>
      <input type="url" name="page_url" placeholder="https://example.com/page.html" required>
      <label>ダウンロードするファイル形式（複数選択可）</label>
      <div class="checkbox-grid">{build_download_type_checkboxes()}</div>
      <button type="submit">選択した形式のファイル ZIP をダウンロード</button>
    </form>
  </section>
</main>
</body>
</html>"""


def parse_multipart_form(content_type: str, body: bytes) -> tuple[dict[str, list[str]], dict[str, list[tuple[str, bytes]]]]:
    """Parse a multipart/form-data request body into fields and uploaded files."""
    message = BytesParser(policy=email_policy).parsebytes(
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode() + body
    )
    fields: dict[str, list[str]] = {}
    files: dict[str, list[tuple[str, bytes]]] = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if not name:
            continue
        filename = part.get_filename()
        payload = part.get_payload(decode=True) or b""
        if filename is None:
            fields.setdefault(name, []).append(payload.decode(part.get_content_charset() or "utf-8", errors="replace"))
        else:
            files.setdefault(name, []).append((filename, payload))
    return fields, files


def parse_urlencoded_form(body: bytes) -> dict[str, list[str]]:
    """Parse an application/x-www-form-urlencoded request body."""
    from urllib.parse import parse_qs

    return parse_qs(body.decode("utf-8", errors="replace"), keep_blank_values=True)


class PdfToolboxRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the browser-based toolbox."""

    server_version = "PDFToolboxWeb/1.0"

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path in {"/", ""}:
            self.send_html(render_page())
            return
        self.send_error(HTTPStatus.NOT_FOUND, "ページが見つかりません。")

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        try:
            if self.path == "/merge":
                self.handle_merge()
            elif self.path == "/split":
                self.handle_split()
            elif self.path == "/download":
                self.handle_download()
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "ページが見つかりません。")
        except Exception as error:  # noqa: BLE001 - show actionable browser error
            self.send_html(render_page(f"処理に失敗しました: {error}"), HTTPStatus.INTERNAL_SERVER_ERROR)

    def read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        return self.rfile.read(length)

    def read_multipart(self) -> tuple[dict[str, list[str]], dict[str, list[tuple[str, bytes]]]]:
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            raise ValueError("フォーム形式が不正です。")
        return parse_multipart_form(content_type, self.read_body())

    def handle_merge(self) -> None:
        from pypdf import PdfReader, PdfWriter

        _fields, files = self.read_multipart()
        uploads = files.get("pdfs", [])
        if len(uploads) < 2:
            self.send_html(render_page("PDF を2つ以上選択してください。"), HTTPStatus.BAD_REQUEST)
            return

        writer = PdfWriter()
        for _filename, payload in uploads:
            reader = PdfReader(BytesIO(payload))
            for page in reader.pages:
                writer.add_page(page)
        self.send_bytes(write_pdf_to_bytes(writer).getvalue(), "merged.pdf", "application/pdf")

    def handle_split(self) -> None:
        from pypdf import PdfReader, PdfWriter

        fields, files = self.read_multipart()
        uploads = files.get("pdf", [])
        if not uploads:
            self.send_html(render_page("分割する PDF を選択してください。"), HTTPStatus.BAD_REQUEST)
            return

        filename, payload = uploads[0]
        reader = PdfReader(BytesIO(payload))
        stem = Path(filename or "split").stem or "split"
        mode = fields.get("split_mode", ["pages"])[0]

        archive = BytesIO()
        with ZipFile(archive, "w", ZIP_DEFLATED) as zip_file:
            if mode == "pages":
                ranges = [(index, index) for index in range(1, len(reader.pages) + 1)]
            else:
                ranges = parse_page_ranges(fields.get("range_text", [""])[0], len(reader.pages))
            for start, end in ranges:
                writer = PdfWriter()
                for page_index in range(start - 1, end):
                    writer.add_page(reader.pages[page_index])
                zip_file.writestr(f"{stem}_pages_{start}-{end}.pdf", write_pdf_to_bytes(writer).getvalue())
        archive.seek(0)
        self.send_bytes(archive.getvalue(), f"{stem}_split.zip", "application/zip")

    def handle_download(self) -> None:
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("application/x-www-form-urlencoded"):
            raise ValueError("フォーム形式が不正です。")
        fields = parse_urlencoded_form(self.read_body())
        page_url = fields.get("page_url", [""])[0].strip()
        selected_types = set(fields.get("file_types", []))
        selected_extensions = {
            extension
            for type_key in selected_types
            for extension in DOWNLOAD_FILE_TYPES.get(type_key, DownloadFileType("", ())).extensions
        }
        if not page_url:
            self.send_html(render_page("Web ページの URL を入力してください。"), HTTPStatus.BAD_REQUEST)
            return
        if not selected_extensions:
            self.send_html(render_page("ダウンロードするファイル形式を1つ以上選択してください。"), HTTPStatus.BAD_REQUEST)
            return

        with TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            downloaded = download_file_links(page_url, output_dir, selected_extensions)
            if downloaded == 0:
                selected_text = format_extensions_for_status(selected_extensions)
                self.send_html(render_page(f"対象ファイルが見つかりませんでした（{selected_text}）。"), HTTPStatus.NOT_FOUND)
                return
            archive = zip_directory(output_dir)
        self.send_bytes(archive.getvalue(), "web_files.zip", "application/zip")

    def send_html(self, html: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_bytes(self, data: bytes, filename: str, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: Any) -> None:
        """Keep terminal output focused on the startup URL."""


def main() -> None:
    """Start the local web application and open it in the default browser."""
    host = "127.0.0.1"
    port = 5000
    url = f"http://{host}:{port}"
    server = ThreadingHTTPServer((host, port), PdfToolboxRequestHandler)
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    print(f"PDF Toolbox Web を起動しました: {url}")
    server.serve_forever()


if __name__ == "__main__":
    main()

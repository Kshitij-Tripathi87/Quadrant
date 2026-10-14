import os
from pathlib import Path
from typing import List
import httpx
from bs4 import BeautifulSoup
from langchain_core.documents import Document

class DocumentLoader:
    """
    Handles loading technical documentation from local files (.md, .txt, .html)
    or remote URLs.
    """

    @staticmethod
    def load_file(file_path: str | Path) -> Document:
        """Load content from a local file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        suffix = path.suffix.lower()
        if suffix in [".md", ".markdown", ".txt", ".html", ".htm"]:
            text = path.read_text(encoding="utf-8", errors="replace")
            first_line = text.strip().split("\n")[0] if text else ""
            title = first_line.lstrip("#").strip() if first_line.startswith("#") else path.stem
            return Document(
                page_content=text,
                metadata={
                    "source": str(path.resolve()),
                    "title": title or path.name,
                    "filename": path.name,
                    "source_type": "file",
                },
            )
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    @staticmethod
    async def load_url(url: str) -> Document:
        """Fetch and extract text content from a remote URL."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TechnicalDocsBot/1.0"
        }
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove navigation, footer, scripts, stylesheets
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else url

        main_content = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", {"role": "main"})
            or soup.body
        )

        content = main_content.get_text(separator="\n\n", strip=True) if main_content else ""

        return Document(
            page_content=content,
            metadata={
                "source": url,
                "title": title,
                "filename": url.split("/")[-1] or "webpage",
                "source_type": "url",
            },
        )

    @staticmethod
    def load_directory(directory_path: str | Path) -> List[Document]:
        """Load all markdown and text files from a directory."""
        dir_path = Path(directory_path)
        if not dir_path.exists():
            return []

        docs = []
        for file_path in dir_path.glob("**/*"):
            if file_path.is_file() and file_path.suffix.lower() in [".md", ".markdown", ".txt"]:
                try:
                    docs.append(DocumentLoader.load_file(file_path))
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
        return docs

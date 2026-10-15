import hashlib
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from src.config import settings

router = APIRouter(tags=["Downloads"])

# Resolve repository paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
DIST_DIR = ROOT_DIR / "dist"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

EXE_PATH = DIST_DIR / "DocuGraphAI_Setup.exe"
MSI_PATH = DIST_DIR / "DocuGraphAI_Setup.msi"
ZIP_PATH = DIST_DIR / "DocuGraphAI_bundle.zip"
BAT_PATH = ROOT_DIR / "Install_DocuGraphAI.bat"

_HASH_CACHE: Dict[str, str] = {}

def get_file_sha256(path: Path) -> str:
    """Computes and caches the SHA256 checksum of a file."""
    if not path.exists():
        return ""
    str_path = str(path)
    if str_path in _HASH_CACHE:
        return _HASH_CACHE[str_path]
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
    digest = hasher.hexdigest().upper()
    _HASH_CACHE[str_path] = digest
    return digest

@router.get(
    "/download",
    include_in_schema=False,
    summary="Download portal landing page",
)
async def serve_download_portal():
    download_html = STATIC_DIR / "download.html"
    if download_html.exists():
        return FileResponse(download_html)
    return {"message": "Download portal is available. Visit /download/exe or /download/msi directly."}

@router.get(
    "/download/exe",
    summary="Download Windows Setup Wizard (.exe)",
    description="Downloads the standalone Windows Setup Wizard executable for DocuGraph AI.",
)
async def download_exe():
    if not EXE_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Windows Setup executable (.exe) is currently not available on this server.",
        )
    return FileResponse(
        path=str(EXE_PATH),
        filename="DocuGraphAI_Setup.exe",
        media_type="application/vnd.microsoft.portable-executable",
        headers={
            "Content-Disposition": 'attachment; filename="DocuGraphAI_Setup.exe"',
            "Cache-Control": "public, max-age=3600",
        },
    )

@router.get(
    "/download/msi",
    summary="Download Windows Installer Package (.msi)",
    description="Downloads the standard Windows Installer MSI package for DocuGraph AI.",
)
async def download_msi():
    if not MSI_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Windows Installer package (.msi) is currently not available on this server.",
        )
    return FileResponse(
        path=str(MSI_PATH),
        filename="DocuGraphAI_Setup.msi",
        media_type="application/x-msi",
        headers={
            "Content-Disposition": 'attachment; filename="DocuGraphAI_Setup.msi"',
            "Cache-Control": "public, max-age=3600",
        },
    )

@router.get(
    "/download/zip",
    summary="Download Portable Application Archive (.zip)",
    description="Downloads the portable zip package of DocuGraph AI (no installation required).",
)
async def download_zip():
    if not ZIP_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portable zip archive is currently not available on this server.",
        )
    return FileResponse(
        path=str(ZIP_PATH),
        filename="DocuGraphAI_bundle.zip",
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="DocuGraphAI_bundle.zip"',
            "Cache-Control": "public, max-age=3600",
        },
    )

@router.get(
    "/download/script",
    summary="Download 1-Click Quick Batch Installer (.bat)",
)
async def download_script():
    if not BAT_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Install script is not available.",
        )
    return FileResponse(
        path=str(BAT_PATH),
        filename="Install_DocuGraphAI.bat",
        media_type="application/x-bat",
        headers={
            "Content-Disposition": 'attachment; filename="Install_DocuGraphAI.bat"',
        },
    )

@router.get(
    "/api/v1/download/info",
    summary="Get installer file metadata and SHA256 checksums",
)
async def get_download_info() -> Dict[str, Any]:
    def file_info(path: Path, url: str, name: str, is_recommended: bool = False):
        if not path.exists():
            return None
        size_bytes = path.stat().st_size
        size_mb = round(size_bytes / (1024 * 1024), 1)
        return {
            "name": name,
            "filename": path.name,
            "size_bytes": size_bytes,
            "size_mb": size_mb,
            "sha256": get_file_sha256(path),
            "download_url": url,
            "recommended": is_recommended,
            "available": True,
        }

    return {
        "app_name": "DocuGraph AI",
        "tagline": "Self-Corrective Technical Documentation Assistant",
        "version": "2.0.0",
        "release_date": "October 2026",
        "supported_os": "Windows 10 / Windows 11 (64-bit)",
        "packages": {
            "exe": file_info(EXE_PATH, "/download/exe", "Windows Setup Wizard (.exe)", is_recommended=True),
            "msi": file_info(MSI_PATH, "/download/msi", "Windows Installer Package (.msi)", is_recommended=False),
            "zip": file_info(ZIP_PATH, "/download/zip", "Portable Application Archive (.zip)", is_recommended=False),
            "bat": file_info(BAT_PATH, "/download/script", "1-Click Batch Installer Script (.bat)", is_recommended=False),
        },
    }

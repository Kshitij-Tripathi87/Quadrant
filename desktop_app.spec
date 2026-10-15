# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys

block_cipher = None

BASE_DIR = Path(SPECPATH).resolve()

datas = [
    ('src/api/static', 'src/api/static'),
    ('data/raw_documents', 'data/raw_documents'),
    ('.env', '.'),
    ('app_icon.ico', '.'),
    ('app_icon.png', '.'),
]

hiddenimports = [
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.loops.asyncio',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.http.h11_impl',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'fastapi.staticfiles',
    'fastapi.middleware.cors',
    'pydantic',
    'pydantic_settings',
    'pydantic.deprecated.decorator',
    'webview',
    'webview.platforms.winforms',
    'clr_loader',
    'pythonnet',
    'sqlite3',
    'aiosqlite',
    'langgraph',
    'langgraph.graph',
    'langchain_core',
    'langchain_google_genai',
    'fastembed',
    'chromadb',
    'duckduckgo_search',
]

a = Analysis(
    ['desktop_app.py'],
    pathex=[str(BASE_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'sympy',
        'torch',
        'torchvision',
        'torchaudio',
        'transformers',
        'sentence_transformers',
        'IPython',
        'jupyter',
        'pytest',
        'pytest_asyncio',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DocuGraphAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # Windowed GUI application (no black cmd popup)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='DocuGraphAI',
)

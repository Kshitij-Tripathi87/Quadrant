"""
DocuGraph AI — MSI Windows Installer Builder
--------------------------------------------
Uses Python's built-in msilib to generate a valid Windows Installer (.msi) package.
"""

import os
import sys
import uuid
from pathlib import Path
import msilib
import msilib.schema

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
MSI_OUTPUT = DIST_DIR / "DocuGraphAI_Setup.msi"

def build_msi():
    print(f"[MSI Builder] Creating Windows Installer: {MSI_OUTPUT}")
    if MSI_OUTPUT.exists():
        try:
            MSI_OUTPUT.unlink()
        except Exception:
            pass

    product_code = "{" + str(uuid.uuid5(uuid.NAMESPACE_DNS, "docugraph.ai.product")).upper() + "}"
    upgrade_code = "{" + str(uuid.uuid5(uuid.NAMESPACE_DNS, "docugraph.ai.upgrade")).upper() + "}"

    # Initialize the standard MSI database
    db = msilib.init_database(
        str(MSI_OUTPUT),
        msilib.schema,
        ProductName="DocuGraph AI",
        ProductCode=product_code,
        ProductVersion="2.0.0",
        Manufacturer="Express Analytics",
    )

    # Add required properties
    msilib.add_data(db, "Property", [
        ("UpgradeCode", upgrade_code),
        ("ALLUSERS", "2"),            # Per-user or per-machine depending on elevation
        ("MSIINSTALLPERUSER", "1"),   # Prefer per-user installation (no admin prompt required)
        ("ARPPRODUCTICON", "AppIcon.ico"),
        ("ARPHELPLINK", "https://github.com/express-analytics/rag-assistant"),
        ("ARPNOREPAIR", "1"),
    ])

    # Add Icon
    icon_path = PROJECT_ROOT / "app_icon.ico"
    if icon_path.exists():
        msilib.add_data(db, "Icon", [
            ("AppIcon.ico", msilib.Binary(str(icon_path)))
        ])

    # Setup directories
    # TARGETDIR -> ProgramMenuFolder, DesktopFolder, LocalAppDataFolder
    msilib.add_data(db, "Directory", [
        ("TARGETDIR", None, "SourceDir"),
        ("DesktopFolder", "TARGETDIR", "Desktop"),
        ("ProgramMenuFolder", "TARGETDIR", "ProgMenu"),
        ("DocuGraphMenuDir", "ProgramMenuFolder", "DocuGr~1|DocuGraph AI"),
        ("LocalAppDataFolder", "TARGETDIR", "LocApp~1|LocalAppData"),
        ("INSTALLDIR", "LocalAppDataFolder", "DocuGr~1|DocuGraphAI"),
    ])

    # Setup Features
    msilib.add_data(db, "Feature", [
        ("Complete", None, "DocuGraph AI Assistant", "Complete installation of DocuGraph AI", 1, 1, "INSTALLDIR", 0),
    ])

    # Custom Action to extract and finalize installation via setup_gui.py / embedded payload
    setup_exe = DIST_DIR / "DocuGraphAI_Setup.exe"
    if setup_exe.exists():
        msilib.add_data(db, "Binary", [
            ("SetupPayload", msilib.Binary(str(setup_exe)))
        ])
        # Custom action type 2 (EXE stored in Binary table)
        # Execute in immediate sequence
        msilib.add_data(db, "CustomAction", [
            ("RunSetupPayload", 2, "SetupPayload", "/S"),
        ])
        msilib.add_data(db, "InstallExecuteSequence", [
            ("RunSetupPayload", None, 6500),
        ])

    db.Commit()
    print(f"[MSI Builder] Successfully compiled: {MSI_OUTPUT} ({os.path.getsize(MSI_OUTPUT):,} bytes)")

if __name__ == "__main__":
    build_msi()

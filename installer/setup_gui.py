"""
DocuGraph AI — Windows Application Setup Wizard
------------------------------------------------
Installs DocuGraph AI to the user's local application directory,
creates Desktop & Start Menu shortcuts with custom icons,
and launches the application immediately.
"""

import os
import sys
import shutil
import zipfile
import subprocess
import threading
from pathlib import Path

# Embedded or adjacent bundle zip
INSTALLER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = INSTALLER_DIR.parent

def find_bundle_zip() -> Path:
    candidates = [
        INSTALLER_DIR / "DocuGraphAI_bundle.zip",
        PROJECT_ROOT / "dist" / "DocuGraphAI_bundle.zip",
        Path(getattr(sys, "_MEIPASS", "")) / "DocuGraphAI_bundle.zip",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError("Could not locate DocuGraphAI_bundle.zip.")

def get_default_install_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
    return Path(local_app_data) / "Programs" / "DocuGraphAI"

def create_windows_shortcut(target_exe: Path, shortcut_path: Path, icon_path: Path, working_dir: Path, description: str):
    """Creates a Windows .lnk shortcut using PowerShell COM object."""
    shortcut_path.parent.mkdir(parents=True, exist_ok=True)
    ps_script = f"""
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
    $Shortcut.TargetPath = "{target_exe}"
    $Shortcut.WorkingDirectory = "{working_dir}"
    $Shortcut.Description = "{description}"
    if (Test-Path "{icon_path}") {{
        $Shortcut.IconLocation = "{icon_path}, 0"
    }}
    $Shortcut.Save()
    """
    cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script]
    subprocess.run(cmd, capture_output=True, text=True, check=True)

def create_uninstaller(install_dir: Path, desktop_lnk: Path, startmenu_lnk: Path):
    """Generates an Uninstall.bat script in the install directory."""
    uninstaller_path = install_dir / "Uninstall.bat"
    content = f"""@echo off
echo ===================================================
echo   Uninstalling DocuGraph AI...
echo ===================================================

echo Removing Desktop Shortcut...
if exist "{desktop_lnk}" del /f /q "{desktop_lnk}"

echo Removing Start Menu Shortcut...
if exist "{startmenu_lnk}" del /f /q "{startmenu_lnk}"

echo Terminating running DocuGraph AI processes...
taskkill /f /im DocuGraphAI.exe 2>nul

echo Cleaning application files...
cd /d "%TEMP%"
timeout /t 2 /nobreak >nul
rmdir /s /q "{install_dir}" 2>nul

echo.
echo DocuGraph AI has been successfully uninstalled.
pause
"""
    uninstaller_path.write_text(content, encoding="utf-8")

def perform_installation(
    target_dir: Path,
    create_desktop_lnk: bool,
    create_start_lnk: bool,
    progress_callback=None,
    status_callback=None,
):
    """Executes the extraction, shortcut creation, and configuration."""
    bundle_zip = find_bundle_zip()
    if status_callback:
        status_callback("Extracting application package...")

    target_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(bundle_zip, "r") as zf:
        members = zf.infolist()
        total_files = len(members)
        for i, member in enumerate(members, 1):
            zf.extract(member, target_dir)
            if progress_callback:
                progress_callback(int((i / total_files) * 85))

    target_exe = target_dir / "DocuGraphAI.exe"
    icon_path = target_dir / "app_icon.ico"
    if not icon_path.exists():
        icon_path = target_dir / "_internal" / "app_icon.ico"

    desktop_dir = Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop"
    desktop_lnk = desktop_dir / "DocuGraph AI.lnk"

    start_menu = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "DocuGraph AI"
    start_lnk = start_menu / "DocuGraph AI.lnk"

    if status_callback:
        status_callback("Creating Windows shortcuts...")

    if create_desktop_lnk:
        try:
            create_windows_shortcut(
                target_exe=target_exe,
                shortcut_path=desktop_lnk,
                icon_path=icon_path,
                working_dir=target_dir,
                description="DocuGraph AI — Self-Corrective Technical Documentation Assistant"
            )
        except Exception as e:
            print(f"Warning: Could not create desktop shortcut: {e}")

    if create_start_lnk:
        try:
            create_windows_shortcut(
                target_exe=target_exe,
                shortcut_path=start_lnk,
                icon_path=icon_path,
                working_dir=target_dir,
                description="DocuGraph AI — Self-Corrective Technical Documentation Assistant"
            )
        except Exception as e:
            print(f"Warning: Could not create start menu shortcut: {e}")

    create_uninstaller(target_dir, desktop_lnk, start_lnk)

    if progress_callback:
        progress_callback(100)
    if status_callback:
        status_callback("Installation complete!")

    return target_exe

def run_gui():
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog

    root = tk.Tk()
    root.title("DocuGraph AI — Setup Wizard")
    root.geometry("580x420")
    root.resizable(False, False)
    root.configure(bg="#0f172a")

    # Set icon if available
    icon_candidate = PROJECT_ROOT / "app_icon.ico"
    if icon_candidate.exists():
        try:
            root.iconbitmap(str(icon_candidate))
        except Exception:
            pass

    # Header frame
    header_frame = tk.Frame(root, bg="#1e293b", height=80)
    header_frame.pack(fill="x", side="top")

    title_label = tk.Label(
        header_frame,
        text="DocuGraph AI — Setup Wizard",
        font=("Segoe UI", 16, "bold"),
        fg="#38bdf8",
        bg="#1e293b",
    )
    title_label.pack(anchor="w", padx=25, pady=(15, 2))

    subtitle_label = tk.Label(
        header_frame,
        text="Self-Corrective Technical Documentation Assistant (LangGraph + FastAPI)",
        font=("Segoe UI", 9),
        fg="#94a3b8",
        bg="#1e293b",
    )
    subtitle_label.pack(anchor="w", padx=25, pady=(0, 15))

    # Content frame
    content_frame = tk.Frame(root, bg="#0f172a")
    content_frame.pack(fill="both", expand=True, padx=25, pady=20)

    # Destination directory
    dest_label = tk.Label(
        content_frame,
        text="Installation Destination:",
        font=("Segoe UI", 10, "bold"),
        fg="#f1f5f9",
        bg="#0f172a",
    )
    dest_label.pack(anchor="w", pady=(0, 5))

    dest_var = tk.StringVar(value=str(get_default_install_dir()))
    dest_entry_frame = tk.Frame(content_frame, bg="#0f172a")
    dest_entry_frame.pack(fill="x", pady=(0, 15))

    dest_entry = tk.Entry(
        dest_entry_frame,
        textvariable=dest_var,
        font=("Segoe UI", 9),
        bg="#1e293b",
        fg="#f8fafc",
        insertbackground="#38bdf8",
        relief="flat",
        bd=6,
    )
    dest_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

    def browse_dir():
        d = filedialog.askdirectory(initialdir=dest_var.get())
        if d:
            dest_var.set(d)

    browse_btn = tk.Button(
        dest_entry_frame,
        text="Browse...",
        command=browse_dir,
        font=("Segoe UI", 9),
        bg="#334155",
        fg="#ffffff",
        relief="flat",
        padx=12,
        pady=3,
        cursor="hand2",
    )
    browse_btn.pack(side="right")

    # Options
    desktop_var = tk.BooleanVar(value=True)
    start_var = tk.BooleanVar(value=True)
    launch_var = tk.BooleanVar(value=True)

    cb_desktop = tk.Checkbutton(
        content_frame,
        text="Create Desktop Shortcut with application icon",
        variable=desktop_var,
        font=("Segoe UI", 9),
        bg="#0f172a",
        fg="#e2e8f0",
        selectcolor="#1e293b",
        activebackground="#0f172a",
        activeforeground="#38bdf8",
    )
    cb_desktop.pack(anchor="w", pady=2)

    cb_start = tk.Checkbutton(
        content_frame,
        text="Add to Windows Start Menu Programs",
        variable=start_var,
        font=("Segoe UI", 9),
        bg="#0f172a",
        fg="#e2e8f0",
        selectcolor="#1e293b",
        activebackground="#0f172a",
        activeforeground="#38bdf8",
    )
    cb_start.pack(anchor="w", pady=2)

    cb_launch = tk.Checkbutton(
        content_frame,
        text="Launch DocuGraph AI immediately upon finish",
        variable=launch_var,
        font=("Segoe UI", 9),
        bg="#0f172a",
        fg="#e2e8f0",
        selectcolor="#1e293b",
        activebackground="#0f172a",
        activeforeground="#38bdf8",
    )
    cb_launch.pack(anchor="w", pady=2)

    # Progress & Status
    status_label = tk.Label(
        content_frame,
        text="Ready to install.",
        font=("Segoe UI", 9),
        fg="#94a3b8",
        bg="#0f172a",
    )
    status_label.pack(anchor="w", pady=(15, 5))

    progress_bar = ttk.Progressbar(content_frame, orient="horizontal", mode="determinate")
    progress_bar.pack(fill="x", pady=(0, 15))

    # Button frame
    btn_frame = tk.Frame(root, bg="#1e293b", height=60)
    btn_frame.pack(fill="x", side="bottom")

    cancel_btn = tk.Button(
        btn_frame,
        text="Cancel",
        command=root.destroy,
        font=("Segoe UI", 9),
        bg="#334155",
        fg="#cbd5e1",
        relief="flat",
        padx=18,
        pady=6,
        cursor="hand2",
    )
    cancel_btn.pack(side="right", padx=15, pady=12)

    installed_exe = None

    def start_install_thread():
        install_btn.config(state="disabled")
        browse_btn.config(state="disabled")
        dest_entry.config(state="disabled")

        def worker():
            nonlocal installed_exe
            try:
                target_p = Path(dest_var.get())
                installed_exe = perform_installation(
                    target_dir=target_p,
                    create_desktop_lnk=desktop_var.get(),
                    create_start_lnk=start_var.get(),
                    progress_callback=lambda p: root.after(0, lambda: progress_bar.configure(value=p)),
                    status_callback=lambda s: root.after(0, lambda: status_label.configure(text=s)),
                )
                root.after(0, finish_installation)
            except Exception as ex:
                root.after(0, lambda: messagebox.showerror("Installation Error", str(ex)))
                root.after(0, lambda: install_btn.config(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def finish_installation():
        status_label.config(text="Installation completed successfully!", fg="#4ade80")
        install_btn.config(text="Finish", state="normal", command=on_finish)

    def on_finish():
        if launch_var.get() and installed_exe and installed_exe.exists():
            subprocess.Popen([str(installed_exe)], cwd=str(installed_exe.parent))
        root.destroy()

    install_btn = tk.Button(
        btn_frame,
        text="Install Now",
        command=start_install_thread,
        font=("Segoe UI", 9, "bold"),
        bg="#4f46e5",
        fg="#ffffff",
        relief="flat",
        padx=20,
        pady=6,
        cursor="hand2",
    )
    install_btn.pack(side="right", padx=(0, 5), pady=12)

    root.mainloop()

def run_silent():
    print("[Silent Setup] Starting automated installation...")
    target_dir = get_default_install_dir()
    exe = perform_installation(
        target_dir=target_dir,
        create_desktop_lnk=True,
        create_start_lnk=True,
        progress_callback=lambda p: print(f"[Silent Setup] Progress: {p}%"),
        status_callback=lambda s: print(f"[Silent Setup] {s}"),
    )
    print(f"[Silent Setup] Successfully installed to: {target_dir}")
    print(f"[Silent Setup] Executable: {exe}")

if __name__ == "__main__":
    if "/S" in sys.argv or "--silent" in sys.argv:
        run_silent()
    else:
        run_gui()

"""
Build script for Kanban Desktop Application
Creates a standalone .exe file using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import tempfile

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()

# Use local temp directory to avoid Google Drive sync issues
TEMP_BUILD_DIR = Path(tempfile.gettempdir()) / "KanbanBuild"
DIST_DIR = TEMP_BUILD_DIR / "dist"
BUILD_DIR = TEMP_BUILD_DIR / "build"

def clean_build():
    """Remove previous build artifacts."""
    print("[*] Cleaning previous builds...")
    if TEMP_BUILD_DIR.exists():
        shutil.rmtree(TEMP_BUILD_DIR, ignore_errors=True)
    # Create all required directories
    TEMP_BUILD_DIR.mkdir(exist_ok=True)
    DIST_DIR.mkdir(exist_ok=True)
    BUILD_DIR.mkdir(exist_ok=True)
    spec_file = SCRIPT_DIR / "KanbanBoard.spec"
    if spec_file.exists():
        try:
            spec_file.unlink()
        except:
            pass

def install_dependencies():
    """Install required packages."""
    print("[*] Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                   cwd=SCRIPT_DIR, check=True)

def build_exe():
    """Build the executable."""
    print("[*] Building executable...")
    print(f"    Output directory: {DIST_DIR}")
    
    # PyInstaller command (splash screen removed to avoid Tcl DLL issues)
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=KanbanBoard",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--add-data=kanban.html;.",
        "--add-data=loading.png;.",
        "--add-data=logo.png;.",
        "--icon=icon.ico",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        "--hidden-import=pystray._win32",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=plyer.platforms.win.notification",
        "--exclude-module=tkinter",
        "--exclude-module=matplotlib",
        "--exclude-module=scipy",
        "--exclude-module=pandas",
        "--exclude-module=notebook",
        "--exclude-module=unittest",
        "--exclude-module=pydoc",
        "--exclude-module=pdb",
        "--exclude-module=distutils",
        "--exclude-module=setuptools",
        "--exclude-module=asyncio",
        "--exclude-module=curses",
        "--exclude-module=lib2to3",
        "--exclude-module=xmlrpc",
        "--exclude-module=test",
        # "--clean", # Optional
        "main.py"
    ]
    
    subprocess.run(cmd, cwd=SCRIPT_DIR, check=True)

def copy_assets():
    """Copy required assets to dist folder."""
    print("[*] Copying assets...")
    
    dist_folder = DIST_DIR
    if not dist_folder.exists():
        print("[!] Dist folder not found!")
        return
    
    # Create data folder structure
    data_folder = dist_folder / "data"
    data_folder.mkdir(exist_ok=True)
    
    backup_folder = data_folder / "backups"
    backup_folder.mkdir(exist_ok=True)
    
    print("[+] Created data folders")

def main():
    print("=" * 50)
    print("   Kanban Desktop - Build Script")
    print("=" * 50)
    print()
    
    try:
        clean_build()
        install_dependencies()
        build_exe()
        copy_assets()
        
        print()
        print("=" * 50)
        print("   [+] Build Complete!")
        print("=" * 50)
        print()
        print(f"Location: {DIST_DIR / 'KanbanBoard.exe'}")
        print()
        print("To run the application:")
        print(f"  1. Copy the 'KanbanBoard.exe' from '{DIST_DIR}' to any folder")
        print("  2. Double-click to run")
        print()
        print("Note: The app will create a 'data' folder next to the exe")
        print("      to store your tasks and settings.")
        
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Build failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

"""
Build script for Kanban Desktop Application (Linux)
Creates a standalone executable using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import tempfile

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()

# Use local temp directory
TEMP_BUILD_DIR = Path(tempfile.gettempdir()) / "KanbanBuildLinux"
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
    
    # Clean possible spec file
    spec_file = SCRIPT_DIR / "KanbanBoard.spec"
    if spec_file.exists():
        try:
            spec_file.unlink()
        except:
            pass

def install_dependencies():
    """Install required packages."""
    print("[*] Checking dependencies...")
    # subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
    #                cwd=SCRIPT_DIR, check=True)
    print("    Skipping automatic installation to avoid 'externally-managed-environment' errors.")
    print("    Please ensure 'requirements.txt' packages are installed manually if build fails.")

def build_exe():
    """Build the executable."""
    print("[*] Building executable for Linux...")
    print(f"    Output directory: {DIST_DIR}")
    
    # PyInstaller command for Linux
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=KanbanBoard",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--add-data=kanban.html:.",  # Note: separator is : on Linux
        "--add-data=loading.png:.", 
        "--add-data=logo.png:.", 
        # No icon argument for Linux build typically, handled by .desktop or app window
        "--hidden-import=gi",
        "--hidden-import=gi.repository.Gtk",
        "--hidden-import=gi.repository.Gdk",
        "--hidden-import=gi.repository.GLib",
        "--hidden-import=gi.repository.GObject",
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
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        # Removed Windows-specific hidden info
        "--clean",
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
    print("   Kanban Desktop - Linux Build Script")
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
        print(f"Location: {DIST_DIR / 'KanbanBoard'}")
        print()
        print("To run the application:")
        print(f"  1. Copy the 'KanbanBoard' binary from '{DIST_DIR}' to any folder")
        print("  2. Ensure it has execute permissions (chmod +x KanbanBoard)")
        print("  3. Run ./KanbanBoard")
        print()
        
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Build failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

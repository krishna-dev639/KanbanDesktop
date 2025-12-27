# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('kanban.html', '.'), ('loading.png', '.'), ('logo.png', '.')],
    hiddenimports=['gi', 'gi.repository.Gtk', 'gi.repository.Gdk', 'gi.repository.GLib', 'gi.repository.GObject'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'pandas', 'notebook', 'unittest', 'pydoc', 'pdb', 'distutils', 'setuptools', 'asyncio', 'curses', 'lib2to3', 'xmlrpc', 'test'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='KanbanBoard_Linux_v1.0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

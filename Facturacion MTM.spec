# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/icon.png', 'assets'),
        ('assets/icon.ico', 'assets'),
        ('app/assets/bulk_template.xlsx', 'app/assets'),
    ],
    hiddenimports=['docx', 'pypdf', 'win32com', 'win32com.client', 'pythoncom', 'pywintypes'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'numpy', 'pandas', 'matplotlib', 'scipy', 'PIL', 'Pillow', 'tkinter',
        'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuickControls2',
        'PySide6.QtQuickWidgets', 'PySide6.QtQuick3D',
        'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineQuick', 'PySide6.QtWebChannel', 'PySide6.QtWebSockets',
        'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
        'PySide6.Qt3DCore', 'PySide6.Qt3DRender', 'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic', 'PySide6.Qt3DAnimation', 'PySide6.Qt3DExtras',
        'PySide6.QtCharts', 'PySide6.QtDataVisualization',
        'PySide6.QtPdf', 'PySide6.QtPdfWidgets', 'PySide6.QtSql',
        'PySide6.QtHelp', 'PySide6.QtDesigner', 'PySide6.QtUiTools',
        'PySide6.QtTest',
    ],
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
    name='Facturacion MTM',
    icon='assets/icon.ico',
    version='version_info.txt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('ui', 'ui'),
        ('assets', 'assets'),
        ('bin', 'bin'),
        ('config', 'config'),
        ('assets/icon.ico', '.'),
    ],
    hiddenimports=[
        'src.models',
        'src.curriculum_engine',
        'src.room_allocation_engine',
        'src.fet_constraints_catalog',
        'src.fet_xml_generator',
        'src.timetable_engine',
        'src.fet_native_bridge',
        'src.export_engine',
        'src.desktop_server',
        'src.splash_screen',
        'src.auth_engine',
        'src.exam_management_engine',
        'src.golden_window_engine',
        'src.surveillance_daily_report_engine',
        'src.student_mobility_engine',
        'openpyxl',
        'tkinter',
        'tkinter.ttk',
        'pymupdf',
        'webview',
        'webview.platforms.winforms',
        'webview.platforms.edgechromium',
        'pythonnet',
        'clr_loader',
        'bottle',
        'proxy_tools',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

splash = Splash(
    'assets/splash.png',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
)

exe = EXE(
    pyz,
    a.scripts,
    splash,
    splash.binaries,
    [],
    exclude_binaries=True,
    name='RzzakFet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    splash.binaries,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RzzakFet',
)

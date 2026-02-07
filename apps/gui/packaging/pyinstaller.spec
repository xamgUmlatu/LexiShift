# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from typing import Optional

block_cipher = None


def _find_repo_root(start_dir: str) -> str:
    current = os.path.abspath(start_dir)
    while True:
        marker = os.path.join(current, "core", "lexishift_core", "__init__.py")
        if os.path.exists(marker):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            raise RuntimeError(f"Unable to locate LexiShift repo root from: {start_dir}")
        current = parent


def _spec_path_from_argv() -> Optional[str]:
    for arg in sys.argv[1:]:
        if arg.endswith(".spec") and os.path.exists(arg):
            return os.path.abspath(arg)
    return None


# Resolve the repo root from env, spec path, or current working directory.
env_repo_root = os.environ.get("LEXISHIFT_REPO_ROOT")
env_spec_path = os.environ.get("LEXISHIFT_SPEC_PATH")
argv_spec_path = _spec_path_from_argv()
spec_hint = env_spec_path or argv_spec_path
repo_root = env_repo_root or _find_repo_root(os.path.dirname(spec_hint) if spec_hint else os.getcwd())
spec_dir = os.path.join(repo_root, "apps", "gui", "packaging")

APP_NAME = "LexiShift"
APP_DISPLAY_NAME = "LexiShift"
APP_DESCRIPTION = "LexiShift desktop app"
APP_BUNDLE_ID = "com.lexishift.app"
APP_VERSION = "0.1.0"
APP_BUILD = "0.1.0"
APP_COMPANY_NAME = "LexiShift"
APP_PRODUCT_NAME = "LexiShift"
APP_COPYRIGHT = "髮ｻ蟄舌Ξ繝ｳ繧ｸ"
APP_CATEGORY = "public.app-category.productivity"

HELPER_APP_NAME = "LexiShiftHelper"
HELPER_DISPLAY_NAME = "LexiShift Helper"
HELPER_BUNDLE_NAME = "LexiShift Helper"
HELPER_DESCRIPTION = "LexiShift helper tray app"
HELPER_BUNDLE_ID = "com.lexishift.helper.agent"
HELPER_CATEGORY = "public.app-category.utilities"

# Paths to branding assets in the new structure
icon_icns = os.path.join(repo_root, "apps", "gui", "resources", "ttbn.icns")
icon_ico = os.path.join(repo_root, "apps", "gui", "resources", "ttbn.ico")
if sys.platform == "darwin":
    icon_path = icon_icns
    EXE_NAME = APP_NAME
    COLLECT_NAME = f"{APP_NAME}_dir"
else:
    icon_path = icon_ico
    EXE_NAME = APP_NAME
    COLLECT_NAME = APP_NAME

# macOS bundle settings (explicit for easy editing)
MACOS_DEV_REGION = "ja"
MACOS_MIN_SYSTEM_VERSION = None
MACOS_ICON_FILE = os.path.basename(icon_icns)
MACOS_INFO_PLIST = {
    "CFBundleDevelopmentRegion": MACOS_DEV_REGION,
    "CFBundleName": APP_NAME,
    "CFBundleDisplayName": APP_DISPLAY_NAME,
    "CFBundleExecutable": APP_NAME,
    "CFBundleIdentifier": APP_BUNDLE_ID,
    "CFBundleShortVersionString": APP_VERSION,
    "CFBundleVersion": APP_BUILD,
    "CFBundlePackageType": "APPL",
    "CFBundleIconFile": MACOS_ICON_FILE,
    "LSApplicationCategoryType": APP_CATEGORY,
    "LSBackgroundOnly": False,
    "NSHighResolutionCapable": True,
    "NSHumanReadableCopyright": APP_COPYRIGHT,
}
HELPER_MACOS_INFO_PLIST = {
    "CFBundleDevelopmentRegion": MACOS_DEV_REGION,
    "CFBundleName": HELPER_APP_NAME,
    "CFBundleDisplayName": HELPER_DISPLAY_NAME,
    "CFBundleExecutable": HELPER_APP_NAME,
    "CFBundleIdentifier": HELPER_BUNDLE_ID,
    "CFBundleShortVersionString": APP_VERSION,
    "CFBundleVersion": APP_BUILD,
    "CFBundlePackageType": "APPL",
    "CFBundleIconFile": MACOS_ICON_FILE,
    "LSApplicationCategoryType": HELPER_CATEGORY,
    "LSBackgroundOnly": False,
    "LSUIElement": True,
    "NSHighResolutionCapable": True,
    "NSHumanReadableCopyright": APP_COPYRIGHT,
}
MACOS_CODESIGN_IDENTITY = None
MACOS_ENTITLEMENTS_FILE = None
if MACOS_MIN_SYSTEM_VERSION:
    MACOS_INFO_PLIST["LSMinimumSystemVersion"] = MACOS_MIN_SYSTEM_VERSION
    HELPER_MACOS_INFO_PLIST["LSMinimumSystemVersion"] = MACOS_MIN_SYSTEM_VERSION

# Windows version resource (explicit for easy editing)
WIN_FILE_VERSION = (0, 1, 0, 0)
WIN_PRODUCT_VERSION = (0, 1, 0, 0)
WIN_VERSION_STR = APP_VERSION
WIN_VERSION_FILE = os.path.join(spec_dir, "windows_version_info.txt")
WIN_MANIFEST_FILE = None
WIN_UAC_ADMIN = False
WIN_UAC_UIACCESS = False

WIN_VERSION_INFO = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={WIN_FILE_VERSION},
    prodvers={WIN_PRODUCT_VERSION},
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        "040904B0",
        [
          StringStruct("CompanyName", "{APP_COMPANY_NAME}"),
          StringStruct("FileDescription", "{APP_DESCRIPTION}"),
          StringStruct("FileVersion", "{WIN_VERSION_STR}"),
          StringStruct("InternalName", "{APP_NAME}"),
          StringStruct("LegalCopyright", "{APP_COPYRIGHT}"),
          StringStruct("OriginalFilename", "{APP_NAME}.exe"),
          StringStruct("ProductName", "{APP_PRODUCT_NAME}"),
          StringStruct("ProductVersion", "{WIN_VERSION_STR}")
        ]
      )
    ]),
    VarFileInfo([VarStruct("Translation", [1033, 1200])])
  ]
)
"""

if sys.platform == "win32":
    with open(WIN_VERSION_FILE, "w", encoding="utf-8") as handle:
        handle.write(WIN_VERSION_INFO)

common_pathex = [
    os.path.join(repo_root, "apps", "gui", "src"),
    os.path.join(repo_root, "core"),
    repo_root,
]

main_datas = [
    (os.path.join(repo_root, "apps", "gui", "resources"), "resources"),
    (os.path.join(repo_root, "scripts", "helper", "lexishift_native_host.py"), "resources/helper"),
    (os.path.join(repo_root, "core", "lexishift_core"), "resources/helper/lexishift_core"),
    (os.path.join(repo_root, "apps", "gui", "src", "helper_daemon.py"), "resources/helper"),
]

main_a = Analysis(
    [os.path.join(repo_root, "apps", "gui", "src", "main.py")],
    pathex=common_pathex,
    binaries=[],
    datas=main_datas,
    hiddenimports=["lexishift_core"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

main_pyz = PYZ(main_a.pure, main_a.zipped_data, cipher=block_cipher)

main_exe = EXE(
    main_pyz,
    main_a.scripts,
    main_a.binaries,
    main_a.zipfiles,
    main_a.datas,
    [],
    name=EXE_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=sys.platform == "darwin",
    target_arch=None,
    codesign_identity=MACOS_CODESIGN_IDENTITY,
    entitlements_file=MACOS_ENTITLEMENTS_FILE,
    icon=icon_path,
    version=WIN_VERSION_FILE if sys.platform == "win32" else None,
    manifest=WIN_MANIFEST_FILE,
    uac_admin=WIN_UAC_ADMIN,
    uac_uiaccess=WIN_UAC_UIACCESS,
)

if sys.platform == "darwin":
    main_coll = COLLECT(
        main_exe,
        main_a.binaries,
        main_a.zipfiles,
        main_a.datas,
        strip=False,
        upx=True,
        name=COLLECT_NAME,
    )
    app = BUNDLE(
        main_coll,
        name=f"{APP_NAME}.app",
        icon=icon_icns,
        bundle_identifier=APP_BUNDLE_ID,
        info_plist=MACOS_INFO_PLIST,
    )

    helper_a = Analysis(
        [os.path.join(repo_root, "apps", "gui", "src", "helper_app.py")],
        pathex=common_pathex,
        binaries=[],
        datas=[(os.path.join(repo_root, "apps", "gui", "resources"), "resources")],
        hiddenimports=["lexishift_core"],
        hookspath=[],
        runtime_hooks=[],
        excludes=[],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=block_cipher,
    )

    helper_pyz = PYZ(helper_a.pure, helper_a.zipped_data, cipher=block_cipher)

    helper_exe = EXE(
        helper_pyz,
        helper_a.scripts,
        helper_a.binaries,
        helper_a.zipfiles,
        helper_a.datas,
        [],
        name=HELPER_APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=True,
        target_arch=None,
        codesign_identity=MACOS_CODESIGN_IDENTITY,
        entitlements_file=MACOS_ENTITLEMENTS_FILE,
        icon=icon_icns,
    )

    helper_coll = COLLECT(
        helper_exe,
        helper_a.binaries,
        helper_a.zipfiles,
        helper_a.datas,
        strip=False,
        upx=True,
        name=f"{HELPER_APP_NAME}_dir",
    )

    helper_app = BUNDLE(
        helper_coll,
        name=f"{HELPER_BUNDLE_NAME}.app",
        icon=icon_icns,
        bundle_identifier=HELPER_BUNDLE_ID,
        info_plist=HELPER_MACOS_INFO_PLIST,
    )
else:
    coll = COLLECT(
        main_exe,
        main_a.binaries,
        main_a.zipfiles,
        main_a.datas,
        strip=False,
        upx=True,
        name=COLLECT_NAME,
    )

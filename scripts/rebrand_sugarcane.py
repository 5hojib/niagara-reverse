#!/usr/bin/env python3
"""Replace human-facing Salt Player branding in an apktool disassembly.

Internal package names, preference/product identifiers, file-format markers,
and working upstream URLs are intentionally left unchanged.
"""

import argparse
from pathlib import Path


TEXT_REPLACEMENTS = (
    (b"Visit SaltPlayerSource", b"Visit the upstream project"),
    (b"SALT PLAYER", b"SUGARCANE"),
    (b"Salt Player", b"Sugarcane"),
    (b"Salt player", b"Sugarcane"),
    (b"salt player", b"Sugarcane"),
)

SMALI_REPLACEMENTS = (
    ("SALT PLAYER", "SUGARCANE"),
    ("Salt Player", "Sugarcane"),
    ("Salt player", "Sugarcane"),
    ("salt player", "Sugarcane"),
)

# Persisted identifiers/file signatures must remain byte-compatible. These are
# not user-facing labels.
PRESERVED_SMALI_LITERALS = {
    '"Salt Player Channel Id"',
    '"SALT PLAYER AUDIOFX V4"',
}

TEXT_SUFFIXES = {
    ".css",
    ".htm",
    ".html",
    ".js",
    ".json",
    ".md",
    ".properties",
    ".txt",
    ".xml",
}


def patch_text_tree(root: Path) -> tuple[int, int]:
    files_changed = replacements = 0
    for directory_name in ("res", "assets"):
        directory = root / directory_name
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            original = path.read_bytes()
            patched = original
            for old, new in TEXT_REPLACEMENTS:
                count = patched.count(old)
                replacements += count
                patched = patched.replace(old, new)
            if patched != original:
                path.write_bytes(patched)
                files_changed += 1
    return files_changed, replacements


def patch_smali_tree(root: Path) -> tuple[int, int]:
    files_changed = replacements = 0
    for path in root.rglob("*.smali"):
        original = path.read_text()
        lines = original.splitlines(keepends=True)
        changed = False
        for index, line in enumerate(lines):
            if "const-string " not in line:
                continue
            if any(literal in line for literal in PRESERVED_SMALI_LITERALS):
                continue
            patched = line
            for old, new in SMALI_REPLACEMENTS:
                count = patched.count(old)
                replacements += count
                patched = patched.replace(old, new)
            if patched != line:
                lines[index] = patched
                changed = True
        if changed:
            path.write_text("".join(lines))
            files_changed += 1
    return files_changed, replacements


def patch_native_library(path: Path) -> int:
    """Patch equal-width branding in native display strings without moving ELF data."""
    if not path.is_file():
        raise ValueError(f"Native library not found: {path}")
    original = path.read_bytes()
    old = b"Salt Player"
    new = b"Sugarcane  "
    if len(old) != len(new):
        raise AssertionError("Native replacement must preserve byte length")
    count = original.count(old)
    if count == 0:
        raise ValueError("Expected native Salt Player branding was not found")
    path.write_bytes(original.replace(old, new))
    return count


def verify(resource_root: Path, smali_root: Path) -> None:
    default_strings = resource_root / "res/values/strings.xml"
    values = default_strings.read_text()
    if '<string name="app_name">Sugarcane</string>' not in values:
        raise ValueError("Default app_name was not changed to Sugarcane")

    forbidden = ("Salt Player", "Salt player", "salt player", "SALT PLAYER")
    for directory_name in ("res", "assets"):
        directory = resource_root / directory_name
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            text = path.read_text(errors="replace")
            if any(value in text for value in forbidden):
                raise ValueError(f"Human-facing branding remains in {path}")

    for path in smali_root.rglob("*.smali"):
        for line in path.read_text().splitlines():
            if "const-string " not in line:
                continue
            if any(literal in line for literal in PRESERVED_SMALI_LITERALS):
                continue
            if any(value in line for value in forbidden):
                raise ValueError(f"Hardcoded branding remains in {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("resource_root", type=Path, help="apktool root containing res/ and assets/")
    parser.add_argument("smali_root", type=Path, help="primary classes.dex smali directory")
    args = parser.parse_args()

    text_files, text_count = patch_text_tree(args.resource_root)
    smali_files, smali_count = patch_smali_tree(args.smali_root)
    native_count = patch_native_library(
        args.resource_root / "lib/arm64-v8a/libexp82464.so"
    )
    verify(args.resource_root, args.smali_root)
    print(
        f"Rebranded {text_count} text occurrences in {text_files} files, "
        f"{smali_count} DEX literals in {smali_files} files, and "
        f"{native_count} native occurrences"
    )


if __name__ == "__main__":
    main()

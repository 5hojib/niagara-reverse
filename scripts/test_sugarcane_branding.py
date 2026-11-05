#!/usr/bin/env python3
"""Regression tests for the final Sugarcane-branded stable APK.

Requires unicorn==2.1.4 and six arguments:
BASE_APK FINAL_APK STANDARD_CONFIG FINAL_CONFIG DECODED_ROOT FINAL_SMALI_ROOT
"""

import struct
import sys
import unittest
import zipfile
from pathlib import Path

from fix_apk_validation import LIBRARY_ENTRY, apk_certificate, signature_hash
from test_apk_validation import native_certificate_hash
from test_local_features import LOCAL_KEYS, instructions, methods, run_defaults


ALLOWED_CHANGED_ENTRIES = {
    "META-INF/MANIFEST.MF",
    "META-INF/SALT.RSA",
    "META-INF/SALT.SF",
    "assets/src/en/privacy_policy.txt",
    "assets/src/en/terms_of_use_for_software.txt",
    "assets/src/zh-CN/terms_of_use_for_software.txt",
    "classes.dex",
    "lib/arm64-v8a/libexp82464.so",
    "resources.arsc",
}

ALLOWED_INTERNAL_BRANDING = (
    "SaltPlayerPro",
    "Salt Player Channel Id",
    "SALT PLAYER AUDIOFX V4",
    "github.com/Moriafly/SaltPlayerSource",
    "t.me/saltplayerupdate",
)


class SugarcaneBrandingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.standard_config = methods(STANDARD_CONFIG.read_text())
        cls.final_config = methods(FINAL_CONFIG.read_text())
        cls.helper = cls.final_config["enableLocalFeatureDefaults()V"]

    def test_app_label_is_sugarcane_in_every_packaged_locale(self) -> None:
        string_files = list((DECODED_ROOT / "res").glob("values*/strings.xml"))
        labels = []
        for path in string_files:
            for line in path.read_text().splitlines():
                if 'name="app_name"' in line:
                    labels.append((path, line.strip()))
        self.assertTrue(labels)
        for path, label in labels:
            self.assertEqual(label, '<string name="app_name">Sugarcane</string>', path)

    def test_human_facing_branding_is_removed(self) -> None:
        forbidden = ("Salt Player", "Salt player", "salt player")
        for directory_name in ("res", "assets"):
            directory = DECODED_ROOT / directory_name
            for path in directory.rglob("*"):
                if path.is_file():
                    text = path.read_text(errors="replace")
                    self.assertFalse(any(value in text for value in forbidden), path)

        for path in FINAL_SMALI_ROOT.rglob("*.smali"):
            for line in path.read_text().splitlines():
                if "const-string " not in line:
                    continue
                if any(value in line for value in ALLOWED_INTERNAL_BRANDING):
                    continue
                self.assertFalse(any(value in line for value in forbidden), path)

    def test_local_feature_defaults_are_preserved(self) -> None:
        self.assertEqual(run_defaults(self.helper, {}), dict.fromkeys(LOCAL_KEYS, True))
        for name in ("ނ", "ރ", "އ"):
            self.assertEqual(
                instructions(self.final_config[f"{name}(Z)V"])[0],
                "const/4 p0, 0x1",
            )

    def test_only_expected_apk_payload_changes(self) -> None:
        with zipfile.ZipFile(BASE_APK) as before, zipfile.ZipFile(FINAL_APK) as after:
            self.assertEqual(set(before.namelist()), set(after.namelist()))
            changed = {
                name for name in before.namelist()
                if before.read(name) != after.read(name)
            }
            self.assertEqual(changed, ALLOWED_CHANGED_ENTRIES)
            self.assertIsNone(after.testzip())

    def test_package_manifest_and_secondary_dex_files_are_unchanged(self) -> None:
        with zipfile.ZipFile(BASE_APK) as before, zipfile.ZipFile(FINAL_APK) as after:
            for name in ("AndroidManifest.xml", "classes2.dex", "classes3.dex", "classes100.dex"):
                self.assertEqual(before.read(name), after.read(name), name)

    def test_primary_dex_version_and_reference_count_are_preserved(self) -> None:
        with zipfile.ZipFile(BASE_APK) as before, zipfile.ZipFile(FINAL_APK) as after:
            baseline = before.read("classes.dex")
            final = after.read("classes.dex")
        self.assertEqual(final[:8], baseline[:8])
        self.assertEqual(final[:8], b"dex\n035\0")
        self.assertEqual(
            struct.unpack_from("<I", final, 0x58)[0],
            struct.unpack_from("<I", baseline, 0x58)[0],
        )

    def test_signing_key_and_native_startup_check_are_preserved(self) -> None:
        certificate = apk_certificate(FINAL_APK)
        self.assertEqual(apk_certificate(BASE_APK), certificate)
        with zipfile.ZipFile(FINAL_APK) as archive:
            library = archive.read(LIBRARY_ENTRY)
        self.assertEqual(native_certificate_hash(library), signature_hash(certificate))

    def test_native_visible_brand_is_replaced_without_resizing_library(self) -> None:
        with zipfile.ZipFile(BASE_APK) as before, zipfile.ZipFile(FINAL_APK) as after:
            original = before.read(LIBRARY_ENTRY)
            final = after.read(LIBRARY_ENTRY)
        self.assertEqual(len(original), len(final))
        self.assertGreater(original.count(b"Salt Player"), 0)
        self.assertEqual(final.count(b"Salt Player"), 0)
        self.assertEqual(final.count(b"Sugarcane  "), original.count(b"Salt Player"))


if __name__ == "__main__":
    if len(sys.argv) != 7:
        sys.exit(
            "Usage: test_sugarcane_branding.py BASE_APK FINAL_APK "
            "STANDARD_CONFIG FINAL_CONFIG DECODED_ROOT FINAL_SMALI_ROOT"
        )
    (
        BASE_APK,
        FINAL_APK,
        STANDARD_CONFIG,
        FINAL_CONFIG,
        DECODED_ROOT,
        FINAL_SMALI_ROOT,
    ) = map(Path, sys.argv[1:])
    unittest.main(argv=[sys.argv[0]], verbosity=2)

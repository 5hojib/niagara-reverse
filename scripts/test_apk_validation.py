#!/usr/bin/env python3
"""Execute the actual ARM64 certificate-hash getter with Unicorn, not Android.

Usage: python3 scripts/test_apk_validation.py ORIGINAL_APK FIXED_APK PREVIOUS_ENGLISH_APK
Requires unicorn==2.1.4. Neither APK is installed or launched.
"""

import struct
import sys
import unittest
import zipfile
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM
from unicorn.arm64_const import (
    UC_ARM64_REG_PC,
    UC_ARM64_REG_SP,
    UC_ARM64_REG_W0,
    UC_ARM64_REG_X30,
)

from fix_apk_validation import (
    LIBRARY_ENTRY,
    ORIGINAL_CERTIFICATE_HASH,
    apk_certificate,
    retarget_library,
    signature_hash,
)


def native_certificate_hash(library):
    """Load PT_LOAD segments and run the unchanged getter/branch on ARM64."""
    base, stack, stop = 0x100000, 0x200000, 0x300000
    emulator = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
    emulator.mem_map(base, 0x10000)
    emulator.mem_map(stack, 0x10000)
    emulator.mem_map(stop, 0x1000)
    if library[:6] != b"\x7fELF\x02\x01":
        raise ValueError("Expected a 64-bit little-endian ELF library")
    machine = struct.unpack_from("<H", library, 18)[0]
    if machine != 183:
        raise ValueError("Expected AArch64 ELF")
    headers = struct.unpack_from("<Q", library, 32)[0]
    entry_size, count = struct.unpack_from("<HH", library, 54)
    for index in range(count):
        kind, _, offset, address, _, file_size, memory_size, _ = struct.unpack_from(
            "<IIQQQQQQ", library, headers + index * entry_size
        )
        if kind != 1:
            continue
        if address + memory_size > 0x10000 or file_size > memory_size:
            raise ValueError("ELF segment exceeds the test memory map")
        emulator.mem_write(base + address, library[offset:offset + file_size])
    emulator.reg_write(UC_ARM64_REG_SP, stack + 0xF000)
    emulator.reg_write(UC_ARM64_REG_X30, stop)
    # getCacheVersion at 0x1a10 calls the original helper at 0x26a0.
    # Neither routine invokes JNI or OS functions, so no mocks are needed.
    emulator.emu_start(base + 0x1A10, stop, count=1000)
    if emulator.reg_read(UC_ARM64_REG_PC) != stop:
        raise RuntimeError("Native getter did not return within the instruction limit")
    return emulator.reg_read(UC_ARM64_REG_W0)


class ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_certificate = apk_certificate(ORIGINAL_APK)
        cls.rebuild_certificate = apk_certificate(REBUILT_APK)
        with zipfile.ZipFile(ORIGINAL_APK) as archive:
            cls.original_library = archive.read(LIBRARY_ENTRY)
        with zipfile.ZipFile(REBUILT_APK) as archive:
            cls.rebuilt_library = archive.read(LIBRARY_ENTRY)

    def test_original_certificate_matches_original_native_check(self):
        self.assertEqual(signature_hash(self.original_certificate), ORIGINAL_CERTIFICATE_HASH)
        self.assertEqual(native_certificate_hash(self.original_library), ORIGINAL_CERTIFICATE_HASH)

    def test_reproduces_old_rebuild_rejection(self):
        self.assertNotEqual(
            native_certificate_hash(self.original_library), signature_hash(self.rebuild_certificate)
        )

    def test_fixed_native_check_accepts_rebuild_certificate(self):
        self.assertEqual(
            native_certificate_hash(self.rebuilt_library), signature_hash(self.rebuild_certificate)
        )

    def test_check_is_not_disabled_for_other_certificates(self):
        expected = native_certificate_hash(self.rebuilt_library)
        self.assertNotEqual(expected, signature_hash(self.original_certificate))
        self.assertNotEqual(expected, signature_hash(b"unrelated signing certificate"))

    def test_only_two_constant_load_instructions_changed(self):
        self.assertEqual(len(self.original_library), len(self.rebuilt_library))
        changed = {
            index for index, pair in enumerate(zip(self.original_library, self.rebuilt_library))
            if pair[0] != pair[1]
        }
        self.assertTrue(changed)
        self.assertLessEqual(changed, set(range(0x1A1C, 0x1A20)) | set(range(0x1A24, 0x1A28)))
        self.assertEqual(
            retarget_library(self.original_library, self.rebuild_certificate), self.rebuilt_library
        )

    def test_dex_translations_unchanged(self):
        with zipfile.ZipFile(REBUILT_APK) as rebuilt, zipfile.ZipFile(PREVIOUS_APK) as previous:
            for name in ("classes.dex", "classes2.dex", "classes3.dex", "classes100.dex"):
                self.assertEqual(rebuilt.read(name), previous.read(name), name)

    def test_other_app_payload_unchanged(self):
        signing_entries = {"META-INF/MANIFEST.MF", "META-INF/SALT.RSA", "META-INF/SALT.SF"}
        with zipfile.ZipFile(REBUILT_APK) as rebuilt, zipfile.ZipFile(PREVIOUS_APK) as previous:
            self.assertEqual(set(rebuilt.namelist()), set(previous.namelist()))
            for name in rebuilt.namelist():
                if name != LIBRARY_ENTRY and name not in signing_entries:
                    self.assertEqual(rebuilt.read(name), previous.read(name), name)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("Usage: test_apk_validation.py ORIGINAL_APK FIXED_APK PREVIOUS_ENGLISH_APK")
    ORIGINAL_APK, REBUILT_APK, PREVIOUS_APK = map(Path, sys.argv[1:])
    unittest.main(argv=[sys.argv[0]], verbosity=2)

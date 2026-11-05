#!/usr/bin/env python3
"""Retarget Salt Player 12.6.0's native certificate check to a rebuild key.

This changes the expected certificate hash, not the check or its callers.
Only the exact original arm64 library is accepted as input.
"""

import argparse
import hashlib
import struct
from pathlib import Path


ORIGINAL_LIBRARY_SHA256 = (
    "9b0b72d4daee77f59b7018f2f4fbca930ca517aea3cdd68d77d0b26cabf3299f"
)
LIBRARY_ENTRY = "lib/arm64-v8a/libexp82464.so"
ORIGINAL_CERTIFICATE_HASH = 0xBA4870D3
V2_BLOCK_ID = 0x7109871A


def length_prefixed(data, offset=0):
    if offset < 0 or offset + 4 > len(data):
        raise ValueError("Truncated length-prefixed signing data")
    size = struct.unpack_from("<I", data, offset)[0]
    end = offset + 4 + size
    if end > len(data):
        raise ValueError("Signing-data length exceeds its enclosing block")
    return data[offset + 4:end], end


def apk_certificate(apk):
    """Read the first v2 signer certificate; this does not verify signatures.

    Run apksigner verify separately before trusting an input APK.
    Multiple signers are deliberately rejected for this single-signer build.
    """
    data = Path(apk).read_bytes()
    end_record = None
    for offset in range(len(data) - 22, max(-1, len(data) - 65558), -1):
        if data[offset:offset + 4] != b"PK\x05\x06":
            continue
        comment_size = struct.unpack_from("<H", data, offset + 20)[0]
        if offset + 22 + comment_size == len(data):
            end_record = offset
            break
    if end_record is None:
        raise ValueError("ZIP end-of-central-directory record not found")
    directory = struct.unpack_from("<I", data, end_record + 16)[0]
    if directory < 32 or directory > end_record:
        raise ValueError("Invalid ZIP central-directory offset")
    if data[directory - 16:directory] != b"APK Sig Block 42":
        raise ValueError("APK signing block not found")
    size = struct.unpack_from("<Q", data, directory - 24)[0]
    start = directory - size - 8
    if start < 0 or size < 24 or struct.unpack_from("<Q", data, start)[0] != size:
        raise ValueError("Invalid APK signing-block size")
    offset = start + 8
    end = directory - 24
    certificate = None
    while offset < end:
        if offset + 12 > end:
            raise ValueError("Truncated APK signing-block entry")
        entry_size, identifier = struct.unpack_from("<QI", data, offset)
        entry_end = offset + 8 + entry_size
        if entry_size < 4 or entry_end > end:
            raise ValueError("Invalid APK signing-block entry size")
        if identifier == V2_BLOCK_ID:
            if certificate is not None:
                raise ValueError("Duplicate v2 signing block")
            signers, value_end = length_prefixed(data[offset + 12:entry_end])
            if value_end != entry_size - 4:
                raise ValueError("Trailing v2 signing data")
            signer, signer_end = length_prefixed(signers)
            if signer_end != len(signers):
                raise ValueError("Expected exactly one APK signer")
            signed_data, _ = length_prefixed(signer)
            _, position = length_prefixed(signed_data)
            certificates, _ = length_prefixed(signed_data, position)
            certificate, _ = length_prefixed(certificates)
            if not certificate:
                raise ValueError("Empty APK certificate")
        offset = entry_end
    if certificate is None:
        raise ValueError("APK has no v2 signing certificate")
    return certificate


def signature_hash(certificate):
    """Android Signature.hashCode(), i.e. Arrays.hashCode(signed byte[])."""
    value = 1
    for byte in certificate:
        value = (31 * value + (byte if byte < 128 else byte - 256)) & 0xFFFFFFFF
    return value


def retarget_library(original, certificate):
    if hashlib.sha256(original).hexdigest() != ORIGINAL_LIBRARY_SHA256:
        raise ValueError("Not the original Salt Player 12.6.0 arm64 validation library")
    patched = bytearray(original)
    expected = signature_hash(certificate)
    # getCacheVersion() returns this base + 1 on the normal release path.
    # Keep its conditional increment, state handling, and both DEX callers.
    base = (expected - 1) & 0xFFFFFFFF
    instructions = (
        (0x1A1C, bytes.fromhex("481a8e52"), 0x52800008 | ((base & 0xFFFF) << 5)),
        (0x1A24, bytes.fromhex("0849b772"), 0x72A00008 | ((base >> 16) << 5)),
    )
    for offset, old, replacement in instructions:
        if original[offset:offset + 4] != old:
            raise ValueError(f"Unexpected instruction at {offset:#x}")
        patched[offset:offset + 4] = struct.pack("<I", replacement)
    return bytes(patched)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_library", type=Path)
    parser.add_argument("signed_apk", type=Path, help="Previously verified APK signed with the rebuild key")
    parser.add_argument("output_library", type=Path)
    args = parser.parse_args()
    if args.output_library.exists():
        parser.error("Output already exists; choose a new path")
    certificate = apk_certificate(args.signed_apk)
    original = args.original_library.read_bytes()
    args.output_library.write_bytes(retarget_library(original, certificate))
    print(f"Expected certificate hash: {signature_hash(certificate):#010x}")
    print(f"Certificate SHA-256: {hashlib.sha256(certificate).hexdigest()}")
    print(f"Patched library: {args.output_library}")


if __name__ == "__main__":
    main()

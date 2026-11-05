#!/usr/bin/env python3
"""Test the re-disassembled local-defaults patch and APK payload boundaries.

The small initialization helper is interpreted with an in-memory MMKV stub.
This is not an Android lifecycle/UI test. Requires unicorn==2.1.4 for the
independent check that the earlier ARM64 startup fix is preserved.
"""

import json
import re
import sys
import unittest
import zipfile
from pathlib import Path

from enable_local_features import CONFIG_CLASS, HELPER_NAME
from fix_apk_validation import LIBRARY_ENTRY, apk_certificate, signature_hash
from test_apk_validation import native_certificate_hash


KEY_FIELDS = {
    "Landroidx/media3/თ;->Ԫ:Ljava/lang/String;": "salt_player_pro",
    "Landroidx/media3/თ;->ԫ:Ljava/lang/String;": "salt_player_pro_purchased_2",
}
LOCAL_KEYS = set(KEY_FIELDS.values()) | {"audiophile_pack"}
MMKV_GETTER = "Lcom/salt/music/App$Companion;->Ԫ()Lcom/tencent/mmkv/MMKV;"
MMKV_SETTER = "Lcom/tencent/mmkv/MMKV;->ށ(Ljava/lang/String;Z)V"


def methods(text):
    return {
        declaration.split()[-1]: body
        for declaration, body in re.findall(
            r"^\.method ([^\n]+)\n(.*?)^\.end method", text, re.M | re.S
        )
    }


def instructions(body):
    return [
        line.strip() for line in body.splitlines()
        if line.strip() and not line.strip().startswith((".", "#", ":"))
    ]


def normalized(body):
    labels = {}
    lines = []
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith((".line ", "#")):
            continue
        if not line.startswith("const-string"):
            def label(match):
                name = match.group(0)
                return labels.setdefault(name, f":label_{len(labels)}")
            line = re.sub(r":[A-Za-z_][A-Za-z_0-9]*", label, line)
        lines.append(line)
    return lines


def run_defaults(body, initial):
    """Only the branchless helper's whitelisted instructions/calls are allowed."""
    store = dict(initial)
    registers = {}
    result = None
    returned = False
    for line in instructions(body):
        if line.startswith("invoke-"):
            match = re.fullmatch(r"invoke-(static|virtual) \{([^}]*)\}, (\S+)", line)
            if not match:
                raise ValueError(f"Unexpected invoke: {line}")
            kind, arguments, target = match.groups()
            arguments = [registers[name.strip()] for name in arguments.split(",") if name.strip()]
            if kind == "static" and target == MMKV_GETTER and not arguments:
                result = store
            elif kind == "virtual" and target == MMKV_SETTER and len(arguments) == 3:
                owner, key, value = arguments
                if owner is not store or key not in LOCAL_KEYS:
                    raise ValueError("Helper wrote outside the local availability keys")
                store[key] = bool(value)
            else:
                raise ValueError(f"Unapproved helper call: {target}")
        elif line.startswith("move-result-object "):
            registers[line.split()[-1]] = result
        elif line.startswith("const/4 "):
            register, value = line[len("const/4 "):].split(", ")
            registers[register] = int(value, 0)
        elif line.startswith("sget-object "):
            register, field = line[len("sget-object "):].split(", ")
            registers[register] = KEY_FIELDS[field]
        elif line.startswith("const-string "):
            register, literal = line[len("const-string "):].split(", ", 1)
            registers[register] = json.loads(literal)
        elif line == "return-void":
            returned = True
            break
        else:
            raise ValueError(f"Unexpected helper instruction: {line}")
    if not returned:
        raise ValueError("Helper did not return")
    return store


class LocalFeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = methods(BASE_CONFIG.read_text())
        cls.patched = methods(FEATURE_CONFIG.read_text())
        cls.helper = cls.patched[f"{HELPER_NAME}()V"]

    def test_fresh_install_has_all_local_availability_flags(self):
        self.assertEqual(run_defaults(self.helper, {}), dict.fromkeys(LOCAL_KEYS, True))

    def test_upgrade_overrides_previously_disabled_flags(self):
        before = dict.fromkeys(LOCAL_KEYS, False)
        self.assertEqual(run_defaults(self.helper, before), dict.fromkeys(LOCAL_KEYS, True))

    def test_normal_settings_and_consents_are_preserved(self):
        before = {
            "agree_privacy": False,
            "honor_audio_consent": False,
            "usb_exclusive_output_enabled": False,
            "boolean_morvanium_auto_mix": False,
            "reverse_play_mode": False,
            "anti_alias_filter": False,
            "player_screen_background_cover": "user-selected.jpg",
        }
        after = run_defaults(self.helper, before)
        self.assertEqual({key: after[key] for key in before}, before)

    def test_defaults_are_written_before_the_flags_are_loaded(self):
        initializer = instructions(self.patched["<clinit>()V"])
        call = f"invoke-static {{}}, {CONFIG_CLASS}->{HELPER_NAME}()V"
        self.assertEqual(initializer.count(call), 1)
        for field in ("ދ", "ތ", "ގ"):
            assignment = next(i for i, line in enumerate(initializer) if f"->{field}:Landroidx/media3/sp0;" in line)
            self.assertLess(initializer.index(call), assignment)

    def test_deactivation_cannot_turn_the_local_flags_off(self):
        for name in ("ނ", "ރ", "އ"):
            self.assertEqual(instructions(self.patched[f"{name}(Z)V"])[0], "const/4 p0, 0x1")

    def test_only_the_requested_configuration_methods_change(self):
        self.assertEqual(set(self.patched), set(self.original) | {f"{HELPER_NAME}()V"})
        for name, original in self.original.items():
            patched = normalized(self.patched[name])
            if name == "<clinit>()V":
                patched.remove(f"invoke-static {{}}, {CONFIG_CLASS}->{HELPER_NAME}()V")
            elif name in ("ނ(Z)V", "ރ(Z)V", "އ(Z)V"):
                self.assertEqual(patched[1], "const/4 p0, 0x1")
                del patched[1]
            self.assertEqual(normalized(original), patched, name)

    def test_other_apk_payload_is_unchanged(self):
        allowed = {"classes.dex", "META-INF/MANIFEST.MF", "META-INF/SALT.RSA", "META-INF/SALT.SF"}
        with zipfile.ZipFile(BASE_APK) as before, zipfile.ZipFile(FEATURE_APK) as after:
            self.assertEqual(set(before.namelist()), set(after.namelist()))
            for name in before.namelist():
                if name not in allowed:
                    self.assertEqual(before.read(name), after.read(name), name)

    def test_signing_key_and_native_startup_fix_are_preserved(self):
        certificate = apk_certificate(FEATURE_APK)
        self.assertEqual(apk_certificate(BASE_APK), certificate)
        with zipfile.ZipFile(FEATURE_APK) as archive:
            self.assertEqual(native_certificate_hash(archive.read(LIBRARY_ENTRY)), signature_hash(certificate))


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit("Usage: test_local_features.py BASE_APK FEATURE_APK BASE_CONFIG_SMALI FEATURE_CONFIG_SMALI")
    BASE_APK, FEATURE_APK, BASE_CONFIG, FEATURE_CONFIG = map(Path, sys.argv[1:])
    unittest.main(argv=[sys.argv[0]], verbosity=2)

#!/usr/bin/env python3
"""Regression tests for the Salt Player swipe/lyrics UI variant.

Usage:
    python3 scripts/test_ui_changes.py BASE_APK UI_APK BASE_SMALI UI_SMALI

BASE_SMALI and UI_SMALI are the primary classes.dex baksmali directories
(usually apktool's `smali/` directories), not the decoded APK roots.
Requires unicorn==2.1.4 for the preserved native startup-check test.
"""

import struct
import sys
import unittest
import zipfile
from pathlib import Path

from fix_apk_validation import LIBRARY_ENTRY, apk_certificate, signature_hash
from test_apk_validation import native_certificate_hash


CHANGED_CLASSES = {
    "androidx/media3/ch1.smali",
    "androidx/media3/s92.smali",
    "androidx/media3/ut2.smali",
    "androidx/media3/wt2.smali",
    "com/salt/music/ui/MainActivity.smali",
}
PATCH_CLASS = "com/salt/music/ui/patch/LocalUiPatch.smali"
SIGNATURE_ENTRIES = {
    "META-INF/MANIFEST.MF",
    "META-INF/SALT.RSA",
    "META-INF/SALT.SF",
}


def smali_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*.smali")
    }


def modeled_swipe(
    dx: float,
    dy: float,
    duration_ms: int,
    *,
    density: float = 1.0,
    page: int = 1,
    seeking: bool = False,
    elapsed_since_action_ms: int = 301,
) -> str | None:
    """Behavioral model of LocalUiPatch's threshold/direction decisions."""
    if page != 1 or seeking or not 0 <= duration_ms <= 800:
        return None
    if abs(dx) <= 64.0 * density or abs(dx) <= abs(dy) * 1.25:
        return None
    if elapsed_since_action_ms <= 300:
        return None
    return "previous" if dx >= 0 else "next"


class UiChangeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base_files = smali_files(BASE_SMALI)
        cls.ui_files = smali_files(UI_SMALI)
        cls.patch = cls.ui_files[PATCH_CLASS].decode()
        cls.ch1_before = cls.base_files["androidx/media3/ch1.smali"].decode()
        cls.ch1_after = cls.ui_files["androidx/media3/ch1.smali"].decode()
        cls.pager_call_before = cls.base_files["androidx/media3/ut2.smali"].decode()
        cls.pager_call_after = cls.ui_files["androidx/media3/ut2.smali"].decode()
        cls.pager_impl_before = cls.base_files["androidx/media3/s92.smali"].decode()
        cls.pager_impl_after = cls.ui_files["androidx/media3/s92.smali"].decode()
        cls.activity = cls.ui_files["com/salt/music/ui/MainActivity.smali"].decode()
        cls.lyrics_page = cls.ui_files["androidx/media3/wt2.smali"].decode()

    def test_only_five_existing_classes_and_one_new_class_change(self) -> None:
        self.assertEqual(set(self.ui_files) - set(self.base_files), {PATCH_CLASS})
        self.assertEqual(set(self.base_files) - set(self.ui_files), set())
        changed = {
            name for name in self.base_files
            if self.base_files[name] != self.ui_files[name]
        }
        self.assertEqual(changed, CHANGED_CLASSES)

    def test_lyrics_source_tag_is_removed(self) -> None:
        source_label = "Landroidx/media3/sg1;->Ϳ()Ljava/lang/String;"
        self.assertEqual(self.ch1_before.count(source_label), 1)
        self.assertNotIn(source_label, self.ch1_after)
        self.assertEqual(
            self.ch1_after.count(
                "LocalUiPatch;->renderLyricsBack(Landroidx/media3/r50;)V"
            ),
            1,
        )

    def test_back_button_targets_player_page_with_animation(self) -> None:
        self.assertIn("const v0, 0x7f0800fa", self.patch)  # ic_back_up
        self.assertIn("const v0, 0x7f1200a1", self.patch)  # Back
        self.assertIn("const/4 v4, 0x6", self.patch)
        self.assertIn(
            "Landroidx/media3/hi2;-><init>(Landroidx/media3/ആ;Landroidx/media3/hj2;I)V",
            self.patch,
        )
        self.assertIn(
            "LocalUiPatch;->setLyricsNavigation(Landroidx/media3/ആ;Landroidx/media3/hj2;)V",
            self.lyrics_page,
        )
        self.assertIn("->lyricsScope:Landroidx/media3/ആ;", self.patch)
        self.assertIn("->lyricsPager:Landroidx/media3/hj2;", self.patch)
        self.assertNotIn("Landroidx/media3/g70;->ޕ", self.patch)
        hi2 = self.ui_files["androidx/media3/hi2.smali"].decode()
        ii2 = self.ui_files["androidx/media3/ii2.smali"].decode()
        self.assertIn("const/4 v2, 0x6", hi2)
        self.assertIn(
            "invoke-direct {v0, v5, v4, v2}, Landroidx/media3/ii2;-><init>",
            hi2,
        )
        # Selector 6 uses a 300 ms animation and targets page 1.
        self.assertIn("const/16 v1, 0x12c", ii2)
        self.assertIn(
            "invoke-static {v6, v9, p1, p0, v3}, Landroidx/media3/hj2;->Ԯ",
            ii2,
        )

    def test_touch_swiping_is_disabled_only_for_the_player_pager(self) -> None:
        self.assertEqual(self.pager_call_before.count("const/16 v17, 0x3fec"), 1)
        self.assertEqual(self.pager_call_after.count("const/16 v17, 0x3f6c"), 1)
        self.assertEqual(0x3F6C & 0x80, 0)
        self.assertNotIn("and-int/lit16 v5, v5, 0x80", self.pager_impl_before)
        self.assertIn("and-int/lit16 v5, v5, 0x80", self.pager_impl_after)
        self.assertEqual(self.pager_impl_before.count("move/from16 v5, p7"), 1)
        self.assertEqual(self.pager_impl_after.count("move/from16 v5, p7"), 2)

    def test_main_activity_routes_touch_events_without_consuming_them(self) -> None:
        self.assertIn(
            "LocalUiPatch;->handlePlayerTouch(Lcom/salt/music/ui/MainActivity;Landroid/view/MotionEvent;)V",
            self.activity,
        )
        self.assertIn(
            "invoke-super {p0, p1}, Landroidx/media3/ȕ;->dispatchTouchEvent(Landroid/view/MotionEvent;)Z",
            self.activity,
        )

    def test_swipes_reuse_directional_track_animation(self) -> None:
        self.assertIn("const/high16 v5, 0x42800000    # 64.0f", self.patch)
        self.assertIn("const v4, 0x3fa00000    # 1.25f", self.patch)
        self.assertIn("const-wide/16 v10, 0x320", self.patch)
        self.assertIn("const-wide/16 v6, 0x12c", self.patch)
        self.assertIn("->getSeeking()Z", self.patch)
        self.assertIn("->setPlayerTopAnimRight(Z)V", self.patch)
        self.assertIn("->playPrevious()V", self.patch)
        self.assertIn("->playNext()V", self.patch)

    def test_swipe_direction_and_guards(self) -> None:
        self.assertEqual(modeled_swipe(-120, 5, 250), "next")
        self.assertEqual(modeled_swipe(120, 5, 250), "previous")
        self.assertIsNone(modeled_swipe(50, 0, 250))
        self.assertIsNone(modeled_swipe(120, 110, 250))
        self.assertIsNone(modeled_swipe(-120, 5, 900))
        self.assertIsNone(modeled_swipe(-120, 5, 250, page=2))
        self.assertIsNone(modeled_swipe(-120, 5, 250, seeking=True))
        self.assertIsNone(
            modeled_swipe(-120, 5, 250, elapsed_since_action_ms=300)
        )

    def test_only_primary_dex_and_signing_metadata_change_in_apk(self) -> None:
        allowed = {"classes.dex"} | SIGNATURE_ENTRIES
        with zipfile.ZipFile(BASE_APK) as before, zipfile.ZipFile(UI_APK) as after:
            self.assertEqual(set(before.namelist()), set(after.namelist()))
            changed = {
                name for name in before.namelist()
                if before.read(name) != after.read(name)
            }
            self.assertEqual(changed, allowed)
            self.assertIsNone(after.testzip())

    def test_dex_is_valid_and_below_reference_limit(self) -> None:
        with zipfile.ZipFile(BASE_APK) as before, zipfile.ZipFile(UI_APK) as after:
            baseline_dex = before.read("classes.dex")
            dex = after.read("classes.dex")
        self.assertEqual(dex[:8], baseline_dex[:8])
        self.assertLess(struct.unpack_from("<I", dex, 0x58)[0], 65536)

    def test_signing_key_and_native_startup_fix_are_preserved(self) -> None:
        certificate = apk_certificate(UI_APK)
        self.assertEqual(apk_certificate(BASE_APK), certificate)
        with zipfile.ZipFile(UI_APK) as archive:
            self.assertEqual(
                native_certificate_hash(archive.read(LIBRARY_ENTRY)),
                signature_hash(certificate),
            )


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(
            "Usage: test_ui_changes.py BASE_APK UI_APK BASE_SMALI UI_SMALI"
        )
    BASE_APK, UI_APK, BASE_SMALI, UI_SMALI = map(Path, sys.argv[1:])
    unittest.main(argv=[sys.argv[0]], verbosity=2)

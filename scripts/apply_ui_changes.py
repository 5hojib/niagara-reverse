#!/usr/bin/env python3
"""Apply the player/lyrics UI patch to this exact local-features DEX.

Expected input is a full baksmali disassembly of classes.dex from
SaltPlayer-12.6.0-2026110201-en-local-features-signed.apk.
"""

import argparse
import hashlib
import re
from pathlib import Path


EXPECTED = {
    "androidx/media3/ch1.smali": {
        "cdc3705f79455aa59c9562b7680af4b5b4897fa3c6d17671eef816e38922d5f7",
        "e7a00ea65da854454ab0c2656dddef61bc5e8b4da31d4e4a315dd0743cade2ee",
    },
    "androidx/media3/s92.smali": {
        "036c50bcfd1865ee9c2dfb0481c1ec1f5dc108a9406ed14328a974542a5c200d",
        "f168cc34b1aa691b8d5accdd5629fa02f8b468df195ac73670fa5bfc3388d871",
    },
    "androidx/media3/ut2.smali": {
        "21eb12c5a53aed5f4928f65ce810cffb31b39160199d02c94e70416219b51bc2",
        "f6ea639975b3d996450081ca26b4e0570294d45d9a0684c7d44fb2ccc9ba1295",
    },
    "androidx/media3/wt2.smali": {
        "641b850bcbdab3b98241a2f5ce24ff04080d5fda9665347e84ccab84cfdd9ce8",
    },
    "com/salt/music/ui/MainActivity.smali": {
        "1353d6017effdd35146cee10f7d29ab768d9cfa18e69e0848215d28a37cc48d4",
        "5dcfa1b67e927ceb96ab0ea7ad740a4cb9f1bbad415a0962e4f983d278effb80",
    },
}

PATCH_CLASS = r'''.class public final Lcom/salt/music/ui/patch/LocalUiPatch;
.super Ljava/lang/Object;
.source "LocalUiPatch.java"


# static fields
.field private static lastSwipeTime:J

.field private static lyricsPager:Landroidx/media3/hj2;

.field private static lyricsScope:Landroidx/media3/ആ;

.field private static swipeActive:Z

.field private static swipeDownTime:J

.field private static swipeDownX:F

.field private static swipeDownY:F


# direct methods
.method private constructor <init>()V
    .registers 1

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method private static currentPlayerPage(Lcom/salt/music/ui/MainActivity;)I
    .registers 2

    iget-object v0, p0, Lcom/salt/music/ui/MainActivity;->ޱ:Landroidx/media3/b2;

    if-eqz v0, :missing

    iget-object v0, v0, Landroidx/media3/hj2;->ފ:Ljava/lang/Object;

    if-eqz v0, :missing

    check-cast v0, Landroidx/media3/vi2;

    iget-object v0, v0, Landroidx/media3/vi2;->ԭ:Ljava/lang/Object;

    if-eqz v0, :missing

    check-cast v0, Landroidx/media3/al2;

    invoke-virtual {v0}, Landroidx/media3/al2;->ԭ()I

    move-result v0

    return v0

    :missing
    const/4 v0, -0x1

    return v0
.end method

.method public static handlePlayerTouch(Lcom/salt/music/ui/MainActivity;Landroid/view/MotionEvent;)V
    .registers 14

    if-eqz p0, :return

    if-eqz p1, :return

    invoke-virtual {p1}, Landroid/view/MotionEvent;->getActionMasked()I

    move-result v0

    if-nez v0, :not_down

    invoke-static {p0}, Lcom/salt/music/ui/patch/LocalUiPatch;->currentPlayerPage(Lcom/salt/music/ui/MainActivity;)I

    move-result v0

    const/4 v1, 0x1

    if-ne v0, v1, :disable

    sput-boolean v1, Lcom/salt/music/ui/patch/LocalUiPatch;->swipeActive:Z

    invoke-virtual {p1}, Landroid/view/MotionEvent;->getX()F

    move-result v0

    sput v0, Lcom/salt/music/ui/patch/LocalUiPatch;->swipeDownX:F

    invoke-virtual {p1}, Landroid/view/MotionEvent;->getY()F

    move-result v0

    sput v0, Lcom/salt/music/ui/patch/LocalUiPatch;->swipeDownY:F

    invoke-virtual {p1}, Landroid/view/MotionEvent;->getEventTime()J

    move-result-wide v8

    sput-wide v8, Lcom/salt/music/ui/patch/LocalUiPatch;->swipeDownTime:J

    return-void

    :disable
    const/4 v0, 0x0

    sput-boolean v0, Lcom/salt/music/ui/patch/LocalUiPatch;->swipeActive:Z

    return-void

    :not_down
    const/4 v1, 0x3

    if-ne v0, v1, :not_cancel

    const/4 v0, 0x0

    sput-boolean v0, Lcom/salt/music/ui/patch/LocalUiPatch;->swipeActive:Z

    return-void

    :not_cancel
    const/4 v1, 0x1

    if-ne v0, v1, :return

    sget-boolean v0, Lcom/salt/music/ui/patch/LocalUiPatch;->swipeActive:Z

    const/4 v1, 0x0

    sput-boolean v1, Lcom/salt/music/ui/patch/LocalUiPatch;->swipeActive:Z

    if-eqz v0, :return

    invoke-static {p0}, Lcom/salt/music/ui/patch/LocalUiPatch;->currentPlayerPage(Lcom/salt/music/ui/MainActivity;)I

    move-result v0

    const/4 v1, 0x1

    if-ne v0, v1, :return

    invoke-virtual {p1}, Landroid/view/MotionEvent;->getEventTime()J

    move-result-wide v8

    sget-wide v10, Lcom/salt/music/ui/patch/LocalUiPatch;->swipeDownTime:J

    sub-long/2addr v8, v10

    const-wide/16 v10, 0x0

    cmp-long v0, v8, v10

    if-ltz v0, :return

    const-wide/16 v10, 0x320

    cmp-long v0, v8, v10

    if-gtz v0, :return

    invoke-virtual {p1}, Landroid/view/MotionEvent;->getX()F

    move-result v0

    sget v1, Lcom/salt/music/ui/patch/LocalUiPatch;->swipeDownX:F

    sub-float/2addr v0, v1

    invoke-virtual {p1}, Landroid/view/MotionEvent;->getY()F

    move-result v1

    sget v2, Lcom/salt/music/ui/patch/LocalUiPatch;->swipeDownY:F

    sub-float/2addr v1, v2

    invoke-static {v0}, Ljava/lang/Math;->abs(F)F

    move-result v2

    invoke-static {v1}, Ljava/lang/Math;->abs(F)F

    move-result v3

    invoke-virtual {p0}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;

    move-result-object v4

    invoke-virtual {v4}, Landroid/content/res/Resources;->getDisplayMetrics()Landroid/util/DisplayMetrics;

    move-result-object v4

    iget v4, v4, Landroid/util/DisplayMetrics;->density:F

    const/high16 v5, 0x42800000    # 64.0f

    mul-float/2addr v4, v5

    cmpg-float v5, v2, v4

    if-lez v5, :return

    const v4, 0x3fa00000    # 1.25f

    mul-float/2addr v3, v4

    cmpl-float v4, v2, v3

    if-lez v4, :return

    invoke-virtual {p0}, Lcom/salt/music/ui/MainActivity;->ޑ()Lcom/salt/music/ui/player/viewmodel/PlayerViewModel;

    move-result-object v4

    invoke-virtual {v4}, Lcom/salt/music/ui/player/viewmodel/PlayerViewModel;->getSeeking()Z

    move-result v5

    if-nez v5, :return

    invoke-static {}, Landroid/os/SystemClock;->uptimeMillis()J

    move-result-wide v8

    sget-wide v10, Lcom/salt/music/ui/patch/LocalUiPatch;->lastSwipeTime:J

    sub-long/2addr v10, v8

    neg-long v10, v10

    const-wide/16 v6, 0x12c

    cmp-long v5, v10, v6

    if-lez v5, :return

    sput-wide v8, Lcom/salt/music/ui/patch/LocalUiPatch;->lastSwipeTime:J

    const/4 v5, 0x0

    cmpg-float v5, v0, v5

    if-ltz v5, :next

    const/4 v5, 0x0

    invoke-virtual {v4, v5}, Lcom/salt/music/ui/player/viewmodel/PlayerViewModel;->setPlayerTopAnimRight(Z)V

    invoke-virtual {v4}, Lcom/salt/music/ui/player/viewmodel/PlayerViewModel;->playPrevious()V

    return-void

    :next
    const/4 v5, 0x1

    invoke-virtual {v4, v5}, Lcom/salt/music/ui/player/viewmodel/PlayerViewModel;->setPlayerTopAnimRight(Z)V

    invoke-virtual {v4}, Lcom/salt/music/ui/player/viewmodel/PlayerViewModel;->playNext()V

    :return
    return-void
.end method

.method public static setLyricsNavigation(Landroidx/media3/ആ;Landroidx/media3/hj2;)V
    .registers 2

    sput-object p0, Lcom/salt/music/ui/patch/LocalUiPatch;->lyricsScope:Landroidx/media3/ആ;

    sput-object p1, Lcom/salt/music/ui/patch/LocalUiPatch;->lyricsPager:Landroidx/media3/hj2;

    return-void
.end method

.method public static renderLyricsBack(Landroidx/media3/r50;)V
    .registers 6

    sget-object v1, Lcom/salt/music/ui/patch/LocalUiPatch;->lyricsPager:Landroidx/media3/hj2;

    if-eqz v1, :return

    sget-object v2, Lcom/salt/music/ui/patch/LocalUiPatch;->lyricsScope:Landroidx/media3/ആ;

    if-eqz v2, :return

    new-instance v3, Landroidx/media3/hi2;

    const/4 v4, 0x6

    invoke-direct {v3, v2, v1, v4}, Landroidx/media3/hi2;-><init>(Landroidx/media3/ആ;Landroidx/media3/hj2;I)V

    const v0, 0x7f1200a1

    invoke-static {v0, p0}, Landroidx/media3/ps3;->ގ(ILandroidx/media3/r50;)Ljava/lang/String;

    move-result-object v1

    const v0, 0x7f0800fa

    const/4 v2, 0x0

    invoke-static {v0, v1, v3, p0, v2}, Landroidx/media3/sl1;->ތ(ILjava/lang/String;Landroidx/media3/d40;Landroidx/media3/r50;I)V

    :return
    return-void
.end method
'''

DISPATCH_METHOD = r'''
.method public dispatchTouchEvent(Landroid/view/MotionEvent;)Z
    .registers 3

    invoke-static {p0, p1}, Lcom/salt/music/ui/patch/LocalUiPatch;->handlePlayerTouch(Lcom/salt/music/ui/MainActivity;Landroid/view/MotionEvent;)V

    invoke-super {p0, p1}, Landroidx/media3/ȕ;->dispatchTouchEvent(Landroid/view/MotionEvent;)Z

    move-result v0

    return v0
.end method

'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"Expected one patch anchor, found {text.count(old)}: {old!r}")
    return text.replace(old, new, 1)


def patch_tree(root: Path) -> None:
    for relative, expected in EXPECTED.items():
        path = root / relative
        if not path.is_file() or digest(path) not in expected:
            raise ValueError(f"Unexpected baseline; refusing to patch {path}")

    patch_path = root / "com/salt/music/ui/patch/LocalUiPatch.smali"
    if patch_path.exists():
        raise ValueError(f"Patch class already exists: {patch_path}")

    ch1 = root / "androidx/media3/ch1.smali"
    text = ch1.read_text()
    pattern = re.compile(
        r"(    invoke-static \{v4, v1, v2, v11, v12\}, "
        r"Landroidx/media3/ch1;->ԩ\(Landroidx/media3/ht1;JLandroidx/media3/r50;I\)V\n)"
        r".*?"
        r"(    invoke-virtual \{v11, v3\}, Landroidx/media3/r50;->ށ\(Z\)V)",
        re.S,
    )
    replacement = r"\1\n\2"
    text, count = pattern.subn(replacement, text, count=1)
    if count != 1 or "Landroidx/media3/sg1;->Ϳ()Ljava/lang/String;" in text:
        raise ValueError("Could not isolate/remove the lyrics-source tag")
    text = replace_once(
        text,
        "    invoke-static/range {p0 .. p6}, Landroidx/media3/wr0;->֏(Landroidx/media3/ht1;ZZZFLandroidx/media3/r50;I)V",
        "    invoke-static/range {p0 .. p6}, Landroidx/media3/wr0;->֏(Landroidx/media3/ht1;ZZZFLandroidx/media3/r50;I)V\n\n"
        "    invoke-static/range {p6 .. p6}, Lcom/salt/music/ui/patch/LocalUiPatch;->renderLyricsBack(Landroidx/media3/r50;)V",
    )
    ch1.write_text(text)

    pager = root / "androidx/media3/ut2.smali"
    text = replace_once(
        pager.read_text(),
        "    const/16 v17, 0x3fec",
        "    const/16 v17, 0x3f6c",
    )
    pager.write_text(text)

    pager_impl = root / "androidx/media3/s92.smali"
    text = replace_once(
        pager_impl.read_text(),
        "    move v5, v6\n\n    .line 169",
        "    move/from16 v5, p14\n\n"
        "    and-int/lit16 v5, v5, 0x80\n\n"
        "    if-nez v5, :local_ui_scroll_default\n\n"
        "    move/from16 v5, p7\n\n"
        "    goto :local_ui_scroll_ready\n\n"
        "    :local_ui_scroll_default\n"
        "    move v5, v6\n\n"
        "    :local_ui_scroll_ready\n"
        "    .line 169",
    )
    pager_impl.write_text(text)

    lyrics_page = root / "androidx/media3/wt2.smali"
    text = lyrics_page.read_text()
    pattern = re.compile(
        r"(    const v2, 0x513394f8\n.*?"
        r"    invoke-virtual \{v13, v2\}, Landroidx/media3/r50;->ޢ\(I\)V\n)",
        re.S,
    )
    replacement = (
        r"\1\n"
        r"    iget-object v2, v0, Landroidx/media3/wt2;->ֈ:Landroidx/media3/ആ;\n\n"
        r"    iget-object v3, v0, Landroidx/media3/wt2;->ԯ:Landroidx/media3/hj2;\n\n"
        r"    invoke-static {v2, v3}, Lcom/salt/music/ui/patch/LocalUiPatch;->setLyricsNavigation(Landroidx/media3/ആ;Landroidx/media3/hj2;)V\n"
    )
    text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise ValueError("Could not inject the lyrics navigation context")
    lyrics_page.write_text(text)

    activity = root / "com/salt/music/ui/MainActivity.smali"
    text = replace_once(
        activity.read_text(),
        "# virtual methods\n",
        "# virtual methods\n" + DISPATCH_METHOD,
    )
    activity.write_text(text)

    patch_path.parent.mkdir(parents=True, exist_ok=True)
    patch_path.write_text(PATCH_CLASS)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("smali_root", type=Path)
    args = parser.parse_args()
    patch_tree(args.smali_root)
    print(f"Applied player/lyrics UI patch: {args.smali_root}")


if __name__ == "__main__":
    main()

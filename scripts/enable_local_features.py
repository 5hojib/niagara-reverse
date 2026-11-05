#!/usr/bin/env python3
"""Enable the bundled Pro/Audiophile options in this exact translated build.

Only local configuration flags are changed. Purchase APIs, receipts, server
credentials, feature settings, and Android permission checks are untouched.
"""

import argparse
import hashlib
from pathlib import Path


BASELINE_SHA256 = "7ef3796d0086751b65b5e220d9418a030f884311eccbee79f9117e593e54e9ec"
CONFIG_CLASS = "Landroidx/media3/ཌྷ;"
HELPER_NAME = "enableLocalFeatureDefaults"
HELPER = """.method private static enableLocalFeatureDefaults()V
    .registers 3

    invoke-static {}, Lcom/salt/music/App$Companion;->Ԫ()Lcom/tencent/mmkv/MMKV;
    move-result-object v0

    const/4 v1, 0x1

    sget-object v2, Landroidx/media3/თ;->Ԫ:Ljava/lang/String;
    invoke-virtual {v0, v2, v1}, Lcom/tencent/mmkv/MMKV;->ށ(Ljava/lang/String;Z)V

    sget-object v2, Landroidx/media3/თ;->ԫ:Ljava/lang/String;
    invoke-virtual {v0, v2, v1}, Lcom/tencent/mmkv/MMKV;->ށ(Ljava/lang/String;Z)V

    const-string v2, "audiophile_pack"
    invoke-virtual {v0, v2, v1}, Lcom/tencent/mmkv/MMKV;->ށ(Ljava/lang/String;Z)V

    return-void
.end method

"""


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"Expected one patch anchor: {old!r}")
    return text.replace(old, new, 1)


def enable_local_features(original):
    if hashlib.sha256(original).hexdigest() != BASELINE_SHA256:
        raise ValueError("Unexpected AppConfig baseline; refusing to patch another build")
    text = original.decode("utf-8")
    anchor = "    sget-object v0, Landroidx/media3/თ;->Ԫ:Ljava/lang/String;"
    text = replace_once(
        text, anchor,
        f"    invoke-static {{}}, {CONFIG_CLASS}->{HELPER_NAME}()V\n\n" + anchor,
    )
    text = replace_once(text, ".method public static Ϳ()V", HELPER + ".method public static Ϳ()V")
    # Preserve the original setters and their reactive-state updates. Clamp the
    # three availability flags on instead of faking a billing response.
    for name, registers in (("ނ", 5), ("ރ", 4), ("އ", 4)):
        anchor = f".method public static {name}(Z)V\n    .registers {registers}\n"
        text = replace_once(text, anchor, anchor + "\n    const/4 p0, 0x1\n")
    return text.encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_config", type=Path)
    parser.add_argument("output_config", type=Path)
    args = parser.parse_args()
    if args.output_config.exists():
        parser.error("Output already exists; choose a new path")
    args.output_config.write_bytes(enable_local_features(args.original_config.read_bytes()))
    print(f"Patched local availability defaults: {args.output_config}")


if __name__ == "__main__":
    main()

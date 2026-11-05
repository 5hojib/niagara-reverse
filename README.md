# Salt Player 12.6.0 — English build

English-localized rebuild of Salt Player (`com.salt.music`), based on:

- Original APK: `12.6.0-2026110201-official-arm64-v8a.apk`
- SHA-256: `2af308707dfa0563d7494fde20ce6943f96adeba5b152ba06d9ac19630f80283`

## Artifact

| File | Notes |
| --- | --- |
| `SaltPlayer-12.6.0-2026110201-en-signed.apk` | Rebuilt, zipaligned, signed APK |
| `salt.keystore` | Signing key for this and future rebuilds (alias `salt`, store/key password `saltpass`) |

Signed SHA-256: `a27b1fbd4537b7cfa31e9fcae94349ea34a9e77112f9e2b3d20b9ccaf15ecce6`

## What changed

- Replaced all Chinese UI/format strings in `resources.arsc` with English
  (official upstream translations where available, manual translations otherwise).
- Rewrote hardcoded Chinese string literals inside `classes.dex`, `classes2.dex`,
  and `classes3.dex`.
- Removed the `zh` resource/config locale directories so Chinese locales fall back
  to the default English resources.
- Replaced Chinese legal text under `assets/src/zh-CN/` with English.
- Cleaned Chinese values out of the `values-ug` (Uyghur) resource set, which
  previously contained untranslated Chinese.

Preserved as-is: Japanese song titles, the Japanese language label, and three
non-text binary blobs that merely contain CJK byte sequences.

## Verification

- `apksigner verify`: v2 and v3 signatures valid.
- `zipalign -c -p 4`: aligned.
- Baksmali re-decodes all three DEX files without errors.
- Resource and DEX scans report no remaining Chinese text.

## Rebuild summary

1. `apktool d -s` decode.
2. Merge/translate `res/values*/strings.xml` (566 keys from upstream + 351 manual).
3. Patch 347 hardcoded DEX literals via baksmali/smali (smali 3.0.9).
4. Rebuild with apktool 2.11.1, `zipalign -p 4`, `apksigner` (v1 disabled, v2/v3 enabled).

## Install note

The APK is signed with a new key, so it will not upgrade an existing official
installation. Uninstall the official app first (this clears app data).

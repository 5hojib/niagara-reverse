# Salt Player 12.6.0 — English build

English-localized rebuild of Salt Player (`com.salt.music`), based on:

- Original APK: `12.6.0-2026110201-official-arm64-v8a.apk`
- SHA-256: `2af308707dfa0563d7494fde20ce6943f96adeba5b152ba06d9ac19630f80283`

## Artifact

| File | Notes |
| --- | --- |
| `SaltPlayer-12.6.0-2026110201-en-signed.apk` | Rebuilt, zipaligned, signed APK |
| `salt.keystore` | Signing key for this and future rebuilds (alias `salt`, store/key password `saltpass`) |

Signed SHA-256: `6280e6e845e290a1e603f8c1c6dda1dcc49600f0aa54865a213acd921f77b5a6`

## Startup validation fix

The first English rebuild installed successfully but was rejected when opened.
`AudioConfig.getCacheVersion()` in `lib/arm64-v8a/libexp82464.so` still returned
the original certificate's Android `Signature.hashCode()` (`0xba4870d3`), while
the rebuild's certificate hash is `0x64219e6c`.

The current APK changes only the two native instructions that load that expected
value. The certificate comparison, startup checks, translated DEX files,
resources, assets, manifest, and other libraries remain unchanged. It does not
disable validation or change paid-feature logic.

It uses the same package, version code, and signing key as the previous English
build, so **install it over that build to preserve app data**. The signing key
was published with the first rebuild; treat it as a public test key, not a
private or official developer credential.

## What changed

- Translated Chinese UI/format strings in `resources.arsc` to English
  (official upstream translations where available, manual translations otherwise).
- Rewrote hardcoded Chinese string literals inside `classes.dex`, `classes2.dex`,
  and `classes3.dex`.
- Removed the `zh` resource/config locale directories so Chinese locales fall back
  to the default English resources.
- Replaced Chinese legal text under `assets/src/zh-CN/` with English.
- Cleaned Chinese values out of the `values-ug` (Uyghur) resource set, which
  previously contained untranslated Chinese.

Preserved as-is: Japanese song titles, the Japanese language label, and three
encrypted DEX string pools. Native-library text and encrypted runtime strings
were not comprehensively localized; the earlier plaintext scans did not cover
them.

## Verification

- `apksigner verify`: v2 and v3 signatures valid.
- `zipalign -c -p 4`: aligned.
- Baksmali re-decodes all three DEX files without errors.
- Earlier plaintext resource/asset and DEX scans found no untranslated Chinese
  in the scanned text, excluding the preserved Japanese text and encrypted pools.
- ARM64 regression tests execute the native hash getter with Unicorn, reproduce
  the previous certificate mismatch, and confirm the fixed getter matches the
  rebuild certificate while differing from other certificates.
- Archive-content checks confirm only the validation library and signing metadata
  changed from the previous English APK.

**Limit:** no full Android install/launch test was performed on a device or
Android emulator. CPU emulation tests the specific native validation routine,
not the complete app lifecycle or UI.

### Reproduce the fix and tests

`scripts/fix_apk_validation.py` takes the original native library, a verified APK
signed with the rebuild key, and a new output-library path:

```sh
python3 scripts/fix_apk_validation.py libexp82464-original.so previous-english.apk libexp82464-fixed.so
```

Replace that library in the translated apktool working directory, rebuild,
zipalign, and sign with the **same** key. Then install `unicorn==2.1.4` in a Python
environment and run:

```sh
python3 scripts/test_apk_validation.py original.apk fixed-english.apk previous-english.apk
```

## Rebuild summary

1. `apktool d -s` decode.
2. Merge/translate `res/values*/strings.xml` (566 keys from upstream + 351 manual).
3. Patch 347 hardcoded DEX literals via baksmali/smali (smali 3.0.9).
4. Rebuild with apktool 2.11.1, `zipalign -p 4`, `apksigner` (v1 disabled, v2/v3 enabled).

## Install note

The APK cannot upgrade an official installation because its signing key differs.
Back up app data before uninstalling the official app. No uninstall is needed
when updating the earlier English build with this fixed APK.

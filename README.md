# Salt Player 12.6.0 — English build

English-localized rebuild of Salt Player (`com.salt.music`), based on:

- Original APK: `12.6.0-2026110201-official-arm64-v8a.apk`
- SHA-256: `2af308707dfa0563d7494fde20ce6943f96adeba5b152ba06d9ac19630f80283`

## Artifact

| File | Notes |
| --- | --- |
| `SaltPlayer-12.6.0-2026110201-en-signed.apk` | English build with normal feature availability |
| `SaltPlayer-12.6.0-2026110201-en-local-features-signed.apk` | English build with bundled Pro and Audiophile options locally available |
| `salt.keystore` | Signing key for this and future rebuilds (alias `salt`, store/key password `saltpass`) |

SHA-256:

- Standard English build: `6280e6e845e290a1e603f8c1c6dda1dcc49600f0aa54865a213acd921f77b5a6`
- Local-features build: `036ec39cd5c7167e0aa2f7c36ca3287e4ceb86f02fc3b9150b7b73911ab9e86e`

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

## Local-feature availability variant

The `en-local-features` APK initializes these three local configuration flags as
enabled before the app loads them:

- `salt_player_pro`
- `salt_player_pro_purchased_2`
- `audiophile_pack`

Their setters also clamp the values to `true`, so purchase refresh or a UI
deactivation action cannot switch the local availability flags off. This makes
the bundled Pro UI/effects and Audiophile Pack gates (including Morvanium and
USB DAC controls) locally available on fresh installs and upgrades.

This does **not** fabricate a store receipt, account, server entitlement, or
payment record, and it cannot grant access to services enforced by a remote
server. Feature settings remain under user control: Morvanium auto-mix, USB
exclusive output, reverse playback, visual effects, and similar options are
available but are not forcibly switched on. Android permissions, device support,
privacy consent, and hardware checks are also unchanged.

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
- Eight local-feature tests confirm the three availability flags initialize to
  true on fresh installs and upgrades, cannot be disabled through their setters,
  and do not alter unrelated preferences or consent values.
- Comparing the two current APKs shows that only `classes.dex` and signature
  metadata differ; resources, manifest, assets, native libraries, and the other
  DEX files are byte-identical.

**Limit:** no full Android install/launch test was performed on a device or
Android emulator. CPU emulation tests the specific native validation routine,
not the complete app lifecycle or UI.

### Reproduce the startup fix and tests

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

### Reproduce the local-feature patch and tests

After disassembling the standard translated `classes.dex`, patch its exact
`androidx/media3/ཌྷ.smali` baseline and reassemble it:

```sh
python3 scripts/enable_local_features.py AppConfig-original.smali AppConfig-patched.smali
```

Replace the class in the disassembly tree with the patched output, assemble
`classes.dex`, rebuild, zipalign, and sign with the same key. To test the rebuilt
variant (after installing `unicorn==2.1.4`):

```sh
python3 scripts/test_local_features.py \
  standard-english.apk local-features.apk \
  AppConfig-original.smali AppConfig-redecoded-from-local-features.smali
```

## Rebuild summary

1. `apktool d -s` decode.
2. Merge/translate `res/values*/strings.xml` (566 keys from upstream + 351 manual).
3. Patch 347 hardcoded DEX literals via baksmali/smali (smali 3.0.9).
4. Rebuild with apktool 2.11.1, `zipalign -p 4`, `apksigner` (v1 disabled, v2/v3 enabled).

## Install note

The APK cannot upgrade an official installation because its signing key differs.
Back up app data before uninstalling the official app. No uninstall is needed
when switching between these English builds because they use the same package,
version code, and signing key.

# Sugarcane 12.6.0

English-localized and Sugarcane-branded rebuild of Salt Player, based on:

- Original APK: `12.6.0-2026110201-official-arm64-v8a.apk`
- SHA-256: `2af308707dfa0563d7494fde20ce6943f96adeba5b152ba06d9ac19630f80283`

## Downloads

APK binaries are published in the
[v12.6.0-stable release](https://github.com/5hojib/sugarcane/releases/tag/v12.6.0-stable)
rather than stored on the default branch.

The package ID remains `com.salt.music`, and the public test signing key remains
unchanged, so this APK updates the previous stable English build without data
loss.

| Release asset | Notes |
| --- | --- |
| [`Sugarcane-12.6.0-2026110201-stable.apk`](https://github.com/5hojib/sugarcane/releases/download/v12.6.0-stable/Sugarcane-12.6.0-2026110201-stable.apk) | Stable build with bundled Pro and Audiophile options locally available |

SHA-256:

- Sugarcane stable build: `04a0d673e23cebbe2e29af62c25372bfc38d5ded27c68b0c07cfc5d435e0b8ee`

`salt.keystore` remains in the source tree for reproducible rebuilds (alias
`salt`, store/key password `saltpass`). Treat it as a public test key.

## Startup validation fix

The first English rebuild installed successfully but was rejected when opened.
`AudioConfig.getCacheVersion()` in `lib/arm64-v8a/libexp82464.so` still returned
the original certificate's Android `Signature.hashCode()` (`0xba4870d3`), while
the rebuild's certificate hash is `0x64219e6c`.

The startup-validation fix itself changes only the two native instructions that
load that expected value. It does not disable validation or change paid-feature
logic; the Sugarcane branding changes are documented separately below.

It uses the same package, version code, and signing key as the previous English
build, so **install it over that build to preserve app data**. The signing key
was published with the first rebuild; treat it as a public test key, not a
private or official developer credential.

## Local-feature availability

The Sugarcane APK initializes these three local configuration flags as enabled
before the app loads them:

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
- Changed the launcher/app label to **Sugarcane** in every packaged locale.
- Replaced human-facing Salt Player branding in resources, legal assets,
  hardcoded DEX strings, and native integrity text.

Preserved as-is: Japanese song titles, the Japanese language label, and three
encrypted DEX string pools. Native-library text and encrypted runtime strings
were not comprehensively localized; the earlier plaintext scans did not cover
them. Compatibility identifiers, the package ID, signing certificate, format
markers, and working upstream URLs intentionally retain their original values.

## Verification

- `apksigner verify`: v2 and v3 signatures valid.
- `zipalign -c -p 4`: aligned.
- Baksmali re-decodes all three DEX files without errors.
- Earlier plaintext resource/asset and DEX scans found no untranslated Chinese
  in the scanned text, excluding the preserved Japanese text and encrypted pools.
- ARM64 regression tests execute the native hash getter with Unicorn, reproduce
  the previous certificate mismatch, and confirm the fixed getter matches the
  rebuild certificate while differing from other certificates.
- Native regression checks confirm the certificate getter still matches the
  rebuild certificate after the branding-only native text update.
- Eight local-feature tests confirm the three availability flags initialize to
  true on fresh installs and upgrades, cannot be disabled through their setters,
  and do not alter unrelated preferences or consent values.
- Eight Sugarcane branding regression tests confirm the app label, visible-string
  replacement, unchanged package manifest and secondary DEX files, local-feature
  defaults, DEX 035 format, signing certificate, and native startup validation.

**Limit:** at the user's request, the final branding-only rebuild was not run
through another full emulator launch. Its known-good base build passed the
Android 11 startup smoke test; static APK checks and CPU emulation separately
verify the final payload and native validation routine.

## Automated APK releases

The **Release APK from URL** workflow publishes an APK without committing the
binary to the branch. Open **Actions → Release APK from URL → Run workflow** and
provide:

- an HTTPS APK URL;
- a new release tag;
- optionally, the expected SHA-256, release title, asset filename, and
  prerelease flag.

The workflow validates the URL and filename, checks that the download is a ZIP
containing `AndroidManifest.xml` and `classes.dex`, verifies the optional digest,
and uploads both the APK and `SHA256SUMS.txt` to a new GitHub Release.

Automation can also send a `repository_dispatch` event of type
`release-apk-from-url` with matching fields in `client_payload`.

### Reproduce the Sugarcane branding patch

After decoding the stable local-features APK resources and primary DEX, run:

```sh
python3 scripts/rebrand_sugarcane.py decoded-resources decoded-smali
```

Rebuild resources, assemble the primary DEX as DEX 035, package, align, and sign
with the same key. Then run `scripts/test_sugarcane_branding.py` against the base
and final artifacts.

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
Back up app data before uninstalling the official app. It updates the previous
English/local-features rebuild because the package, version code, and signing key
are unchanged.

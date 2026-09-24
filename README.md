# BL4 AutoReload

[English](README.md) | [Русский](README_RU.md)

BL4 AutoReload gets rid of the awkward pause when a magazine runs dry.

You can have the game reload automatically, or make it wait until you press Fire again on an empty magazine. Both behaviors can be used with every supported weapon or limited to Jakobs only.

The mod still uses Borderlands 4's normal reload, so animations, reload speed, perks and interruption behavior work the way they normally do.

## Available modes

### Auto Reload - All Weapons

Automatically starts a reload when the magazine of a supported weapon becomes empty.

### Auto Reload - Jakobs Only

The same behavior, limited to Jakobs weapons.

### Empty Fire Reload - All Weapons

Does not automatically reload when the last round is fired. Reload begins only when Fire is pressed again while the magazine is already empty.

### Empty Fire Reload - Jakobs Only

The same empty-fire behavior, limited to Jakobs weapons.

## Features

- Automatic reload when the magazine reaches zero.
- Optional "press Fire again to reload" behavior for empty magazines.
- Both modes can apply to all supported weapons or Jakobs only.
- Works with keyboard/mouse and gamepad.
- Follows your current Fire binding, including after remapping controls.
- Handles weapons with separate primary and secondary ammo pools.
- Uses the game's normal reload instead of faking one.

## Requirements

- Borderlands 4
- [BL4 PythonSDK / Oak2 Mod Manager](https://github.com/bl-sdk/oak2-mod-manager/releases/latest)

Use the [official BL4 SDK / Oak2 installation guide](https://bl-sdk.github.io/oak2-mod-db/) for SDK installation and updates.

## Installing the mod

1. Install or update BL4 PythonSDK / Oak2 using the official guide above.
2. Download `BL4_AutoReload.sdkmod` from [GitHub Releases](https://github.com/Last1SiN/BL4-AutoReload/releases/latest) or [Nexus Mods](https://www.nexusmods.com/borderlands4/mods/288).
3. With Borderlands 4 closed, copy the `.sdkmod` file intact to `Borderlands 4\sdk_mods\`. Do not extract the `.sdkmod` itself.
4. Start the game, open the Mods menu, enable **BL4 AutoReload** and select the desired **Behavior**.

To update BL4 AutoReload, replace the existing `.sdkmod` with the newer file and restart the game.

Do not enable older standalone `auto_reload_*` or `empty_fire_reload_*` mods at the same time as BL4 AutoReload.

## How it works

The mod uses the game's native reload request:

`ServerStartReloading(CurrentUseModeIndex, 0)`

Normal reload animation, reload speed, perk effects and standard interruption behavior are therefore preserved.

## Compatibility and license

- Co-op support: **Unknown** — behavior with the mod installed only on a client while the host does not have it has not yet been validated.
- The mod does not replace weapon animations or modify reload speed values.
- License: **GNU GPLv3 with [Section 7 additional provenance terms](ADDITIONAL_TERMS.md)**

## Credits

**Development:** Sol / GPT-5.6 Sol  
**Design, testing & QA:** Last1SiN

**BL4 PythonSDK / Oak2 Mod Manager:** created by [apple1417](https://github.com/apple1417), with contributions from the [BL-SDK](https://github.com/bl-sdk) project and contributors.

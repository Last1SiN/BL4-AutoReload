# BL4 AutoReload

**Borderlands 4 PythonSDK / Oak2 mod**

Current release: **v1.1.1**

> Installation-ready `.sdkmod` files are published under **Releases**.  
> The files in this repository are the mod source.

---

Skip reload delay with a single Borderlands 4 mod with four selectable native reload behaviors.

## Modes

Open the mod settings and select a **Behavior**:

- **Auto Reload - All Weapons** — immediately starts the native reload when any supported weapon magazine reaches 0.
- **Auto Reload - Jakobs Only** — same behavior, but only for Jakobs weapons.
- **Empty Fire Reload - All Weapons** — reload starts only when **Fire** is pressed while the magazine is already empty.
- **Empty Fire Reload - Jakobs Only** — same behavior, but only for Jakobs weapons.

The selected mode is saved between launches and can be changed while the mod is enabled.

## What's new in 1.1.1

Fixed Auto Reload behavior for weapons with separate primary and secondary fire ammo pools.

Some multi-fire-mode weapons can keep an exhausted secondary ammo pool after automatically switching back to primary fire. AutoReload now follows the weapon's active `CurrentUseModeIndex` and selects the matching ammo pool instead of assuming the first ammo pool belongs to the active mode.

Stale ammo replication from an inactive fire mode is also ignored.

This prevents the primary fire mode from incorrectly reloading after individual shots following an exhausted secondary/underbarrel fire mode.

## Action_Fire and remapping

The **Empty Fire Reload** modes do not hardcode Left Mouse Button.

The mod reads the current `Action_Fire` mappings from Enhanced Input and automatically binds to the active keyboard/mouse and gamepad keys.

When controls are remapped, `Action_Fire` is automatically refreshed through `OnControlMappingsRebuilt`; no game restart or manual weapon switch is required. Mappings are also refreshed on gameplay load/equip and weapon changes as fallbacks.

## Requirements

- Borderlands 4.
- [BL4 PythonSDK / Oak2 Mod Manager v0.3+ — latest stable release](https://github.com/bl-sdk/oak2-mod-manager/releases/latest).
- [Official BL4 SDK installation guide](https://bl-sdk.github.io/oak2-mod-db/).

Oak2 Mod Manager v0.3 already bundles the required **Mods Base 1.12**, **Console Mod Menu 1.6**, and **Keybinds 1.1** components. They do not need to be downloaded separately when using that release or a newer compatible Oak2 release.

## Installation

1. **Fully close Borderlands 4.**
2. If BL4 PythonSDK / Oak2 is not installed, or you want to update it, download the [latest stable Oak2 Mod Manager release](https://github.com/bl-sdk/oak2-mod-manager/releases/latest). Extract the SDK release directly into the **Borderlands 4 game folder** (the folder containing `OakGame`) and allow folders/files to merge. For the complete SDK procedure, including Proton/Linux notes, use the [official BL4 SDK installation guide](https://bl-sdk.github.io/oak2-mod-db/).
3. Start Borderlands 4 once after installing/updating the SDK. Press `~` twice to open the SDK console, type `mods`, and verify that the Mod Menu opens.
4. Download the latest **BL4 AutoReload** release from [GitHub Releases](https://github.com/Last1SiN/BL4-AutoReload/releases/latest) or [Nexus Mods](https://www.nexusmods.com/borderlands4/mods/288).
5. Fully close the game again and copy `BL4_AutoReload.sdkmod` **without extracting it** to:

   `Borderlands 4\sdk_mods\`

6. Start/restart Borderlands 4. Press `~` twice, type `mods`, open **BL4 AutoReload**, and enable the mod.
7. Open the mod settings and select the desired **Behavior**.

To update BL4 AutoReload, replace the existing `BL4_AutoReload.sdkmod` with the newer file and restart the game.

Do not enable older standalone `auto_reload_*` or `empty_fire_reload_*` mods at the same time.

## How it works

The mod uses the game's native reload request:

`ServerStartReloading(CurrentUseModeIndex, 0)`

Normal reload animation, reload speed, perk effects, and standard interruption behavior are therefore preserved.

In Empty Fire modes, Fire spam while a reload is already running does not restart the reload.

## Compatibility and license

- Co-op support: **ClientSide** — tested with the mod installed only on the local player while other co-op players did not have AutoReload installed.
- License: **GPL-3.0**

## Credits

- **Development:** Sol / GPT-5.6 Sol
- **Design, testing & QA:** Last1SiN
- **BL4 PythonSDK / Oak2 Mod Manager:** created by [apple1417](https://github.com/apple1417), with contributions from the [BL-SDK](https://github.com/bl-sdk) project and contributors.

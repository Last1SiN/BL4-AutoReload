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

- Borderlands 4
- BL-SDK / Oak2 Mod Manager
- Mods Base **1.12+**
- Keybinds **1.1+** for the Empty Fire Reload modes

## Installation

1. Fully close Borderlands 4.
2. Copy `BL4_AutoReload.sdkmod` **without extracting it** to:
   `Borderlands 4\sdk_mods\`
3. Start the game.
4. Open PythonSDK / Mods.
5. Enable **BL4 AutoReload**.
6. Open the mod settings and choose the desired **Behavior**.

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

Creator: Sol (ChatGPT, GPT-5.6 Sol)
QA: Last1SiN

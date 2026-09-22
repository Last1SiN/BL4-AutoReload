from __future__ import annotations

from typing import Any

from mods_base import (
    DropdownOption,
    EInputEvent,
    HookType,
    build_mod,
    get_pc,
    hook,
    keybind,
)
from unrealsdk.hooks import Type

__author__ = "Sol / GPT-5.6 Sol"

MODE_AUTO_ALL = "Auto Reload - All Weapons"
MODE_AUTO_JAKOBS = "Auto Reload - Jakobs Only"
MODE_EMPTY_ALL = "Empty Fire Reload - All Weapons"
MODE_EMPTY_JAKOBS = "Empty Fire Reload - Jakobs Only"

AUTO_MODES = (MODE_AUTO_ALL, MODE_AUTO_JAKOBS)
EMPTY_MODES = (MODE_EMPTY_ALL, MODE_EMPTY_JAKOBS)
JAKOBS_MODES = (MODE_AUTO_JAKOBS, MODE_EMPTY_JAKOBS)


_pending: set[int] = set()

_mapping_rebuild_hook: HookType | None = None
_mapping_rebuild_path: str | None = None


def _addr(obj: Any) -> int:
    try:
        return int(obj._get_address())
    except Exception:
        return id(obj)


def _pc():
    try:
        return get_pc(possibly_loading=True)
    except Exception:
        return None


def _char():
    p = _pc()
    if p is None:
        return None
    try:
        return p.OakCharacter
    except Exception:
        return None


def _weapon():
    """Return the first weapon in the character's active weapon slots."""
    c = _char()
    if c is None:
        return None
    try:
        for slot in c.ActiveWeapons.Slots:
            if slot.Weapon:
                return slot.Weapon
    except Exception:
        return None
    return None


def _active_weapon():
    """Return the active weapon, falling back to the first populated slot."""
    c = _char()
    if c is None:
        return None

    fallback = None

    try:
        for slot in c.ActiveWeapons.Slots:
            w = slot.Weapon
            if not w:
                continue

            if fallback is None:
                fallback = w

            try:
                state = str(w.CurrentState)
            except Exception:
                state = ""

            if state in ("Active", "Using", "Firing", "Reloading"):
                return w
    except Exception:
        pass

    return fallback


def _behavior_use_mode_index(behavior):
    """Resolve BL4 behavior names such as UM0_5B / UM1_5B to a use-mode index."""
    try:
        name = str(behavior.Name)
    except Exception:
        return None

    if not name.startswith("UM"):
        return None

    digits = []
    for ch in name[2:]:
        if not ch.isdigit():
            break
        digits.append(ch)

    if not digits:
        return None

    try:
        return int("".join(digits))
    except Exception:
        return None


def _ammo_pool(w, use_mode=None):
    """
    Return the AmmoPool belonging to the requested/current use mode.

    Multi-mode weapons can have separate UM0/UM1 pools. Choosing the first pool
    can leave an exhausted secondary pool associated with the primary mode.
    """
    if w is None:
        return None

    if use_mode is None:
        try:
            use_mode = int(w.CurrentUseModeIndex)
        except Exception:
            use_mode = None

    try:
        behaviors = list(w.behaviors)
    except Exception:
        return None

    pools = []

    for b in behaviors:
        try:
            is_pool = str(b.Class.Name) == "WeaponBehavior_AmmoPool"
        except Exception:
            is_pool = False

        if not is_pool:
            try:
                is_pool = "WeaponBehavior_AmmoPool" in repr(b)
            except Exception:
                is_pool = False

        if not is_pool:
            continue

        pools.append(b)

        if use_mode is not None and _behavior_use_mode_index(b) == use_mode:
            return b

    if len(pools) == 1:
        return pools[0]

    return None


def _loaded(w):
    p = _ammo_pool(w)
    if p is None:
        return None
    try:
        return int(p.LoadedAmmo)
    except Exception:
        return None


def _has_magazine(w) -> bool:
    p = _ammo_pool(w)
    if p is None:
        return False

    try:
        value = p.MaxLoadedAmmo
        try:
            value = int(value.Value)
        except Exception:
            value = int(value)
        return value > 0
    except Exception:
        return False


def _has_native_reload_behavior(w) -> bool:
    """Return True only when the weapon exposes a native reload behavior.

    Some non-reloadable weapon types, including Ordnance/HeavyWeaponGadget,
    expose an AmmoPool and ServerStartReloading() even though their ammunition
    is governed by a cooldown/recharge path. Calling the reload RPC on those
    weapons can refill the pool immediately, bypassing the intended cooldown.
    """
    if w is None:
        return False

    try:
        behaviors = list(w.behaviors)
    except Exception:
        return False

    for behavior_obj in behaviors:
        try:
            class_name = str(behavior_obj.Class.Name)
        except Exception:
            class_name = ""

        try:
            name = str(behavior_obj.Name)
        except Exception:
            name = ""

        if "reload" in f"{class_name} {name}".lower():
            return True

    return False


def _state(w) -> str:
    try:
        return str(w.CurrentState)
    except Exception:
        return ""


def _is_jakobs(w) -> bool:
    """Identify Jakobs from the weapon's native ManufacturerMod enum."""
    if w is None:
        return False

    try:
        manufacturer_mod = w.ManufacturerMod
    except Exception:
        return False

    try:
        name = manufacturer_mod.name
    except Exception:
        try:
            name = str(manufacturer_mod).rsplit(".", 1)[-1]
        except Exception:
            return False

    return str(name).casefold().startswith("jakobs")


def _mode() -> str:
    return behavior.value


def _is_auto_mode() -> bool:
    return _mode() in AUTO_MODES


def _is_empty_mode() -> bool:
    return _mode() in EMPTY_MODES


def _mode_allows_weapon(w) -> bool:
    if w is None:
        return False
    if _mode() in JAKOBS_MODES:
        return _is_jakobs(w)
    return True


def _is_weapon_fire_feedback(args: Any) -> bool:
    """Match the native BL4 weapon-fire feedback GameData handle."""
    try:
        return str(args.data._name).startswith("FBData_WeaponFire_")
    except Exception:
        return False


def _request_reload(w) -> bool:
    if (
        w is None
        or not _mode_allows_weapon(w)
        or not _has_magazine(w)
        or not _has_native_reload_behavior(w)
    ):
        return False

    current = _loaded(w)
    if current is None or current > 0:
        _pending.discard(_addr(w))
        return False

    state = _state(w)
    if state == "Reloading":
        return False
    if state in ("Inactive", "Equipping", "PuttingDown"):
        return False

    key = _addr(w)
    if key in _pending:
        return False

    try:
        use_mode = int(w.CurrentUseModeIndex)
    except Exception:
        return False

    _pending.add(key)
    try:
        w.ServerStartReloading(use_mode, 0)
    except Exception:
        _pending.discard(key)
        return False

    after = _state(w)
    if after != "Reloading":
        _pending.discard(key)
        return False
    return True


# --------------------------------------------------------------------------------------
# Mode option
# --------------------------------------------------------------------------------------

def _on_behavior_change(option, new_value: str) -> None:
    _pending.clear()

    if new_value in EMPTY_MODES:
        _refresh_fire_keys()
        _ensure_mapping_rebuild_hook()


behavior = DropdownOption(
    identifier="behavior",
    value=MODE_AUTO_ALL,
    choices=[
        MODE_AUTO_ALL,
        MODE_AUTO_JAKOBS,
        MODE_EMPTY_ALL,
        MODE_EMPTY_JAKOBS,
    ],
    display_name="Behavior",
    description=(
        "Select one of four reload behaviors. The selected mode is saved between launches."
    ),
    on_change_while_enabled=_on_behavior_change,
)


# --------------------------------------------------------------------------------------
# Auto Reload path
# --------------------------------------------------------------------------------------

@hook(
    "/Script/GbxGame.GbxPlayerController:Client_PlayGbxFeedback",
    Type.PRE,
)
def _weapon_fire_feedback(obj, args, ret, func):
    if not _is_auto_mode():
        return

    if obj != _pc() or not _is_weapon_fire_feedback(args):
        return

    w = _weapon()
    if w is None or not _mode_allows_weapon(w):
        return

    current = _loaded(w)
    if current is None:
        return

    if current == 0:
        _request_reload(w)


@hook(
    "/Script/OakGame.WeaponBehavior_AmmoPool:OnRep_ServerSyncedLoadedAmmo",
    Type.POST,
)
def _ammo_rep_fallback(obj, args, ret, func):
    if not _is_auto_mode():
        return

    try:
        w = obj.Outer
    except Exception:
        return

    try:
        current_use_mode = int(w.CurrentUseModeIndex)
    except Exception:
        current_use_mode = None

    pool_use_mode = _behavior_use_mode_index(obj)

    if (
        current_use_mode is not None
        and pool_use_mode is not None
        and pool_use_mode != current_use_mode
    ):
        return

    _request_reload(w)


@hook(
    "/Game/PlayerCharacters/_Shared/WeaponAnimation/Shotgun/Jakobs/Tricks/"
    "ATrick_JAK_SG_Fire.ATrick_JAK_SG_Fire_Script_Const_C:OnBegin_Mut",
    Type.PRE,
)
def _jakobs_shotgun_fast_path(obj, args, ret, func):
    # Preserve the exact proven fast path only for the Jakobs-only auto mode.
    if _mode() != MODE_AUTO_JAKOBS:
        return

    c = _char()
    if c is None:
        return

    try:
        if args.Actor != c:
            return
    except Exception:
        return

    w = _weapon()
    if w is None:
        return

    if _loaded(w) == 0:
        _request_reload(w)


# --------------------------------------------------------------------------------------
# Empty Fire path
# --------------------------------------------------------------------------------------

def _request_reload_from_fire_press() -> None:
    if not _is_empty_mode():
        return

    w = _active_weapon()
    if w is None or not _mode_allows_weapon(w) or not _has_magazine(w):
        return

    state = _state(w)

    # Explicit anti-spam guard: never restart/interfere with an active reload.
    if state == "Reloading":
        return

    if state in ("Inactive", "Equipping", "PuttingDown"):
        return

    loaded = _loaded(w)

    # This callback happens on the resolved Action_Fire key press, before the game's
    # Fire action consumes ammo:
    #   LoadedAmmo > 0 -> a real shot, do nothing.
    #   LoadedAmmo == 0 -> Fire was pressed while already empty, native reload.
    if loaded is None or loaded != 0:
        return

    _request_reload(w)


@keybind(
    "internal_fire_slot_0",
    key=None,
    is_hidden=True,
    is_rebindable=False,
    event_filter=EInputEvent.IE_Pressed,
)
def _fire_slot_0() -> None:
    _request_reload_from_fire_press()


@keybind(
    "internal_fire_slot_1",
    key=None,
    is_hidden=True,
    is_rebindable=False,
    event_filter=EInputEvent.IE_Pressed,
)
def _fire_slot_1() -> None:
    _request_reload_from_fire_press()


@keybind(
    "internal_fire_slot_2",
    key=None,
    is_hidden=True,
    is_rebindable=False,
    event_filter=EInputEvent.IE_Pressed,
)
def _fire_slot_2() -> None:
    _request_reload_from_fire_press()


@keybind(
    "internal_fire_slot_3",
    key=None,
    is_hidden=True,
    is_rebindable=False,
    event_filter=EInputEvent.IE_Pressed,
)
def _fire_slot_3() -> None:
    _request_reload_from_fire_press()


_FIRE_SLOTS = (
    _fire_slot_0,
    _fire_slot_1,
    _fire_slot_2,
    _fire_slot_3,
)


def _is_action_fire(action: Any) -> bool:
    try:
        if str(action.Name) == "Action_Fire":
            return True
    except Exception:
        pass

    try:
        text = repr(action)
    except Exception:
        return False

    return "Action_Fire.Action_Fire" in text


def _mapping_key_name(mapping: Any):
    try:
        key = mapping.Key
    except Exception:
        return None

    try:
        name = str(key.KeyName)
    except Exception:
        return None

    if not name or name == "None":
        return None
    return name


def _discover_fire_keys() -> list[str]:
    p = _pc()
    c = _char()

    if p is None or c is None:
        return []

    try:
        if "/FrontEnd/" in repr(p) or "Entry_P" in repr(p):
            return []
    except Exception:
        return []

    try:
        mappings = list(p.PlayerInput.EnhancedActionMappings)
    except Exception:
        return []

    result: list[str] = []

    for mapping in mappings:
        try:
            action = mapping.Action
        except Exception:
            continue

        if not _is_action_fire(action):
            continue

        try:
            if bool(mapping.bShouldBeIgnored):
                continue
        except Exception:
            pass

        key_name = _mapping_key_name(mapping)
        if key_name is None or key_name in result:
            continue

        result.append(key_name)

    return result


def _refresh_fire_keys() -> None:
    keys = _discover_fire_keys()
    if not keys:
        return

    keys = keys[: len(_FIRE_SLOTS)]
    for i, slot in enumerate(_FIRE_SLOTS):
        new_key = keys[i] if i < len(keys) else None

        try:
            old_key = slot.key
        except Exception:
            old_key = None

        if old_key == new_key:
            continue

        # Oak2 Keybinds automatically re-registers an enabled keybind when .key changes.
        slot.key = new_key


def _bound_function_path(bound_function: Any) -> str | None:
    """
    Resolve the declaring UFunction path at runtime so this remains robust even if
    GbxEnhancedPlayerInput's script module path differs between builds.
    """
    try:
        func = bound_function.func
    except Exception:
        return None

    try:
        text = repr(func)
    except Exception:
        return None

    # Expected form: Function'/Script/...:OnControlMappingsRebuilt'
    if "'" not in text:
        return None

    try:
        return text.split("'", 1)[1].rsplit("'", 1)[0]
    except Exception:
        return None


def _control_mappings_rebuilt(obj, args, ret, func):
    p = _pc()
    if p is None:
        return

    try:
        if obj != p.PlayerInput:
            return
    except Exception:
        return

    _refresh_fire_keys()


def _ensure_mapping_rebuild_hook() -> None:
    global _mapping_rebuild_hook, _mapping_rebuild_path

    p = _pc()
    if p is None:
        return

    try:
        player_input = p.PlayerInput
        bound = player_input.OnControlMappingsRebuilt
    except Exception:
        return

    path = _bound_function_path(bound)
    if not path:
        return

    if _mapping_rebuild_hook is not None and path == _mapping_rebuild_path:
        return

    if _mapping_rebuild_hook is not None:
        try:
            _mapping_rebuild_hook.disable()
        except Exception:
            pass
        _mapping_rebuild_hook = None
        _mapping_rebuild_path = None

    try:
        dynamic_hook = hook(
            path,
            Type.POST,
            hook_identifier="BL4_AutoReload:OnControlMappingsRebuilt",
        )(_control_mappings_rebuilt)
        dynamic_hook.enable()
    except Exception:
        return

    _mapping_rebuild_hook = dynamic_hook
    _mapping_rebuild_path = path


# --------------------------------------------------------------------------------------
# Shared lifecycle hooks
# --------------------------------------------------------------------------------------

@hook(
    "/Script/OakGame.OakUIDataCollector_WeaponStatus:OnReloadEnded",
    Type.POST,
)
def _reload_ended(obj, args, ret, func):
    try:
        w = args.EventWeapon
    except Exception:
        return

    _pending.discard(_addr(w))


@hook(
    "/Script/OakGame.OakUIDataCollector_WeaponStatus:OnWeaponChanged",
    Type.POST,
)
def _weapon_changed(obj, args, ret, func):
    _refresh_fire_keys()
    _ensure_mapping_rebuild_hook()


@hook(
    "/Script/OakGame.OakCharacter:OnInventoryEquippedOnSlot",
    Type.POST,
)
def _inventory_equipped(obj, args, ret, func):
    c = _char()
    if c is None or obj != c:
        return
    _refresh_fire_keys()
    _ensure_mapping_rebuild_hook()


def on_enable() -> None:
    _pending.clear()
    _refresh_fire_keys()
    _ensure_mapping_rebuild_hook()


def on_disable() -> None:
    global _mapping_rebuild_hook, _mapping_rebuild_path

    _pending.clear()

    if _mapping_rebuild_hook is not None:
        try:
            _mapping_rebuild_hook.disable()
        except Exception:
            pass

    _mapping_rebuild_hook = None
    _mapping_rebuild_path = None


build_mod(
    on_enable=on_enable,
    on_disable=on_disable,
)

from __future__ import annotations

from typing import Any

from mods_base import (
    DropdownOption,
    EInputEvent,
    HookType,
    MODS_DIR,
    build_mod,
    get_pc,
    hook,
    keybind,
)
from unrealsdk.hooks import Type

__author__ = "Sol (ChatGPT, GPT-5.6 Sol)"

MODE_AUTO_ALL = "Auto Reload - All Weapons"
MODE_AUTO_JAKOBS = "Auto Reload - Jakobs Only"
MODE_EMPTY_ALL = "Empty Fire Reload - All Weapons"
MODE_EMPTY_JAKOBS = "Empty Fire Reload - Jakobs Only"

AUTO_MODES = (MODE_AUTO_ALL, MODE_AUTO_JAKOBS)
EMPTY_MODES = (MODE_EMPTY_ALL, MODE_EMPTY_JAKOBS)
JAKOBS_MODES = (MODE_AUTO_JAKOBS, MODE_EMPTY_JAKOBS)

LOG_PATH = MODS_DIR / "BL4_AutoReload.log"

_pending: set[int] = set()
_last_loaded: dict[int, int] = {}
_jakobs_cache: dict[int, bool] = {}

_mapping_rebuild_hook: HookType | None = None
_mapping_rebuild_path: str | None = None


def _log(msg: str) -> None:
    line = f"[BL4 AutoReload] {msg}"
    print(line)
    try:
        with LOG_PATH.open("a", encoding="utf-8", errors="replace") as f:
            f.write(line + "\n")
    except Exception:
        pass


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
    """
    Original auto-reload selector: first active weapon slot with a weapon.
    Preserved from the user-tested v1.3 auto variants.
    """
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
    """
    Selector used by the user-tested Empty Fire v1.5 path.
    """
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
        return True


def _state(w) -> str:
    try:
        return str(w.CurrentState)
    except Exception:
        return ""


def _looks_jakobs(value: Any) -> bool:
    try:
        text = repr(value).lower()
    except Exception:
        return False
    return "jakobs" in text or "jak_" in text


def _is_jakobs(w) -> bool:
    if w is None:
        return False

    key = _addr(w)
    cached = _jakobs_cache.get(key)
    if cached is not None:
        return cached

    for collection_name in ("InstanceComponents", "BlueprintCreatedComponents"):
        try:
            components = list(getattr(w, collection_name))
        except Exception:
            continue

        for component in components:
            if _looks_jakobs(component):
                _jakobs_cache[key] = True
                return True

            for attr_name in (
                "AnimClass",
                "AnimScriptInstance",
                "SkeletalMesh",
                "SkeletalMeshAsset",
                "Class",
                "Name",
            ):
                try:
                    if _looks_jakobs(getattr(component, attr_name)):
                        _jakobs_cache[key] = True
                        return True
                except Exception:
                    pass

    for attr_name in ("ManufacturerMod", "TrickData", "BodyData", "Item"):
        try:
            if _looks_jakobs(getattr(w, attr_name)):
                _jakobs_cache[key] = True
                return True
        except Exception:
            pass

    _jakobs_cache[key] = False
    return False


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
    try:
        text = repr(args.data).lower()
    except Exception:
        try:
            text = repr(args).lower()
        except Exception:
            return False
    return "weaponfire" in text or ("weapon" in text and "fire" in text)


def _seed_current_weapon() -> None:
    w = _weapon()
    if w is None:
        return
    value = _loaded(w)
    if value is not None:
        _last_loaded[_addr(w)] = value


def _request_reload(w, source: str) -> bool:
    if w is None or not _mode_allows_weapon(w) or not _has_magazine(w):
        return False

    current = _loaded(w)
    if current is None or current > 0:
        if current is not None:
            _last_loaded[_addr(w)] = current
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
    except Exception as exc:
        _pending.discard(key)
        _log(f"reload ERROR from {source}: {exc!r}")
        return False

    after = _state(w)
    if after != "Reloading":
        _pending.discard(key)
        _log(f"reload rejected from {source}; state={after!r}")
        return False

    _log(f"reload START [{_mode()}] from {source}; weapon={w!r}")
    return True


# --------------------------------------------------------------------------------------
# Mode option
# --------------------------------------------------------------------------------------

def _on_behavior_change(option, new_value: str) -> None:
    _pending.clear()
    _last_loaded.clear()

    if new_value in EMPTY_MODES:
        _refresh_fire_keys("Behavior change")
        _ensure_mapping_rebuild_hook()

    _log(f"Behavior changed -> {new_value}")


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
# Auto Reload path — preserved from the user-tested v1.3 variants
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

    _last_loaded[_addr(w)] = current

    if current == 0:
        _request_reload(w, "WeaponFire feedback")


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
        _log(
            "ignored stale AmmoPool replication; "
            f"pool_mode={pool_use_mode} current_mode={current_use_mode}"
        )
        return

    _request_reload(w, "AmmoPool replication fallback")


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

    value = _loaded(w)
    if value is not None:
        _last_loaded[_addr(w)] = value

    if value == 0:
        _request_reload(w, "proven Jakobs shotgun PRE")


# --------------------------------------------------------------------------------------
# Empty Fire path — preserved from the user-tested v1.5 variants
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

    _request_reload(w, "empty Action_Fire press")


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


def _refresh_fire_keys(source: str) -> None:
    keys = _discover_fire_keys()
    if not keys:
        return

    keys = keys[: len(_FIRE_SLOTS)]
    changed = False

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
        changed = True

    if changed:
        _log(f"Action_Fire bindings refreshed from {source}: {keys!r}")


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

    _refresh_fire_keys("OnControlMappingsRebuilt")


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
    except Exception as exc:
        _log(f"Unable to hook OnControlMappingsRebuilt ({path!r}): {exc!r}")
        return

    _mapping_rebuild_hook = dynamic_hook
    _mapping_rebuild_path = path
    _log(f"Auto Action_Fire refresh hook enabled: {path}")


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

    key = _addr(w)
    _pending.discard(key)

    value = _loaded(w)
    if value is not None:
        _last_loaded[key] = value


@hook(
    "/Script/OakGame.OakUIDataCollector_WeaponStatus:OnWeaponChanged",
    Type.POST,
)
def _weapon_changed(obj, args, ret, func):
    _seed_current_weapon()
    _refresh_fire_keys("OnWeaponChanged")
    _ensure_mapping_rebuild_hook()


@hook(
    "/Script/OakGame.OakCharacter:OnInventoryEquippedOnSlot",
    Type.POST,
)
def _inventory_equipped(obj, args, ret, func):
    c = _char()
    if c is None or obj != c:
        return

    _seed_current_weapon()
    _refresh_fire_keys("OnInventoryEquippedOnSlot")
    _ensure_mapping_rebuild_hook()


def on_enable() -> None:
    _pending.clear()
    _seed_current_weapon()
    _refresh_fire_keys("on_enable")
    _ensure_mapping_rebuild_hook()
    _log(f"enabled; Behavior={_mode()}")


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
    _log("disabled")


try:
    LOG_PATH.write_text(
        "BL4 AutoReload v1.1.1\n"
        "Creator: Sol (ChatGPT, GPT-5.6 Sol)\n"
        "QA: Last1SiN\n",
        encoding="utf-8",
    )
except Exception:
    pass

_log("loaded")

build_mod(
    on_enable=on_enable,
    on_disable=on_disable,
)

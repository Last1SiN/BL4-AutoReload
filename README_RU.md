# BL4 AutoReload

[English](README.md) | [Русский](README_RU.md)

BL4 AutoReload добавляет в Borderlands 4 четыре переключаемых режима перезарядки, сохраняя штатную игровую логику reload и помогая убрать встроенную задержку перед началом перезарядки на нулевом боезапасе магазина.

Мод не заменяет и не симулирует саму перезарядку, а просит игру запустить её обычным способом. Поэтому сохраняются штатные анимации, скорость перезарядки, бонусы и логика прерывания.

## Доступные режимы

### Auto Reload - All Weapons

Автоматически запускает перезарядку, когда магазин поддерживаемого оружия становится пустым.

### Auto Reload - Jakobs Only

То же поведение, но только для оружия Jakobs.

### Empty Fire Reload - All Weapons

Не запускает перезарядку автоматически после последнего выстрела. Reload начинается только при следующем нажатии Fire, когда магазин уже пуст.

### Empty Fire Reload - Jakobs Only

То же empty-fire поведение, но только для оружия Jakobs.

## Возможности

- Четыре переключаемых режима штатной перезарядки.
- Режим выбирается в настройках мода и сохраняется между запусками.
- Empty Fire режимы автоматически используют текущие `Action_Fire` bindings.
- Поддерживаются keyboard/mouse и gamepad fire bindings.
- Fire bindings обновляются после перестройки control mappings.
- Для оружия с отдельными primary/secondary ammo pools используется активный `CurrentUseModeIndex`.
- Устаревшие ammo replication events от неактивных fire modes игнорируются.
- Используется штатный запрос reload игры вместо внешней симуляции перезарядки.

## Требования

- Borderlands 4
- [BL4 PythonSDK / Oak2 Mod Manager](https://github.com/bl-sdk/oak2-mod-manager/releases/latest)

Для установки и обновления SDK используйте [официальную инструкцию BL4 SDK / Oak2](https://bl-sdk.github.io/oak2-mod-db/).

## Установка мода

1. Установите или обновите BL4 PythonSDK / Oak2 по официальной инструкции выше.
2. Скачайте `BL4_AutoReload.sdkmod` из [GitHub Releases](https://github.com/Last1SiN/BL4-AutoReload/releases/latest) или с [Nexus Mods](https://www.nexusmods.com/borderlands4/mods/288).
3. При полностью закрытой Borderlands 4 скопируйте `.sdkmod` целиком в `Borderlands 4\sdk_mods\`. Сам `.sdkmod` распаковывать не нужно.
4. Запустите игру, откройте Mods menu, включите **BL4 AutoReload** и выберите нужный **Behavior**.

Для обновления замените существующий `.sdkmod` новым файлом и перезапустите игру.

Не включайте одновременно старые отдельные `auto_reload_*` или `empty_fire_reload_*` моды.

## Принцип работы

Мод использует штатный игровой запрос reload:

`ServerStartReloading(CurrentUseModeIndex, 0)`

Поэтому сохраняются обычная анимация перезарядки, скорость reload, влияние перков и стандартная логика прерывания.

## Совместимость и лицензия

- Кооператив: **Unknown** — сценарий, где мод установлен только у клиента, а у хоста его нет, пока не проверен.
- Мод не заменяет weapon animations и не изменяет значения reload speed.
- Лицензия: **GPL-3.0**

## Credits

**Development:** Sol / GPT-5.6 Sol  
**Design, testing & QA:** Last1SiN

**BL4 PythonSDK / Oak2 Mod Manager:** создан [apple1417](https://github.com/apple1417) при участии проекта и контрибьюторов [BL-SDK](https://github.com/bl-sdk).

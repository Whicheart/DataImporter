# GI-Database-script

把 JSON 导入本地 MongoDB 的脚本集合。
本仓库不提供 JSON 数据，请前往[上游仓库](https://github.com/DimbreathBot/AnimeGameData)自行获取。

## 目录结构

```
.
├── importer/                       # 39 个导入脚本，一个源文件对应一个
│   ├── AvatarExcelConfigData.py
│   ├── WeaponStory.py              # 武器故事文本
│   ├── ReliquaryStory.py           # 圣遗物故事文本
│   ├── TextMapMedium.py            # 文本表（交互式）
│   ├── 导入角色能力.py              # 勿用：先 drop 再读外部目录
│   └── ...
├── tool/                           # 辅助脚本（字段分析等）
├── json/                           # 源数据（不进版本控制）
├── weapon story/                   # 武器故事文本（源数据）
├── reliquary story/                # 圣遗物故事文本（源数据）
└── README.md
```

## 环境

| 项      | 要求                                                          |
| ------- | ------------------------------------------------------------- |
| Python  | 3.10+（开发环境 3.13）                                        |
| pymongo | 4.x（开发环境 4.19）                                          |
| MongoDB | 6.x / 7.x / 8.x（开发环境 8.2），`mongodb://localhost:27017/` |
| 库名    | `GI`（写在各脚本文件头的 `DB_NAME`）                          |

```bash
pip install pymongo
```

## 运行

脚本里的数据路径都写成相对 `importer/` 的形式（`../json/xxx.json`、`../weapon story/` 等），所以**先进入 `importer/` 目录**再运行。每个脚本会先 `drop` 再重建目标集合。

单个：

```bash
cd importer
python AvatarExcelConfigData.py
```

批量（`TextMapMedium.py` 需要交互、`导入角色能力.py` 勿用，两者跳过）：

```bash
cd importer
for f in *.py; do
  case "$f" in TextMapMedium.py|导入角色能力.py) continue ;; esac
  echo "==> $f"
  python "$f" || break
done
```

> `drop + insert_many` 意味着脚本是**幂等**的：重复执行得到同样结果，但会清掉你手工往集合里追加的数据。

## 脚本与集合对照

| importer 脚本                                     | 源文件                                              | 目标集合                           | 说明                                                |
| ------------------------------------------------- | --------------------------------------------------- | ---------------------------------- | --------------------------------------------------- |
| `AttackAttenuationExcelConfigData.py`             | `AttackAttenuationExcelConfigData.json`             | `attack_attenuation`               | `_id = group`                                       |
| `AvatarExcelConfigData.py`                        | `AvatarExcelConfigData.json`                        | `avatar`                           | `_id = id`，跳过 `ICHCEGHCFJE`                      |
| `AvatarCodexExcelConfigData.py`                   | `AvatarCodexExcelConfigData.json`                   | `avatar_codex`                     | `_id = avatarId`                                    |
| `AvatarCostumeExcelConfigData.py`                 | `AvatarCostumeExcelConfigData.json`                 | `avatar_costume`                   | `_id = skinId`                                      |
| `AvatarCurveExcelConfigData.py`                   | `AvatarCurveExcelConfigData.json`                   | `avatar_curve`                     | `_id = level`，曲线类型取 `GGKIEIJLCJJ`             |
| `AvatarFettersLevelExcelConfigData.py`            | `AvatarFettersLevelExcelConfigData.json`            | `avatar_fetters_level`             | `_id = fetterLevel`                                 |
| `AvatarLevelExcelConfigData.py`                   | `AvatarLevelExcelConfigData.json`                   | `avatar_level`                     | `_id = level`                                       |
| `AvatarPromoteExcelConfigData.py`                 | `AvatarPromoteExcelConfigData.json`                 | `avatar_promote`                   | 按 `avatarPromoteId` 合并，缺 `promoteLevel` 补 0   |
| `AvatarSkillDepotExcelConfigData.py`              | `AvatarSkillDepotExcelConfigData.json`              | `avatar_skill_depot`               | 3 个字段改名 + 嵌套 `unlockPromoteLevel`            |
| `AvatarSkillExcelConfigData.py`                   | `AvatarSkillExcelConfigData.json`                   | `avatar_skill`                     | `_id = id`                                          |
| `AvatarTalentExcelConfigData.py`                  | `AvatarTalentExcelConfigData.json`                  | `avatar_talent`                    | `_id = talentId`                                    |
| `AvatarTraceEffectExcelConfigData.py`             | `AvatarTraceEffectExcelConfigData.json`             | `avatar_trace_effect`              | `_id = avatarId`，跳过 `JLNHLCPGJBN`                |
| `EquipAffixExcelConfigData.py`                    | `EquipAffixExcelConfigData.json`                    | `equip_affix`                      | `_id = id`，缺 `level` 补 0，各档放进 `levels`      |
| `FetterCharacterCardExcelConfigData.py`           | `FetterCharacterCardExcelConfigData.json`           | `fetter_character_card`            | 不设 `_id`（ObjectId）                              |
| `FetterInfoExcelConfigData.py`                    | `FetterInfoExcelConfigData.json`                    | `fetter_info`                      | `_id = avatarId`，3 个字段改名                      |
| `FetterStoryExcelConfigData.py`                   | `FetterStoryExcelConfigData.json`                   | `fetter_story`                     | 不设 `_id`                                          |
| `FettersExcelConfigData.py`                       | `FettersExcelConfigData.json`                       | `fetters`                          | 不设 `_id`，`tips` 元素转字符串                     |
| `MaterialCodexExcelConfigData.py`                 | `MaterialCodexExcelConfigData.json`                 | `material_codex`                   | `_id = id`                                          |
| `MaterialExcelConfigData.py`                      | `MaterialExcelConfigData.json`                      | `material`                         | `_id = id`，2 个字段改名                            |
| `MaterialSourceDataExcelConfigData.py`            | `MaterialSourceDataExcelConfigData.json`            | `material_source_data`             | `_id = id`，`HNNPIIJLLEK → sourceList`              |
| `ProudSkillExcelConfigData.py`                    | `ProudSkillExcelConfigData.json`                    | `proud_skill`                      | `_id = proudSkillId`，2 个字段改名                  |
| `ReliquaryExcelConfigData.py`                     | `ReliquaryExcelConfigData.json`                     | `reliquary`                        | `_id = id`                                          |
| `ReliquaryAffixExcelConfigData.py`                | `ReliquaryAffixExcelConfigData.json`                | `reliquary_affix`                  | `_id = id`                                          |
| `ReliquaryCodexExcelConfigData.py`                | `ReliquaryCodexExcelConfigData.json`                | `reliquary_codex`                  | `_id = id`                                          |
| `ReliquaryLevelExcelConfigData.py`                | `ReliquaryLevelExcelConfigData.json`                | `reliquary_level`                  | 按 `rank` 合并，`addProps` 的 `GGKIEIJLCJJ → value` |
| `ReliquaryAffixNormalizedParamExcelConfigData.py` | `ReliquaryAffixNormalizedParamExcelConfigData.json` | `reliquary_affix_normalized_param` | `_id = id`，`NDDNDHEELMC → propType`                |
| `ReliquaryMainPropExcelConfigData.py`             | `ReliquaryMainPropExcelConfigData.json`             | `reliquary_main_prop`              | `_id = id`                                          |
| `ReliquarySetExcelConfigData.py`                  | `ReliquarySetExcelConfigData.json`                  | `reliquary_set`                    | `_id = setId`，`LAJGLFNPLCP → maxRankLevel`         |
| `ReliquaryWearMainPropExcelConfigData.py`         | `ReliquaryWearMainPropExcelConfigData.json`         | `reliquary_wear_main_prop`         | 不设 `_id`，`DFGOJJFJODK → mainPropId`              |
| `ReliquaryWearAppendPropExcelConfigData.py`       | `ReliquaryWearAppendPropExcelConfigData.json`       | `reliquary_wear_append_prop`       | 不设 `_id`，`DOLNLGCNGIA → appendPropId`            |
| `ReliquaryStory.py`                               | `reliquary story/Relic<id>_<x>.txt`                 | `reliquary_story`                  | `_id = <id>`，`stories[x-1]` 是第 x 篇的行数组      |
| `TextMapMedium.py`                                | `TextMap_MediumCHS/EN.json`                         | `text_map_chs_medium` 等           | 交互选择文件；先写 `*_array.json` 再入库            |
| `WeaponExcelConfigData.py`                        | `WeaponExcelConfigData.json`                        | `weapon`                           | `_id = id`                                          |
| `WeaponLevelExcelConfigData.py`                   | `WeaponLevelExcelConfigData.json`                   | `weapon_level`                     | `_id = level`                                       |
| `WeaponPromoteExcelConfigData.py`                 | `WeaponPromoteExcelConfigData.json`                 | `weapon_promote`                   | 按 `weaponPromoteId` 合并，缺 `promoteLevel` 补 0   |
| `WeaponCurveExcelConfigData.py`                   | `WeaponCurveExcelConfigData.json`                   | `weapon_curve`                     | `_id = level`，`curveInfos` 拍平成 `curves`         |
| `WeaponCodexExcelConfigData.py`                   | `WeaponCodexExcelConfigData.json`                   | `weapon_codex`                     | `_id = id`                                          |
| `WeaponStory.py`                                  | `weapon story/Weapon<id>[_x].txt`                   | `weapon_story`                     | `_id = <id>`，`stories` 是各篇的行数组              |

## 字段处理约定

所有脚本共享同一套清洗规则。

1. 大多数脚本把源记录的某个 `id` 类字段提升为 `_id` 并保留（等于没有 `id` 字段）。少数集合不设 `_id`，交给 MongoDB 生成 ObjectId：`fetters`、`fetter_story`、`fetter_character_card`、`reliquary_wear_main_prop`、`reliquary_wear_append_prop`。

2. 源数据中 `*Hash` 结尾的字段（`nameTextMapHash`、`descTextMapHash`…）是 64 位整数，统一 `str()` 后入库，避免精度/类型问题。超过 int64 的混淆字段（如 `POCCNIJNACM`、`EPCOMPFIIJD`）同样按白名单转字符串，否则 pymongo 会报 `OverflowError`。

**3. 混淆字段改名**

| 集合                                              | 原字段                                        | 新字段                                                                                     |
| ------------------------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `avatar_skill`、`avatar_talent`、`proud_skill`    | `CJJODEPIILB`                                 | `descExtraTextMapHash`                                                                     |
| `proud_skill`                                     | `NAOILGGDLNA`                                 | `loreDescTextMapHash`                                                                      |
| `material`                                        | `LDKKLGEEGAP` / `PANBBKJOBOL`                 | `filterType` / `effectType`                                                                |
| `material_source_data`                            | `HNNPIIJLLEK`                                 | `sourceList`                                                                               |
| `avatar_skill_depot`                              | `LLEFDMDOMGG` / `KDCMKCFKPBL` / `PEAOICMBMKH` | `proudSkillGroups` / `specialProudSkillGroups` / `arkheType`                               |
| `avatar_skill_depot`（`proudSkillGroups` 元素内） | `DHIEHDPAFGI`                                 | `unlockPromoteLevel`                                                                       |
| `fetter_info`                                     | `LCHFJFOMFGA` / `AAEINBDNBHL` / `PNIAJCCODBA` | `avatarPowerBeforTextMapHash` / `avatarPowerAfterTextMapHash` / `avatarNative2TextMapHash` |
| `reliquary_affix_normalized_param`                | `NDDNDHEELMC`                                 | `propType`                                                                                 |
| `reliquary_set`                                   | `LAJGLFNPLCP`                                 | `maxRankLevel`                                                                             |
| `reliquary_wear_main_prop`                        | `DFGOJJFJODK`                                 | `mainPropId`                                                                               |
| `reliquary_wear_append_prop`                      | `DOLNLGCNGIA`                                 | `appendPropId`                                                                             |

4. `addProps` 数组元素里的 `GGKIEIJLCJJ` 改成 `value`（`avatar_promote` / `avatar_talent` / `proud_skill` / `equip_affix` / `weapon_promote` / `reliquary_level`）。

5. 并非所有混淆字段都要改名。`avatar`、`avatar_costume` 的 `OBF_HASH` 白名单、`avatar_trace_effect`、`material_source_data` 等集合里，部分字段按原样保留（只是值统一 `str()`）。

## 注意事项

- **`TextMapMedium.py` 是交互式的**：手动输入文件名，不能直接纳入批量循环。
- **文本表覆盖率并非全部**：部分集合中的大部分哈希字段在 `text_map_chs_medium` 里查不到，属数据源限制。
- **`WeaponStory.py`** 读 `weapon story/` 里的 txt：一行一个字符串存进 `stories`；首行空行去掉；整篇为空时用「……」占位；`Weapon<id>.txt` 排第一位，`_1`、`_2` 等变体依次排在后面。
- **`ReliquaryStory.py`** 读 `reliquary story/` 里的 `Relic<id>_<x>.txt`：一行一个字符串存进 `stories[x-1]`；空行保留；首行为空行时跳过。
- **`reliquary_wear_main_prop` / `reliquary_wear_append_prop` 没有主键**：每次重跑（`drop` 后重插）`_id` 都会变。
- **`导入角色能力.py` 勿用**：先 `drop` 再读仓库根目录的 `AvatarAbilities/`，该目录不存在时会把 `avatar_ability` 清空。

## 版本控制

`.gitignore` 忽略 `json/`、`weapon story/`、`reliquary story/`、`__pycache__/` 与编辑器目录。

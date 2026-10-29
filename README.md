# GI-Database-script

把 JSON 导入本地 MongoDB 的脚本集合。
本仓库不提供 JSON 数据，请前往[仓库](https://github.com/DimbreathBot/AnimeGameData)自行获取。

## 目录结构

```
.
├── importer/                       # 导入脚本
│   ├── AvatarExcelConfigData.py    # 一个源文件对应一个脚本
│   ├── WeaponStory.py              # 武器故事文本导入
│   ├── 导入角色能力.py              # 暂勿使用，无视即可
│   └── ...
├── tool/                           # 一些辅助脚本
├── json/                           # 源数据
├── weapon story/                   # 武器故事文本（源数据）
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

脚本里的 `PATH` 指向 `json/xxx.json`（相对仓库根目录），**在仓库根目录运行**即可，脚本会自动 `drop` 并重建目标集合。

单个：

```bash
python importer/AvatarExcelConfigData.py
```

其余脚本可以使用如下命令全部运行 (除文本表脚本外)：

```bash
for f in importer/*.py; do
  name=$(basename "$f")
  [ "$name" = "TextMapMedium.py" ] && continue
  echo "==> $name"
  python "$f" || break
done
```

> `drop + insert_many` 意味着脚本是**幂等**的：重复执行得到同样结果，但会清掉你手工往集合里追加的数据。

## 脚本与集合对照

| importer 脚本                           | 源文件（`json/`）                         | 目标集合                | 说明                                              |
| --------------------------------------- | ----------------------------------------- | ----------------------- | ------------------------------------------------- |
| `AttackAttenuationExcelConfigData.py`   | `AttackAttenuationExcelConfigData.json`   | `attack_attenuation`    | `_id = group`                                     |
| `AvatarExcelConfigData.py`              | `AvatarExcelConfigData.json`              | `avatar`                | `_id = id`，跳过 `ICHCEGHCFJE`                    |
| `AvatarCodexExcelConfigData.py`         | `AvatarCodexExcelConfigData.json`         | `avatar_codex`          | `_id = avatarId`                                  |
| `AvatarCostumeExcelConfigData.py`       | `AvatarCostumeExcelConfigData.json`       | `avatar_costume`        | `_id = skinId`                                    |
| `AvatarCurveExcelConfigData.py`         | `AvatarCurveExcelConfigData.json`         | `avatar_curve`          | `_id = level`，曲线类型取 `GGKIEIJLCJJ`           |
| `AvatarFettersLevelExcelConfigData.py`  | `AvatarFettersLevelExcelConfigData.json`  | `avatar_fetters_level`  | `_id = fetterLevel`                               |
| `AvatarLevelExcelConfigData.py`         | `AvatarLevelExcelConfigData.json`         | `avatar_level`          | `_id = level`                                     |
| `AvatarPromoteExcelConfigData.py`       | `AvatarPromoteExcelConfigData.json`       | `avatar_promote`        | 按 `avatarPromoteId` 合并，缺 `promoteLevel` 补 0 |
| `AvatarSkillDepotExcelConfigData.py`    | `AvatarSkillDepotExcelConfigData.json`    | `avatar_skill_depot`    | 3 个字段改名 + 嵌套 `unlockPromoteLevel`          |
| `AvatarSkillExcelConfigData.py`         | `AvatarSkillExcelConfigData.json`         | `avatar_skill`          | `_id = id`                                        |
| `AvatarTalentExcelConfigData.py`        | `AvatarTalentExcelConfigData.json`        | `avatar_talent`         | `_id = talentId`                                  |
| `AvatarTraceEffectExcelConfigData.py`   | `AvatarTraceEffectExcelConfigData.json`   | `avatar_trace_effect`   | `_id = avatarId`，跳过 `JLNHLCPGJBN`              |
| `EquipAffixExcelConfigData.py` | `EquipAffixExcelConfigData.json` | `equip_affix` | `_id = id`，缺 `level` 补 0，各档放进 `levels` 数组 |
| `FetterCharacterCardExcelConfigData.py` | `FetterCharacterCardExcelConfigData.json` | `fetter_character_card` | 不设 `_id`（ObjectId）                            |
| `FetterInfoExcelConfigData.py`          | `FetterInfoExcelConfigData.json`          | `fetter_info`           | `_id = avatarId`，3 个字段改名                    |
| `FetterStoryExcelConfigData.py`         | `FetterStoryExcelConfigData.json`         | `fetter_story`          | 不设 `_id`                                        |
| `FettersExcelConfigData.py`             | `FettersExcelConfigData.json`             | `fetters`               | 不设 `_id`，`tips` 元素转字符串                   |
| `MaterialCodexExcelConfigData.py`       | `MaterialCodexExcelConfigData.json`       | `material_codex`        | `_id = id`                                        |
| `MaterialExcelConfigData.py`            | `MaterialExcelConfigData.json`            | `material`              | `_id = id`，2 个字段改名                          |
| `MaterialSourceDataExcelConfigData.py`  | `MaterialSourceDataExcelConfigData.json`  | `material_source_data`  | `_id = id`，`HNNPIIJLLEK → sourceList`            |
| `ProudSkillExcelConfigData.py`          | `ProudSkillExcelConfigData.json`          | `proud_skill`           | `_id = proudSkillId`，2 个字段改名                |
| `ReliquaryExcelConfigData.py` | `ReliquaryExcelConfigData.json` | `reliquary` | `_id = id` |
| `ReliquaryAffixExcelConfigData.py` | `ReliquaryAffixExcelConfigData.json` | `reliquary_affix` | `_id = id` |
| `ReliquaryCodexExcelConfigData.py` | `ReliquaryCodexExcelConfigData.json` | `reliquary_codex` | `_id = id` |
| `ReliquaryLevelExcelConfigData.py` | `ReliquaryLevelExcelConfigData.json` | `reliquary_level` | 按 `rank` 合并，`addProps` 的 `GGKIEIJLCJJ → value` |
| `ReliquaryAffixNormalizedParamExcelConfigData.py` | `ReliquaryAffixNormalizedParamExcelConfigData.json` | `reliquary_affix_normalized_param` | `_id = id`，`NDDNDHEELMC → propType` |
| `ReliquaryMainPropExcelConfigData.py` | `ReliquaryMainPropExcelConfigData.json` | `reliquary_main_prop` | `_id = id` |
| `ReliquarySetExcelConfigData.py` | `ReliquarySetExcelConfigData.json` | `reliquary_set` | `_id = setId`，`LAJGLFNPLCP → maxRankLevel` |
| `ReliquaryWearMainPropExcelConfigData.py` | `ReliquaryWearMainPropExcelConfigData.json` | `reliquary_wear_main_prop` | 不设 `_id`，`DFGOJJFJODK → mainPropId` |
| `ReliquaryWearAppendPropExcelConfigData.py` | `ReliquaryWearAppendPropExcelConfigData.json` | `reliquary_wear_append_prop` | 不设 `_id`，`DOLNLGCNGIA → appendPropId` |
| `TextMapMedium.py`                      | `TextMap_MediumCHS.json`                  | `text_map_chs_medium`   | 交互选择 `json/` 下的文件；先写 `*_array.json` 再入库 |
| `WeaponExcelConfigData.py` | `WeaponExcelConfigData.json` | `weapon` | `_id = id` |
| `WeaponLevelExcelConfigData.py` | `WeaponLevelExcelConfigData.json` | `weapon_level` | `_id = level` |
| `WeaponPromoteExcelConfigData.py` | `WeaponPromoteExcelConfigData.json` | `weapon_promote` | 按 `weaponPromoteId` 合并，缺 `promoteLevel` 补 0 |
| `WeaponCurveExcelConfigData.py` | `WeaponCurveExcelConfigData.json` | `weapon_curve` | `_id = level`，`curveInfos` 拍平成 `curves` |
| `WeaponCodexExcelConfigData.py` | `WeaponCodexExcelConfigData.json` | `weapon_codex` | `_id = id` |
| `WeaponStory.py` | `weapon story/Weapon<id>[_x].txt` | `weapon_story` | `_id = <id>`，`stories` 是各篇的行数组 |

## 字段处理约定

所有脚本共享同一套清洗规则：

1. 大多数脚本把源记录的某个 `id` 类字段提升为 `_id` 并保留（等于没有 `id` 字段）。少数集合不设 `_id`，交给 MongoDB 生成 ObjectId：`fetters`、`fetter_story`、`fetter_character_card`。

2. 源数据中 `*Hash` 结尾的字段（`nameTextMapHash`、`descTextMapHash`…）是 64 位整数，统一 `str()` 后入库，避免精度/类型问题。配套地，源 JSON 里超过 2^53 的大整数只出现在 Hash 字段和混淆字段里，都会被这种规则处理掉。

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

5. 并非所有混淆字段都要改名。`avatar` 的 `OBF_HASH` 白名单、`avatar_costume`、`avatar_trace_effect`、`material_source_data` 等集合里，部分字段按原样保留（只是值统一 `str()`）。

## 注意事项

- **`TextMapMedium.py` 是交互式的**：要手动输入文件名，不能直接纳入上面的 `for` 循环。
- **文本表覆盖率并非全部**：部分集合中的大部分哈希字段无法在 `text_map_chs_medium` 中查到是正常现象。
- **`WeaponStory.py`** 读的是 `weapon story/` 里的 txt：一行一个字符串存进 `stories`；首行空行会被去掉；整篇为空时用「……」占位；`Weapon<id>.txt` 排在第一位，`_1`、`_2` 等变体依次排在后面。
- **`reliquary_wear_main_prop` / `reliquary_wear_append_prop` 没有主键**：源数据里只有 `equipType` 之类的分组字段，`_id` 交给 MongoDB 生成，所以每次重跑（`drop` 后重插）`_id` 都会变。

## 版本控制

`.gitignore` 忽略 `json/`、`weapon story/`、`__pycache__/`、编辑器目录。

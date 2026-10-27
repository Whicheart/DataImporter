# GI-Database-script

把游戏的 JSON 导入本地 MongoDB 的脚本集合。
本仓库不提供 JSON 数据，请前往[仓库](https://github.com/DimbreathBot/AnimeGameData)自行获取。

## 目录结构

```
.
├── importer/                       # 导入脚本
│   ├── AvatarExcelConfigData.py    # 一个源文件对应一个脚本
│   └── ...
├── tool/                           # 一些辅助脚本
├── 导入角色能力.py                  # 暂勿使用，无视即可
├── json/                           # 源数据
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

在 `json/` 目录下运行脚本，脚本会自动 `drop` 并重建目标集合。

单个：

```bash
cd json
python ../importer/AvatarExcelConfigData.py
```

其余脚本可以使用如下命令全部运行 (除文本表脚本外)：

```bash
cd json
for f in ../importer/*.py; do
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
| `FetterCharacterCardExcelConfigData.py` | `FetterCharacterCardExcelConfigData.json` | `fetter_character_card` | 不设 `_id`（ObjectId）                            |
| `FetterInfoExcelConfigData.py`          | `FetterInfoExcelConfigData.json`          | `fetter_info`           | `_id = avatarId`，3 个字段改名                    |
| `FetterStoryExcelConfigData.py`         | `FetterStoryExcelConfigData.json`         | `fetter_story`          | 不设 `_id`                                        |
| `FettersExcelConfigData.py`             | `FettersExcelConfigData.json`             | `fetters`               | 不设 `_id`，`tips` 元素转字符串                   |
| `MaterialCodexExcelConfigData.py`       | `MaterialCodexExcelConfigData.json`       | `material_codex`        | `_id = id`                                        |
| `MaterialExcelConfigData.py`            | `MaterialExcelConfigData.json`            | `material`              | `_id = id`，2 个字段改名                          |
| `MaterialSourceDataExcelConfigData.py`  | `MaterialSourceDataExcelConfigData.json`  | `material_source_data`  | `_id = id`，`HNNPIIJLLEK → sourceList`            |
| `ProudSkillExcelConfigData.py`          | `ProudSkillExcelConfigData.json`          | `proud_skill`           | `_id = proudSkillId`，2 个字段改名                |
| `TextMapMedium.py`                      | `TextMap_MediumCHS.json`                  | `text_map_chs_medium`   | 交互输入文件名；先写 `*_array.json` 再入库        |

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

4. `addProps` 数组元素里的 `GGKIEIJLCJJ` 改成 `value`（`avatar_promote` / `avatar_talent` / `proud_skill`）。

5. 并非所有混淆字段都要改名。`avatar` 的 `OBF_HASH` 白名单、`avatar_costume`、`avatar_trace_effect`、`material_source_data` 等集合里，部分字段按原样保留（只是值统一 `str()`）。

## 注意事项

- **`TextMapMedium.py` 是交互式的**：要手动输入文件名，不能直接纳入上面的 `for` 循环。
- **文本表覆盖率并非全部**：部分集合中的大部分哈希字段无法在 `text_map_chs_medium` 中查到是正常现象。

## 版本控制

`.gitignore` 忽略 `json/`、`__pycache__/`、编辑器目录。

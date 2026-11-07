# DataImporter

把原数据导入本地 MongoDB 的脚本集合。
本仓库不提供数据文件，请前往[上游仓库](https://github.com/DimbreathBot/AnimeGameData)获取，按下文目录结构放置。

## 目录结构

```
.
├── ExcelBinOutput/
├── TextMap/
├── Readable/CHS/
├── importer/
│   ├── ExcelConfigDataImporter.py  # 按 SPECS 表导入 Excel 数据
│   ├── ReadableImporter.py         # 故事文本 → *_story 集合
│   ├── TextMapImporter.py          # 哈希字典 → text_map_medium_<lang>
│   └── _common.py                  # 数据清洗、防护机制、文档构建
├── tool/
│   └── FieldAnalysis.py            # 字段分析工具
├── FieldMap.json                   # 混淆字段字典
├── AnalysisResult.txt              # 由tool/FieldAnalysis.py运行生成
├── 导入角色能力.py                  # 勿用
└── README.md
```

## 环境

| 项      | 要求                                          |
| ------- | --------------------------------------------- |
| Python  | 3.10+                                         |
| pymongo | 4.x                                           |
| MongoDB | 6.x / 7.x / 8.x，`mongodb://localhost:27017/` |
| 库名    | `GI`                                          |

```bash
pip install pymongo
```

## 运行

```bash
cd importer
```

**Excel 数据**

```bash
python ExcelConfigDataImporter.py --list                 # 列出全部表、目标集合与主键
python ExcelConfigDataImporter.py --check --all          # 不连库预检
python ExcelConfigDataImporter.py --all --dry-run        # 预演全部，只打印条数
python ExcelConfigDataImporter.py --all                  # 入库
python ExcelConfigDataImporter.py monster                # 指定单表导入
python ExcelConfigDataImporter.py --all --skip-pending   # 跳过主键未确认的表
```

**文本表与故事文本**

```bash
python TextMapImporter.py     # TextMap/*.json → text_map_medium_<lang>
python ReadableImporter.py    # Readable/CHS/*.txt → weapon_story / relic_story
```

> 所有导入都是**幂等**的 `drop + insert_many`。

## 字段映射：FieldMap.json

`FieldMap.json` 是一个 `{混淆字段: 明文}` 的扁平字典，按明文的写法分四类：

| 写法                 | 含义                     |
| -------------------- | ------------------------ |
| 与混淆字段相同       | 不改名，原样入库         |
| 空字符串             | 该字段直接丢弃           |
| `aaaaTextMapHash` 等 | 用于保留类型语义的占位名 |
| 真实明文名           | 明文                     |

## 预检

`ExcelConfigDataImporter.py` 在 `drop` 之前先跑完以下检查，任何一道不过就整体退出，以此保护库中的原数据：

1. 文件存在且能解析；
2. 混淆字典对混淆字段的覆盖率必须 100%；
3. 哈希字段必须被命名或登记；
4. 主键/分组键必须存在。

## 辅助工具

`tool/FieldAnalysis.py` 用来找出源数据里的混淆字段：

```bash
python tool/FieldAnalysis.py
```

选择分析对象后，分析结果会写入仓库根目录的 `AnalysisResult.txt`：每个字段路径给出所属文件/集合、出现次数和 5 个样本，并区分「混淆字段」与「明文字段」。同时生成字典 `FieldMap.json`，把右边的值改成明文名即可；重跑时已填写的值会保留。

## 注意事项

- **哈希字段统一转字符串**：所有 `*Hash` 结尾的字段 `str()` 后入库；`tips`、`textList`、`paramDescList`、`jumpDescs` 四个字段为哈希数组，元素也转字符串。
- **故事文本**：`ReadableImporter.py` 读 `Readable/CHS/` 下的 `<type><id>[_<idx>].txt`，一行一个字符串，去掉首尾空行、保留行间空行，空文件存成 `[]`；集合名 = `<type>` 小写 + `_story`；同一 id 下无 `idx` 的排最前，其余按 `idx` 升序。
- **`导入角色能力.py` 勿用**。

## 表清单（40 张）

| 集合                    | 主键                   | 源文件                                  | 备注                                        |
| ----------------------- | ---------------------- | --------------------------------------- | ------------------------------------------- |
| `avatar`                | `id`                   | AvatarExcelConfigData.json              |                                             |
| `avatar_codex`          | `avatarId`             | AvatarCodexExcelConfigData.json         |                                             |
| `avatar_costume`        | `skinId`               | AvatarCostumeExcelConfigData.json       |                                             |
| `avatar_curve`          | `level`                | AvatarCurveExcelConfigData.json         | `curveInfos` 拍平成 `curves`                |
| `avatar_fetters_level`  | `fetterLevel`          | AvatarFettersLevelExcelConfigData.json  |                                             |
| `avatar_level`          | `level`                | AvatarLevelExcelConfigData.json         |                                             |
| `avatar_promote`        | 分组 `avatarPromoteId` | AvatarPromoteExcelConfigData.json       | 缺 `promoteLevel` 补 0                      |
| `avatar_skill_depot`    | `id`                   | AvatarSkillDepotExcelConfigData.json    |                                             |
| `avatar_skill`          | `id`                   | AvatarSkillExcelConfigData.json         |                                             |
| `avatar_talent`         | `talentId`             | AvatarTalentExcelConfigData.json        |                                             |
| `avatar_trace_effect`   | `avatarId`             | AvatarTraceEffectExcelConfigData.json   |                                             |
| `avatar_flycloak`       | `id`                   | AvatarFlycloakExcelConfigData.json      | 源字段是混淆名 `FBBOPPGICOK`，映射后即 `id` |
| `reliquary`             | `id`                   | ReliquaryExcelConfigData.json           |                                             |
| `reliquary_affix`       | `id`                   | ReliquaryAffixExcelConfigData.json      |                                             |
| `reliquary_codex`       | `id`                   | ReliquaryCodexExcelConfigData.json      |                                             |
| `reliquary_level`       | 分组 `rank`            | ReliquaryLevelExcelConfigData.json      | 缺 `rank` 补 0，组内按 `level` 排序         |
| `reliquary_main_prop`   | `id`                   | ReliquaryMainPropExcelConfigData.json   |                                             |
| `reliquary_set`         | `setId`                | ReliquarySetExcelConfigData.json        |                                             |
| `weapon`                | `id`                   | WeaponExcelConfigData.json              |                                             |
| `weapon_codex`          | `id`                   | WeaponCodexExcelConfigData.json         |                                             |
| `weapon_curve`          | `level`                | WeaponCurveExcelConfigData.json         | `curveInfos` 拍平成 `curves`                |
| `weapon_level`          | `level`                | WeaponLevelExcelConfigData.json         |                                             |
| `weapon_promote`        | 分组 `weaponPromoteId` | WeaponPromoteExcelConfigData.json       | 缺 `promoteLevel` 补 0                      |
| `equip_affix`           | 分组 `id`              | EquipAffixExcelConfigData.json          | 缺 `level` 补 0，各档放进 `levels`          |
| `material`              | `id`                   | MaterialExcelConfigData.json            |                                             |
| `material_codex`        | `id`                   | MaterialCodexExcelConfigData.json       |                                             |
| `material_source_data`  | `id`                   | MaterialSourceDataExcelConfigData.json  |                                             |
| `proud_skill`           | `proudSkillId`         | ProudSkillExcelConfigData.json          |                                             |
| `fetter_info`           | `avatarId`             | FetterInfoExcelConfigData.json          |                                             |
| `fetters`               | 不设 `_id`             | FettersExcelConfigData.json             |                                             |
| `fetter_story`          | 不设 `_id`             | FetterStoryExcelConfigData.json         |                                             |
| `fetter_character_card` | 不设 `_id`             | FetterCharacterCardExcelConfigData.json |                                             |
| `monster`               | `id`                   | MonsterExcelConfigData.json             |                                             |
| `monster_affix`         | `id`                   | MonsterAffixExcelConfigData.json        |                                             |
| `monster_curve`         | `level`                | MonsterCurveExcelConfigData.json        | `curveInfos` 拍平成 `curves`                |
| `monster_describe`      | `id`                   | MonsterDescribeExcelConfigData.json     |                                             |
| `monster_multi_player`  | `Id`                   | MonsterMultiPlayerExcelConfigData.json  |                                             |
| `monster_relationship`  | `id`                   | MonsterRelationshipExcelConfigData.json |                                             |
| `monster_special_name`  | `specialNameID`        | MonsterSpecialNameExcelConfigData.json  |                                             |
| `monster_title`         | `titleID`              | MonsterTitleExcelConfigData.json        |                                             |

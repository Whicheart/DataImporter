# GI-Database-script

把游戏解包导出的 Excel JSON（`json/`）导入本地 MongoDB（库名 `GI`）的脚本集合。

每个导入脚本只做一件事：读取一个 JSON → 逐条清洗字段 → `drop()` 目标集合并 `insert_many()` 全量重写。脚本之间互不依赖，可以单独跑，也可以按任意顺序跑。

```
json/*.json  ──►  importer/*.py  ──►  MongoDB (GI)
```

## 目录结构

```
.
├── importer/                       # 导入脚本（21 个）
│   ├── AvatarExcelConfigData.py    # 一个源文件对应一个脚本
│   ├── ...
│   └── TextMapMedium.py            # 文本表：交互选择文件，先转 *.json 再入库
├── tool/                           # 辅助脚本（不参与导入）
│   ├── 字段分析-BSON.py            # 递归扫描集合字段路径，找可疑混淆字段
│   ├── 字段分析-JSON.py            # 同上，针对 JSON 源文件
│   ├── 混淆字段对比.py             # 比对 avatar 中混淆字段与明文字段的值
│   └── AAEINBDNBHL.py              # 按 avatarPowerAfterTextMapHash 聚合查文本
├── 导入角色能力.py                  # 独立脚本：从 avatar 集合生成 avatar_ability
├── json/                           # 源数据（不纳入版本控制，见 .gitignore）
└── README.md
```

## 环境

| 项 | 要求 |
| --- | --- |
| Python | 3.10+（开发环境 3.13） |
| pymongo | 4.x（开发环境 4.19） |
| MongoDB | 6.x / 7.x / 8.x（开发环境 8.2），`mongodb://localhost:27017/` |
| 库名 | `GI`（写在各脚本文件头的 `DB_NAME`） |

```bash
pip install pymongo
```

## 运行

脚本里的 `PATH` 是相对路径（如 `"AvatarExcelConfigData.json"`），所以**必须在 `json/` 目录下运行**，脚本会自动 `drop` 并重建目标集合。

单个：

```bash
cd json
python ../importer/AvatarExcelConfigData.py
```

全部（文本表交互脚本除外）：

```bash
cd json
for f in ../importer/*.py; do
  name=$(basename "$f")
  [ "$name" = "TextMapMedium.py" ] && continue
  echo "==> $name"
  python "$f" || break
done
python ../importer/TextMapMedium.py    # 需要手动输入文件名，单独跑
```

> `drop + insert_many` 意味着脚本是**幂等**的：重复执行得到同样结果，但会清掉你手工往集合里追加的数据。

## 脚本与集合对照

| importer 脚本 | 源文件（`json/`） | 目标集合 | 说明 |
| --- | --- | --- | --- |
| `AttackAttenuationExcelConfigData.py` | `AttackAttenuationExcelConfigData.json` | `attack_attenuation` | `_id = group` |
| `AvatarExcelConfigData.py` | `AvatarExcelConfigData.json` | `avatar` | `_id = id`，跳过 `ICHCEGHCFJE` |
| `AvatarCodexExcelConfigData.py` | `AvatarCodexExcelConfigData.json` | `avatar_codex` | `_id = avatarId` |
| `AvatarCostumeExcelConfigData.py` | `AvatarCostumeExcelConfigData.json` | `avatar_costume` | `_id = skinId` |
| `AvatarCurveExcelConfigData.py` | `AvatarCurveExcelConfigData.json` | `avatar_curve` | `_id = level`，曲线类型取 `GGKIEIJLCJJ` |
| `AvatarFettersLevelExcelConfigData.py` | `AvatarFettersLevelExcelConfigData.json` | `avatar_fetters_level` | `_id = fetterLevel` |
| `AvatarLevelExcelConfigData.py` | `AvatarLevelExcelConfigData.json` | `avatar_level` | `_id = level` |
| `AvatarPromoteExcelConfigData.py` | `AvatarPromoteExcelConfigData.json` | `avatar_promote` | 按 `avatarPromoteId` 合并，缺 `promoteLevel` 补 0 |
| `AvatarSkillDepotExcelConfigData.py` | `AvatarSkillDepotExcelConfigData.json` | `avatar_skill_depot` | 3 个字段改名 + 嵌套 `unlockPromoteLevel` |
| `AvatarSkillExcelConfigData.py` | `AvatarSkillExcelConfigData.json` | `avatar_skill` | `_id = id` |
| `AvatarTalentExcelConfigData.py` | `AvatarTalentExcelConfigData.json` | `avatar_talent` | `_id = talentId` |
| `AvatarTraceEffectExcelConfigData.py` | `AvatarTraceEffectExcelConfigData.json` | `avatar_trace_effect` | `_id = avatarId`，跳过 `JLNHLCPGJBN` |
| `FetterCharacterCardExcelConfigData.py` | `FetterCharacterCardExcelConfigData.json` | `fetter_character_card` | 不设 `_id`（ObjectId） |
| `FetterInfoExcelConfigData.py` | `FetterInfoExcelConfigData.json` | `fetter_info` | `_id = avatarId`，3 个字段改名 |
| `FetterStoryExcelConfigData.py` | `FetterStoryExcelConfigData.json` | `fetter_story` | 不设 `_id` |
| `FettersExcelConfigData.py` | `FettersExcelConfigData.json` | `fetters` | 不设 `_id`，`tips` 元素转字符串 |
| `MaterialCodexExcelConfigData.py` | `MaterialCodexExcelConfigData.json` | `material_codex` | `_id = id` |
| `MaterialExcelConfigData.py` | `MaterialExcelConfigData.json` | `material` | `_id = id`，2 个字段改名 |
| `MaterialSourceDataExcelConfigData.py` | `MaterialSourceDataExcelConfigData.json` | `material_source_data` | `_id = id`，`HNNPIIJLLEK → sourceList` |
| `ProudSkillExcelConfigData.py` | `ProudSkillExcelConfigData.json` | `proud_skill` | `_id = proudSkillId`，2 个字段改名 |
| `TextMapMedium.py` | `TextMap_MediumCHS.json` | `text_map_chs_medium` | 交互输入文件名；先写 `*_array.json` 再入库 |

## 字段处理约定

所有脚本共享同一套清洗规则：

**1. 文档主键 `_id`**
大多数脚本把源记录的某个 `id` 类字段提升为 `_id` 并保留（等于没有 `id` 字段）。少数集合不设 `_id`，交给 MongoDB 生成 ObjectId：`fetters`、`fetter_story`、`fetter_character_card`。

**2. 哈希字段统一字符串化**
源数据中 `*Hash` 结尾的字段（`nameTextMapHash`、`descTextMapHash`…）是 64 位整数，统一 `str()` 后入库，避免精度/类型问题。配套地，源 JSON 里超过 2^53 的大整数只出现在 Hash 字段和混淆字段里，都会被这种规则处理掉。

**3. 混淆字段改名**

| 集合 | 原字段 | 新字段 |
| --- | --- | --- |
| `avatar_skill`、`avatar_talent`、`proud_skill` | `CJJODEPIILB` | `descExtraTextMapHash` |
| `proud_skill` | `NAOILGGDLNA` | `loreDescTextMapHash` |
| `material` | `LDKKLGEEGAP` / `PANBBKJOBOL` | `filterType` / `effectType` |
| `material_source_data` | `HNNPIIJLLEK` | `sourceList` |
| `avatar_skill_depot` | `LLEFDMDOMGG` / `KDCMKCFKPBL` / `PEAOICMBMKH` | `proudSkillGroups` / `specialProudSkillGroups` / `arkheType` |
| `avatar_skill_depot`（`proudSkillGroups` 元素内） | `DHIEHDPAFGI` | `unlockPromoteLevel` |
| `fetter_info` | `LCHFJFOMFGA` / `AAEINBDNBHL` / `PNIAJCCODBA` | `avatarPowerBeforTextMapHash` / `avatarPowerAfterTextMapHash` / `avatarNative2TextMapHash` |

**4. 值层面的改名**
`addProps` 数组元素里的 `GGKIEIJLCJJ` 改成 `value`（`avatar_promote` / `avatar_talent` / `proud_skill`）。

**5. 按设计保留的混淆字段**
并非所有混淆字段都要改名。`avatar` 的 `OBF_HASH` 白名单、`avatar_costume`、`avatar_trace_effect`、`material_source_data` 等集合里，部分字段按原样保留（只是值统一 `str()`），因为这些字段在源数据里就不是可读的明文字段名。

## 已知限制

- **`text_map_en_medium` 没有源数据**：目前只有 `TextMap_MediumCHS.json`，需要 EN 版时把 `TextMap_MediumEN.json` 放进 `json/`，`TextMapMedium.py` 会自动映射到 `text_map_en_medium`。
- **`TextMapMedium.py` 是交互式的**：要手动输入文件名，不能直接纳入上面的 `for` 循环。
- **以下集合没有对应导入脚本**：`weapon`（武器，来自 `WeaponExcelConfigData`，尚未提供源数据）、`avatar_ability`（由 `导入角色能力.py` 从 `avatar` 派生，不属于 Excel 导入）、`avatarBackup` / `avatarBu`（手工/自建集合）。
- **文本表对白覆盖率是数据源限制**：`proud_skill` 的 6273 条记录中只有 435 个 `nameTextMapHash` 能在 Medium 文本表里查到，这是 Medium 版文本表覆盖范围决定的，不是导入脚本的问题。
- **`json/` 不纳入版本控制**（约 67MB）。需要版本化时建议用 Git LFS，或删掉 `.gitignore` 里的 `json/` 行。

## 一致性校验

改动脚本后，可以用「假 `pymongo` + `runpy`」的方式做离线回归：把 `sys.modules["pymongo"]` 换成记录 `insert_many` 内容的桩，在 `json/` 下执行脚本，再与真库逐文档、逐字段（类型敏感）比对。

2026-10 的校验结果：落库的 20 个 Excel 脚本与原库 19 个集合**零差异**（按 `_id` 对齐），`text_map_chs_medium` 241738 条完全一致；唯一的偏差是 `proud_skill` 中两条历史文档的 `addProps` 保留了旧字段名 `GGKIEIJLCJJ`，已通过 `ProudSkillExcelConfigData.py` 的 `elif` 修复。

## 版本控制

`.gitignore` 忽略 `json/`、`__pycache__/`、编辑器目录。代码在 `main` 分支维护，提交本文档的仓库即当前仓库。

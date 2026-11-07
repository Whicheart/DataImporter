"""统一导入入口：按 SPECS 表把 ExcelBinOutput/ 的 JSON 导入 MongoDB。

用法（在 importer/ 目录或仓库根目录都能跑）：
    python ExcelConfigDataImporter.py --list                列出全部表与目标集合
    python ExcelConfigDataImporter.py --check               只跑预检，不连库
    python ExcelConfigDataImporter.py material              只导入指定表（集合名或文件名都行）
    python ExcelConfigDataImporter.py --all --dry-run       预演全部，只打印条数
    python ExcelConfigDataImporter.py --all                 真的入库

预检四道闸门，任何一道不过就整体放弃，库里一个字都不会动：
    1. 文件存在且能解析
    2. 混淆字段覆盖率必须 100%（FieldMap.json 决定每个混淆字段的去向）
    3. 哈希字段必须被命名或登记（标量 >2^53、整数数组 >2^31）
    4. 主键/分组键必须存在
"""
import os
import sys

from _common import (
    Context,
    PreflightError,
    SpecError,
    build_docs,
    check_docs,
    check_spec_keys,
    flatten_curves,
    load_field_map,
    load_records,
    scan_coverage,
    scan_hash_fields,
)

# ---------- 配置 ----------
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "GI"
ROOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


class Spec:
    """一张表的导入规格。"""

    def __init__(self, path, coll, id_key=None, group_by=None, level_key=None,
                 default_level=0, default_group=None, transform=None, pending=None, note=""):
        self.path = path                # 相对仓库根目录
        self.coll = coll                # 目标集合
        self.id_key = id_key            # 主键字段；None 表示不设 _id
        self.group_by = group_by        # 分组键；用于“一个键一文档”的表
        self.level_key = level_key      # 组内排序字段
        self.default_level = default_level
        self.default_group = default_group  # 分组键缺失时使用的值；None 表示不允许缺失
        self.transform = transform      # 额外的结构变换
        self.pending = pending          # 非空表示规格未定，禁止执行
        self.note = note


SPECS = [
    # ---------- 角色 ----------
    Spec("ExcelBinOutput/AvatarExcelConfigData.json", "avatar", id_key="id"),
    Spec("ExcelBinOutput/AvatarCodexExcelConfigData.json", "avatar_codex", id_key="avatarId"),
    Spec("ExcelBinOutput/AvatarCostumeExcelConfigData.json", "avatar_costume", id_key="skinId"),
    Spec("ExcelBinOutput/AvatarCurveExcelConfigData.json", "avatar_curve", id_key="level",
         transform=flatten_curves, note="curveInfos 拍平成 curves"),
    Spec("ExcelBinOutput/AvatarFettersLevelExcelConfigData.json", "avatar_fetters_level", id_key="fetterLevel"),
    Spec("ExcelBinOutput/AvatarLevelExcelConfigData.json", "avatar_level", id_key="level"),
    Spec("ExcelBinOutput/AvatarPromoteExcelConfigData.json", "avatar_promote",
         group_by="avatarPromoteId", level_key="promoteLevel", default_level=0),
    Spec("ExcelBinOutput/AvatarSkillDepotExcelConfigData.json", "avatar_skill_depot", id_key="id"),
    Spec("ExcelBinOutput/AvatarSkillExcelConfigData.json", "avatar_skill", id_key="id"),
    Spec("ExcelBinOutput/AvatarTalentExcelConfigData.json", "avatar_talent", id_key="talentId"),
    Spec("ExcelBinOutput/AvatarTraceEffectExcelConfigData.json", "avatar_trace_effect", id_key="avatarId"),

    # ---------- 圣遗物 ----------
    Spec("ExcelBinOutput/ReliquaryExcelConfigData.json", "reliquary", id_key="id"),
    Spec("ExcelBinOutput/ReliquaryAffixExcelConfigData.json", "reliquary_affix", id_key="id"),
    Spec("ExcelBinOutput/ReliquaryCodexExcelConfigData.json", "reliquary_codex", id_key="id"),
    Spec("ExcelBinOutput/ReliquaryLevelExcelConfigData.json", "reliquary_level",
         group_by="rank", level_key="level", default_level=0, default_group=0),
    Spec("ExcelBinOutput/ReliquaryMainPropExcelConfigData.json", "reliquary_main_prop", id_key="id"),
    Spec("ExcelBinOutput/ReliquarySetExcelConfigData.json", "reliquary_set", id_key="setId"),

    # ---------- 武器 ----------
    Spec("ExcelBinOutput/WeaponExcelConfigData.json", "weapon", id_key="id"),
    Spec("ExcelBinOutput/WeaponCodexExcelConfigData.json", "weapon_codex", id_key="id"),
    Spec("ExcelBinOutput/WeaponCurveExcelConfigData.json", "weapon_curve", id_key="level",
         transform=flatten_curves, note="curveInfos 拍平成 curves"),
    Spec("ExcelBinOutput/WeaponLevelExcelConfigData.json", "weapon_level", id_key="level"),
    Spec("ExcelBinOutput/WeaponPromoteExcelConfigData.json", "weapon_promote",
         group_by="weaponPromoteId", level_key="promoteLevel", default_level=0),
    Spec("ExcelBinOutput/EquipAffixExcelConfigData.json", "equip_affix",
         group_by="id", level_key="level", default_level=0),

    # ---------- 材料 ----------
    Spec("ExcelBinOutput/MaterialExcelConfigData.json", "material", id_key="id"),
    Spec("ExcelBinOutput/MaterialCodexExcelConfigData.json", "material_codex", id_key="id"),
    Spec("ExcelBinOutput/MaterialSourceDataExcelConfigData.json", "material_source_data", id_key="id"),

    # ---------- 天赋 / 技能 ----------
    Spec("ExcelBinOutput/ProudSkillExcelConfigData.json", "proud_skill", id_key="proudSkillId"),

    # ---------- 好感度 ----------
    Spec("ExcelBinOutput/FetterInfoExcelConfigData.json", "fetter_info", id_key="avatarId"),
    Spec("ExcelBinOutput/FettersExcelConfigData.json", "fetters", id_key=None, note="不设 _id"),
    Spec("ExcelBinOutput/FetterStoryExcelConfigData.json", "fetter_story", id_key=None, note="不设 _id"),
    Spec("ExcelBinOutput/FetterCharacterCardExcelConfigData.json", "fetter_character_card",
         id_key=None, note="不设 _id"),

    # ---------- 新增：Monster 系列与披风 ----------
    # 主键由用户逐张确认（2026-11-07）
    Spec("ExcelBinOutput/AvatarFlycloakExcelConfigData.json", "avatar_flycloak", id_key="id",
         note="源字段为混淆名 FBBOPPGICOK，映射后即 id"),
    Spec("ExcelBinOutput/MonsterExcelConfigData.json", "monster", id_key="id"),
    Spec("ExcelBinOutput/MonsterAffixExcelConfigData.json", "monster_affix", id_key="id"),
    Spec("ExcelBinOutput/MonsterCurveExcelConfigData.json", "monster_curve", id_key="level",
         transform=flatten_curves, note="curveInfos 拍平成 curves"),
    Spec("ExcelBinOutput/MonsterDescribeExcelConfigData.json", "monster_describe", id_key="id"),
    Spec("ExcelBinOutput/MonsterMultiPlayerExcelConfigData.json", "monster_multi_player",
         id_key="Id"),
    Spec("ExcelBinOutput/MonsterRelationshipExcelConfigData.json", "monster_relationship",
         id_key="id"),
    Spec("ExcelBinOutput/MonsterSpecialNameExcelConfigData.json", "monster_special_name",
         id_key="specialNameID"),
    Spec("ExcelBinOutput/MonsterTitleExcelConfigData.json", "monster_title", id_key="titleID"),
]


# ---------- 参数 ----------
def usage():
    print(__doc__.strip())


def select_specs(flags, names):
    if "--all" in flags:
        return list(SPECS)

    if not names:
        raise SpecError("请指定表名（集合名或文件名），或用 --all")

    picked = []
    for name in names:
        stem = os.path.splitext(os.path.basename(name))[0]
        hits = [s for s in SPECS if s.coll == name or os.path.splitext(os.path.basename(s.path))[0] == stem]
        if not hits:
            raise SpecError("找不到这张表：%s" % name)
        for spec in hits:
            if spec not in picked:
                picked.append(spec)
    return picked


def print_specs():
    print("%-30s %-28s %-16s %s" % ("源文件", "集合", "主键/分组", "备注"))
    print("-" * 92)
    for spec in SPECS:
        key = ("group:" + spec.group_by) if spec.group_by else (spec.id_key or "（无 _id）")
        note = spec.pending or spec.note
        print("%-30s %-28s %-16s %s" % (os.path.basename(spec.path), spec.coll, key, note))


# ---------- 主流程 ----------
def load_all(specs):
    records_by_path = {}
    for spec in specs:
        path = os.path.join(ROOT_DIR, spec.path)
        if not os.path.exists(path):
            raise SpecError("文件不存在：%s" % spec.path)
        try:
            records_by_path[spec.path] = load_records(path)
        except ValueError as exc:
            raise SpecError("JSON 解析失败：%s（%s）" % (spec.path, exc))
    return records_by_path


def preflight(specs, records_by_path, field_map):
    """四道闸门。通过返回占位名上下文，否则抛 PreflightError。"""
    missing, plain_keys, seen = scan_coverage(specs, records_by_path, field_map)
    if missing:
        lines = ["混淆字段覆盖率不足（%d/%d）：" % (len(seen) - len(missing), len(seen))]
        for token, count in sorted(missing.items(), key=lambda item: -item[1]):
            lines.append("  %-14s 出现 %d 次  → %s" % (token, count, field_map.describe(token)))
        lines.append("覆盖率未达 100%，已放弃入库。")
        raise PreflightError("\n".join(lines))

    problems = scan_hash_fields(specs, records_by_path, field_map)
    if problems:
        lines = ["哈希字段未登记（%d 处）：" % len(problems)]
        for path, key, reason in problems[:20]:
            lines.append("  %s  %s：%s" % (os.path.basename(path), key, reason))
        if len(problems) > 20:
            lines.append("  …… 其余 %d 处省略" % (len(problems) - 20))
        lines.append("请把它们登记到名字规则或 HASH_LIST_FIELDS 后重试。")
        raise PreflightError("\n".join(lines))

    key_problems = check_spec_keys(specs, records_by_path, field_map)
    if key_problems:
        lines = ["主键缺失："]
        for path, index, reason in key_problems:
            lines.append("  %s 第 %d 条：%s" % (os.path.basename(path), index + 1, reason))
        raise PreflightError("\n".join(lines))

    all_keys = set(field_map.rename) | field_map.drop | field_map.keep | set(field_map.placeholder)
    unused = sorted(all_keys - set(seen))
    if unused:
        print("提示：FieldMap 中有 %d 条未在本批数据里出现：%s"
              % (len(unused), "、".join(unused[:10]) + ("…" if len(unused) > 10 else "")))

    return Context(field_map, plain_keys)


def run(argv):
    if not argv or "--help" in argv:
        usage()
        return 0

    flags = {arg for arg in argv if arg.startswith("--")}
    names = [arg for arg in argv if not arg.startswith("--")]

    if "--list" in flags:
        print_specs()
        return 0

    specs = select_specs(flags, names)

    pending = [spec for spec in specs if spec.pending]
    if pending:
        print("以下表的主键还没确认，不能执行：")
        for spec in pending:
            print("  %s → %s" % (os.path.basename(spec.path), spec.coll))
        if "--skip-pending" not in flags:
            print("补全 SPECS 里的 id_key 后重试；确认要跳过请加 --skip-pending。")
            return 1
        specs = [spec for spec in specs if not spec.pending]

    field_map = load_field_map()
    try:
        records_by_path = load_all(specs)
    except PreflightError as exc:
        print(str(exc))
        return 1

    try:
        ctx = preflight(specs, records_by_path, field_map)
    except PreflightError as exc:
        print(str(exc))
        return 1

    all_docs = {}
    try:
        for spec in specs:
            docs = build_docs(spec, records_by_path[spec.path], ctx)
            check_docs(spec, docs)
            all_docs[spec.coll] = docs
    except PreflightError as exc:
        print("构建失败：%s" % exc)
        return 1

    total = sum(len(docs) for docs in all_docs.values())
    print("预检通过：%d 张表，共 %d 条文档。" % (len(specs), total))

    if "--check" in flags:
        return 0

    if "--dry-run" in flags:
        for spec in specs:
            print("  %-28s %6d 条" % (spec.coll, len(all_docs[spec.coll])))
        return 0

    from pymongo import MongoClient

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    for spec in specs:
        coll = db[spec.coll]
        coll.drop()
        coll.insert_many(all_docs[spec.coll])
        print("✓ %-28s %6d 条 → %s.%s" % (spec.coll, len(all_docs[spec.coll]), DB_NAME, spec.coll))
    client.close()
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))

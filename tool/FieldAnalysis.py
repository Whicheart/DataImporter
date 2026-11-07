import json
import os
import random
import re

from pymongo import MongoClient

# ---------- 配置 ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_DIR = os.path.join(BASE_DIR, "..", "ExcelBinOutput")         # JSON 数据目录
RENAME_FILE = os.path.join(BASE_DIR, "..", "FieldMap.json")      # 生成的字段映射文件
RESULT_FILE = os.path.join(BASE_DIR, "..", "AnalysisResult.txt")  # 分析结果输出文件
MONGO_URI = "mongodb://localhost:27017/"                          # BSON 数据库连接地址
DB_NAME = "GI"                                                    # BSON 数据库名

# 混淆字段判定：整段全大写字母且长度 >= 5（如 GGKIEIJLCJJ、DFGOJJFJODK）
OBF_PATTERN = re.compile(r"^[A-Z]{5,}$")

SAMPLE_SIZE = 5      # 每个字段路径取几个样本值
MAX_DISTINCT = 50    # 每个字段路径最多缓存多少个去重样本，避免大集合吃内存
MAX_VALUE_CHARS = 80 # 单个样本值的最大显示长度


def render_value(value):
    """把任意值渲染成一行字符串，供样本展示与去重。"""
    if isinstance(value, str):
        text = value
    elif isinstance(value, bool) or value is None or isinstance(value, (int, float)):
        text = repr(value)
    else:
        try:
            text = json.dumps(value, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError):
            text = repr(value)
    text = text.replace("\n", "\\n")
    if len(text) > MAX_VALUE_CHARS:
        text = text[:MAX_VALUE_CHARS] + "…"
    return text


def add_sample(stat, value):
    """记录一个样本：按渲染结果去重，最多保留 MAX_DISTINCT 个。"""
    text = render_value(value)
    if text in stat["samples"]:
        return
    if len(stat["samples"]) < MAX_DISTINCT:
        stat["samples"][text] = text


def walk(value, prefix, stats, source):
    """递归遍历一条记录，登记每个字段路径的出现次数、样本值与所属源。

    dict 的键记为 ``parent.key``；list 只在下钻到字典/列表元素时记 ``parent[]``，
    标量数组不产生额外路径（父字段本身已带整个数组作为样本）。
    """
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            stat = stats.setdefault(path, {"count": 0, "samples": {}, "sources": set()})
            stat["count"] += 1
            stat["sources"].add(source)
            add_sample(stat, child)
            walk(child, path, stats, source)
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (dict, list)):
                walk(item, prefix + "[]", stats, source)


def field_name(path):
    """从字段路径里取出字段名，用于混淆判定。"""
    name = path.rsplit(".", 1)[-1]
    while name.endswith("[]"):
        name = name[:-2]
    return name


def is_obfuscated(path):
    return bool(OBF_PATTERN.fullmatch(field_name(path)))


def analyze(records, stats, source):
    for record in records:
        walk(record, "", stats, source)


def report(stats):
    """按混淆/明文分组整理字段路径、出现次数与样本值，写入 AnalysisResult.txt。"""
    obf = sorted((p for p in stats if is_obfuscated(p)), key=lambda p: (-stats[p]["count"], p))
    plain = sorted((p for p in stats if not is_obfuscated(p)), key=lambda p: (-stats[p]["count"], p))

    lines = []
    for title, paths in (("混淆字段", obf), ("明文字段", plain)):
        lines.append(f"=== {title}（{len(paths)} 个字段路径）===")
        if not paths:
            lines.append("（无）")
            lines.append("")
            continue
        for path in paths:
            stat = stats[path]
            samples = random.sample(sorted(stat["samples"]), min(SAMPLE_SIZE, len(stat["samples"])))
            sources = sorted(stat["sources"])
            shown = "、".join(sources[:5]) + (f" 等 {len(sources)} 个" if len(sources) > 5 else "")
            lines.append(f"路径: {path}")
            lines.append(f"    所属: {shown}")
            lines.append(f"    出现次数: {stat['count']}")
            lines.append(f"    样本值: {' | '.join(samples) if samples else '（无）'}")
            lines.append("")

    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✓ 分析结果已写入 {os.path.normpath(RESULT_FILE)}（混淆 {len(obf)} 个、明文 {len(plain)} 个字段路径）")
    return obf


def write_rename_file(obf_paths):
    """把混淆字段写成 {混淆字段: 混淆字段} 的 json，已存在的文件保留用户已填的值。"""
    names = sorted({field_name(p) for p in obf_paths})
    existing = {}
    if os.path.isfile(RENAME_FILE):
        with open(RENAME_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
    merged = {name: existing.get(name, name) for name in names}
    for name, value in existing.items():
        merged.setdefault(name, value)
    with open(RENAME_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\n已生成 {os.path.normpath(RENAME_FILE)}：{len(names)} 个混淆字段，值默认等于键名，待你填写明文名。")


def ask_choice(prompt, options):
    """把选项列出来让用户选，返回选中的一组（支持 0 / all 表示全部）。"""
    print(prompt)
    for index, (label, _) in enumerate(options, 1):
        print(f"  {index}) {label}")
    print("  0) 全部")
    while True:
        answer = input("请输入序号（或直接输入名称，0 表示全部）：").strip()
        if answer in ("0", "all", "全部"):
            return [value for _, value in options]
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return [options[int(answer) - 1][1]]
        for label, value in options:
            if answer == label or answer == value:
                return [value]
        print("输入无效，请重试。")


def analyze_json():
    if not os.path.isdir(JSON_DIR):
        raise FileNotFoundError(f"JSON 目录不存在：{os.path.normpath(JSON_DIR)}")
    files = sorted(f for f in os.listdir(JSON_DIR) if f.lower().endswith(".json"))
    if not files:
        raise RuntimeError(f"目录里没有 json 文件：{os.path.normpath(JSON_DIR)}")
    options = [(name, name) for name in files]
    chosen = ask_choice(f"ExcelBinOutput/ 下共 {len(files)} 个文件，选择要分析的文件：", options)

    stats = {}
    for name in chosen:
        with open(os.path.join(JSON_DIR, name), "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        records = data if isinstance(data, list) else [data]
        print(f"\n>>> 分析 {name}（{len(records)} 条记录）")
        analyze(records, stats, name)
    report(stats)
    return stats


def analyze_bson():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    names = sorted(db.list_collection_names())
    if not names:
        raise RuntimeError(f"数据库 {DB_NAME} 里没有集合")
    options = [(f"{name}（{db[name].count_documents({})} 条）", name) for name in names]
    chosen = ask_choice(f"数据库 {DB_NAME} 共 {len(names)} 个集合，选择要分析的集合：", options)

    stats = {}
    for name in chosen:
        total = db[name].count_documents({})
        print(f"\n>>> 分析集合 {name}（{total} 条记录）")
        for record in db[name].find({}):
            walk(record, "", stats, name)
    client.close()
    report(stats)
    return stats


def main():
    print("请选择分析类型：")
    print("  1) JSON 文件")
    print("  2) BSON 集合")
    while True:
        answer = input("请输入序号：").strip()
        if answer in ("1", "json", "JSON"):
            stats = analyze_json()
            break
        if answer in ("2", "bson", "BSON"):
            stats = analyze_bson()
            break
        print("输入无效，请重试。")

    obf_paths = [p for p in stats if is_obfuscated(p)]
    if obf_paths:
        write_rename_file(obf_paths)
    else:
        print("\n没有发现混淆字段，未生成映射文件。")


if __name__ == "__main__":
    main()

import json
import os
import unicodedata

# ---------- 配置 ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_DIR = os.path.join(BASE_DIR, "..", "ExcelBinOutput")  # JSON 数据目录
MONGO_URI = "mongodb://localhost:27017/"                   # BSON 数据库连接地址
DB_NAME = "GI"                                             # BSON 数据库名

# 本脚本只读：只打开文件读取、只执行 find 查询，不写文件、不写数据库。


def type_name(value):
    """把一个值映射成可读的类型名。"""
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if value is None:
        return "null"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return type(value).__name__


def walk(value, prefix, stats):
    """递归遍历一条记录，登记每个字段路径与出现过的类型。

    dict 的键记为 ``parent.key``；list 只在下钻到字典/列表元素时记 ``parent[]``，
    标量数组不产生额外路径（父字段本身已代表整个数组）。
    """
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            stat = stats.setdefault(path, {"count": 0, "types": []})
            stat["count"] += 1
            name = type_name(child)
            if name not in stat["types"]:
                stat["types"].append(name)
            walk(child, path, stats)
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (dict, list)):
                walk(item, prefix + "[]", stats)


def disp_width(text):
    """按终端显示宽度计算字符串宽度（中文等全角字符算 2 列）。"""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def pad(text, width):
    """把字符串补齐到指定显示宽度。"""
    return text + " " * (width - disp_width(text))


def report(title, records, stats):
    """把登记结果打印成对齐的表格。"""
    print(f"\n>>> {title}（{len(records)} 条记录）")
    if not stats:
        print("    没有可展示的字段。")
        return

    rows = []
    for path, stat in stats.items():
        types = " | ".join(stat["types"])
        if len(stat["types"]) > 1:
            types += "（不一致）"
        rows.append((path, types, stat["count"]))

    path_width = max(disp_width("路径"), max(disp_width(r[0]) for r in rows))
    type_width = max(disp_width("类型"), max(disp_width(r[1]) for r in rows))
    print(f"\n字段路径（共 {len(rows)} 个）：")
    print(f"  {pad('路径', path_width)}  {pad('类型', type_width)}  出现次数")
    print(f"  {'-' * path_width}  {'-' * type_width}  --------")
    for path, types, count in rows:
        print(f"  {pad(path, path_width)}  {pad(types, type_width)}  {count}")


def ask_single(prompt, options):
    """列出选项让用户选一个，返回 (label, value)。"""
    print(prompt)
    for index, (label, _) in enumerate(options, 1):
        print(f"  {index}) {label}")
    while True:
        answer = input("请输入序号（或直接输入名称）：").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return options[int(answer) - 1]
        for label, value in options:
            if answer == label or answer == value:
                return label, value
        print("输入无效，请重试。")


def analyze_json():
    if not os.path.isdir(JSON_DIR):
        raise FileNotFoundError(f"JSON 目录不存在：{os.path.normpath(JSON_DIR)}")
    files = sorted(f for f in os.listdir(JSON_DIR) if f.lower().endswith(".json"))
    if not files:
        raise RuntimeError(f"目录里没有 json 文件：{os.path.normpath(JSON_DIR)}")

    name, _ = ask_single(f"ExcelBinOutput/ 下共 {len(files)} 个文件，选择要分析的文件：",
                         [(f, f) for f in files])

    with open(os.path.join(JSON_DIR, name), "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    records = data if isinstance(data, list) else [data]

    stats = {}
    for record in records:
        walk(record, "", stats)
    report(name, records, stats)


def analyze_bson():
    from pymongo import MongoClient

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    try:
        db = client[DB_NAME]
        names = sorted(db.list_collection_names())
        if not names:
            raise RuntimeError(f"数据库 {DB_NAME} 里没有集合")

        options = [(f"{n}（{db[n].count_documents({})} 条）", n) for n in names]
        _, chosen = ask_single(f"数据库 {DB_NAME} 共 {len(names)} 个集合，选择要分析的集合：", options)

        records = list(db[chosen].find({}))
        stats = {}
        for record in records:
            walk(record, "", stats)
        report(f"{DB_NAME}.{chosen}", records, stats)
    finally:
        client.close()


def main():
    print("请选择数据来源：")
    print("  1) JSON 文件（ExcelBinOutput/）")
    print("  2) BSON 集合（数据库）")
    while True:
        answer = input("请输入序号：").strip()
        if answer in ("1", "json", "JSON"):
            analyze_json()
            break
        if answer in ("2", "bson", "BSON"):
            analyze_bson()
            break
        print("输入无效，请重试。")


if __name__ == "__main__":
    main()

import json
import os
import re
from collections import Counter


def choose_json_file():
    """列出当前目录下的 .json 文件，让用户选序号或输入文件名"""
    files = sorted(f for f in os.listdir(".") if f.lower().endswith(".json"))
    if not files:
        print("当前目录下没有 .json 文件")
        raise SystemExit(1)

    print("可选的 JSON 文件：")
    for i, f in enumerate(files, 1):
        print(f"  [{i}] {f}")

    while True:
        raw = input("\n请输入序号或文件名：").strip()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(files):
                return files[idx]
            print("序号越界，请重新输入")
        elif raw in files:
            return raw
        else:
            print("无效输入，请重新输入")


PATH = choose_json_file()

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# 结构检查：只支持 [{...}, ...] 这种顶层是数组的结构
if not isinstance(data, list) or not data or not isinstance(data[0], dict):
    print(f"\n错误：{PATH} 不是 [{...}, ...] 结构")
    raise SystemExit(1)

print(f"\n已选择：{PATH}\n")

key_counter = Counter()
value_samples = {}  # path -> list，最多存 5 个值


def traverse(obj, current_path=""):
    """
    递归遍历 JSON 对象，提取所有层级字段的路径及其对应的值。
    如果是数组内部的对象，路径会带上 []，例如 "propGrowCurves[].growCurve"
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            # 拼接当前路径（如果当前路径为空，就直接用字段名）
            path = f"{current_path}.{k}" if current_path else k
            yield path, v
            # 继续向内部深挖
            yield from traverse(v, path)
    elif isinstance(obj, list):
        for item in obj:
            # 数组本身不产生新字段，但如果里面是字典，就继续挖
            yield from traverse(item, f"{current_path}[]")


# 开始深度遍历收集数据
for rec in data:
    if not isinstance(rec, dict):
        continue
    for path, v in traverse(rec):
        key_counter[path] += 1
        lst = value_samples.setdefault(path, [])
        if len(lst) < 5:
            lst.append(v)

ALL_CAPS = re.compile(r"^[A-Z]+$")
VOWELS = set("AEIOUaeiou")


def get_real_key(path):
    """从带层级的路径中提取最后的真实字段名，例如 'a[].b' 提取出 'b'"""
    last_part = path.split(".")[-1]
    return last_part.replace("[]", "")


def is_suspicious(path):
    """判断字段名是否可疑（基于最后的真实字段名）"""
    key = get_real_key(path)

    try:
        key.encode("ascii")
    except UnicodeEncodeError:
        return True, ["含非ASCII字符"]

    if ALL_CAPS.match(key) and len(key) >= 5:
        reasons = ["纯大写字母"]
        v = sum(1 for c in key if c in VOWELS)
        if v / len(key) < 0.2:
            reasons.append("元音比例低(随机串特征)")
        return True, reasons

    if not re.match(r"^[A-Za-z_]", key):
        return True, ["非法开头字符"]

    return False, []


suspicious, normal = [], []
for path in sorted(key_counter, key=lambda x: -key_counter[x]):
    bad, reasons = is_suspicious(path)
    (suspicious if bad else normal).append((path, key_counter[path], reasons))

print(f"总记录数      : {len(data)}")
print(f"总字段路径数  : {len(key_counter)}")
print(f"疑似混淆字段数: {len(suspicious)}")
print()


def fmt(v):
    """把值格式化成一行，对象/列表转 JSON，字符串加引号"""
    try:
        s = json.dumps(v, ensure_ascii=False)
    except Exception:
        s = repr(v)
    return s if len(s) <= 80 else s[:77] + "..."


print("=== 疑似混淆字段 ===")
for path, c, r in suspicious:
    vals = value_samples.get(path, [])
    print(f"\n字段路径 {path!r}   出现 {c} 次   原因={','.join(r)}")
    print(f"  样本值({len(vals)}个):")
    for i, v in enumerate(vals, 1):
        print(f"    [{i}] {fmt(v)}")

print("\n=== 正常字段（对照） ===")
for path, c, _ in normal:
    # 如果路径里包含 [] 或 . 说明是嵌套字段，为了对齐稍微加长一点
    print(f"  {path!r:40s} 出现 {c:5d} 次")
import re
import json
from collections import Counter
from pymongo import MongoClient

# ---------- 数据库配置 ----------
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "GI"

# ---------- 连接数据库并选择集合 ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]

colls = sorted(db.list_collection_names())
if not colls:
    print(f"数据库 {DB_NAME} 中没有任何集合")
    raise SystemExit(1)

print("可选的集合：")
for i, c in enumerate(colls, 1):
    print(f"  [{i}] {c}")

while True:
    raw = input("\n请输入序号或集合名：").strip()
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(colls):
            coll_name = colls[idx]
            break
        print("序号越界，请重新输入")
    elif raw in colls:
        coll_name = raw
        break
    else:
        print("无效输入，请重新输入")

coll = db[coll_name]
print(f"\n已选择集合：{coll_name}，正在读取数据...\n")

# ---------- 读取集合数据 ----------
# 直接遍历游标，防止一次性全加载进内存（虽然这些表数据量很小，但养成好习惯）
data = list(coll.find())
if not data:
    print("该集合没有数据")
    raise SystemExit(1)

key_counter = Counter()
value_samples = {}  # path -> list，最多存 5 个值


def traverse(obj, current_path=""):
    """
    递归遍历 MongoDB 文档，提取所有层级字段的路径及其对应的值。
    数组内部对象的路径带 []，例如 "curveInfos[].type"
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{current_path}.{k}" if current_path else k
            yield path, v
            yield from traverse(v, path)
    elif isinstance(obj, list):
        for item in obj:
            yield from traverse(item, f"{current_path}[]")


# 开始深度遍历收集数据
for rec in data:
    if not isinstance(rec, dict):
        continue
    for path, v in traverse(rec):
        key_counter[path] += 1
        lst = value_samples.setdefault(path, [])
        if len(lst) < 5:
            # 数据库里的特殊类型（如 Int64）转成标准 int 方便打印
            if hasattr(v, "item"):
                v = v.item()
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
        # MongoDB 的 ObjectId 或特殊类型无法直接 json.dumps，兜底用 repr
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
    print(f"  {path!r:40s} 出现 {c:5d} 次")

# 释放连接
client.close()
import json
from collections import defaultdict

from pymongo import MongoClient

# ---------- 配置 ----------
PATH = "json/ReliquaryLevelExcelConfigData.json"  # 数据文件路径（相对仓库根目录）
MONGO_URI = "mongodb://localhost:27017/"          # MongoDB 连接地址
DB_NAME = "GI"                                    # 数据库名
COLL_NAME = "reliquary_level"                     # 集合名


def is_hash_field(k):
    """判断字段是否为 hash：明文名以 Hash 结尾"""
    return k.endswith("Hash")


# ---------- 读取数据 ----------
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 转换：按 rank 分组，同一 rank 的各等级放进 levels 数组 ----------
# addProps 元素里的 GGKIEIJLCJJ 是已知明文的混淆字段，改名为 value
groups = defaultdict(list)
for rec in data:
    rank = rec.get("rank") or 0  # 首条缺少 rank，补 0
    level_rec = {}
    for k, v in rec.items():
        if k == "rank":
            continue

        if k == "addProps" and isinstance(v, list):
            new_props = []
            for prop in v:
                new_prop = {}
                for pk, pv in prop.items():
                    if pk == "GGKIEIJLCJJ":
                        new_prop["value"] = pv
                    else:
                        new_prop[pk] = pv
                new_props.append(new_prop)
            level_rec[k] = new_props

        # 顶层 Hash 字段转字符串
        elif is_hash_field(k) and v is not None:
            level_rec[k] = str(v)

        else:
            level_rec[k] = v

    groups[rank].append(level_rec)

docs = [
    {
        "_id": rank,  # 以 rank 作为主键
        "levels": sorted(levels, key=lambda x: x["level"]),
    }
    for rank, levels in sorted(groups.items())
]

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()                 # 清空旧数据
coll.insert_many(docs)      # 6 个 rank 一次插完
print(f"✓ 导入 {len(docs)} 个 rank 的等级数据 → {DB_NAME}.{COLL_NAME}")

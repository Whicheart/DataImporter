import json
from collections import defaultdict
from pymongo import MongoClient

# ---------- 配置 ----------
PATH = "json/EquipAffixExcelConfigData.json"  # 数据文件路径（相对仓库根目录）
MONGO_URI = "mongodb://localhost:27017/"      # MongoDB 连接地址
DB_NAME = "GI"                                # 数据库名
COLL_NAME = "equip_affix"                     # 集合名


def is_hash_field(k):
    """判断字段是否为 hash：明文名以 Hash 结尾"""
    return k.endswith("Hash")


# ---------- 读取数据 ----------
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 按 id 分组 ----------
grouped_data = defaultdict(list)

for rec in data:
    # 提取主键
    affix_id = rec.pop("id")    # 使用 pop 把该字段移除，后续不再重复存储

    # 有些记录（基础档）没有 level 字段，默认补 0
    if "level" not in rec:
        rec["level"] = 0

    # addProps 里的 GGKIEIJLCJJ 是已知明文字段 value
    if "addProps" in rec and isinstance(rec["addProps"], list):
        for prop in rec["addProps"]:
            if "GGKIEIJLCJJ" in prop:
                prop["value"] = prop.pop("GGKIEIJLCJJ")

    # hash 字段转字符串
    for k, v in rec.items():
        if is_hash_field(k) and v is not None:
            rec[k] = str(v)

    grouped_data[affix_id].append(rec)

# ---------- 构造最终文档 ----------
docs = []
for affix_id, levels in grouped_data.items():
    # 按 level 排序（0 是基础档，1~4 是精炼等级）
    levels.sort(key=lambda x: x["level"])

    doc = {
        "_id": affix_id,
        "levels": levels
    }
    docs.append(doc)

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()                 # 清空旧数据
coll.insert_many(docs)      # 1412 条被整合成 344 个文档（每个 affix 组一个）
print(f"✓ 导入 {len(docs)} 个 affix 组 → {DB_NAME}.{COLL_NAME}")

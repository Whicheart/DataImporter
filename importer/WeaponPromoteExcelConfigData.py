import json
from collections import defaultdict
from pymongo import MongoClient

# ---------- 配置 ----------
PATH = "WeaponPromoteExcelConfigData.json"  # 数据文件路径
MONGO_URI = "mongodb://localhost:27017/"    # MongoDB 连接地址
DB_NAME = "GI"                              # 数据库名
COLL_NAME = "weapon_promote"                # 集合名

# ---------- 读取数据 ----------
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 按 weaponPromoteId 分组 ----------
grouped_data = defaultdict(list)

for rec in data:
    # 提取主键
    promote_id = rec.pop("weaponPromoteId")  # 使用 pop 把该字段移除，后续不再重复存储
    # 有些记录没有 promoteLevel 字段，默认补 0 阶（基础属性那一档）
    if "promoteLevel" not in rec:
        rec["promoteLevel"] = 0

    # addProps 里的 GGKIEIJLCJJ 是已知明文字段 value
    if "addProps" in rec and isinstance(rec["addProps"], list):
        for prop in rec["addProps"]:
            if "GGKIEIJLCJJ" in prop:
                prop["value"] = prop.pop("GGKIEIJLCJJ")

    grouped_data[promote_id].append(rec)

# ---------- 构造最终文档 ----------
docs = []
for promote_id, levels in grouped_data.items():
    # 按 promoteLevel 排序（从 0 到 6）
    levels.sort(key=lambda x: x["promoteLevel"])

    doc = {
        "_id": promote_id,
        "levels": levels
    }
    docs.append(doc)

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()  # 清空旧数据
coll.insert_many(docs)  # 1814 条被整合成若干个文档（每把武器一个）
print(f"✓ 导入 {len(docs)} 个武器突破数据 → {DB_NAME}.{COLL_NAME}")

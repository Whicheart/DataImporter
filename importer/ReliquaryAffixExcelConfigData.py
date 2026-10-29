import json
from pymongo import MongoClient

# ---------- 配置 ----------
PATH = "json/ReliquaryAffixExcelConfigData.json"  # 数据文件路径（相对仓库根目录）
MONGO_URI = "mongodb://localhost:27017/"          # MongoDB 连接地址
DB_NAME = "GI"                                    # 数据库名
COLL_NAME = "reliquary_affix"                     # 集合名


def is_hash_field(k):
    """判断字段是否为 hash：明文名以 Hash 结尾"""
    return k.endswith("Hash")


# ---------- 读取数据 ----------
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 转换：id → _id，*Hash → 字符串 ----------
# 记录形如 {id, groupId, depotId, propType, propValue}，propType/propValue 已是明文
docs = []
for rec in data:
    new_rec = {"_id": rec["id"]}
    for k, v in rec.items():
        if k == "id":
            continue
        new_rec[k] = str(v) if is_hash_field(k) and v is not None else v
    docs.append(new_rec)

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()                 # 清空旧数据
coll.insert_many(docs)      # 350 条一次插完
print(f"✓ 导入 {len(docs)} 条 → {DB_NAME}.{COLL_NAME}")

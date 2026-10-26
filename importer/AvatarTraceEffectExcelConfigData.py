import json
from pymongo import MongoClient

# ---------- 配置 ----------
PATH = "AvatarTraceEffectExcelConfigData.json"  # 数据文件路径
MONGO_URI = "mongodb://localhost:27017/"  # MongoDB 连接地址
DB_NAME = "GI"  # 数据库名
COLL_NAME = "avatar_trace_effect"  # 集合名

# 混淆字段没有哈希，全是普通 ID 或特效路径，所以留空
OBF_HASH = set()


def is_hash_field(k):
    """判断字段是否为 hash：明文名以 Hash 结尾"""
    return k.endswith("Hash") or k in OBF_HASH


# ---------- 读取数据 ----------
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 转换：avatarId 作为主键 _id；明文 Hash 字段转字符串 ----------
docs = []
for rec in data:
    new_rec = {
        "_id": rec["avatarId"]
    }
    for k, v in rec.items():
        if k == "avatarId":
            continue
        if k == "JLNHLCPGJBN":
            continue
        # 只有以 Hash 结尾的（如 nameTextMapHash, descTextMapHash）转字符串
        # JLNHLCPGJBN 等其他 ID 原样保留 Int
        new_rec[k] = str(v) if is_hash_field(k) and v is not None else v

    docs.append(new_rec)

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()  # 清空旧数据
coll.insert_many(docs)  # 23 条一次插完
print(f"✓ 导入 {len(docs)} 条 → {DB_NAME}.{COLL_NAME}")
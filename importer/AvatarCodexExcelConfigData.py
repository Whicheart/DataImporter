import json
from pymongo import MongoClient

# ---------- 配置 ----------
PATH = "AvatarCodexExcelConfigData.json"   # 数据文件路径
MONGO_URI = "mongodb://localhost:27017/"    # MongoDB 连接地址
DB_NAME = "GI"                              # 数据库名
COLL_NAME = "avatar_codex"                  # 集合名

# ---------- 读取数据 ----------
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 转换：avatarId 作为主键 _id ----------
# 这张表没有内置 id，avatarId 在图鉴表中是唯一的
# 混淆字段 OOBINIPDJEF 值为布尔 true，直接原样保留
docs = []
for rec in data:
    new_rec = {
        "_id": rec["avatarId"]
    }
    for k, v in rec.items():
        if k == "avatarId":
            continue
        new_rec[k] = v
    docs.append(new_rec)

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()                 # 清空旧数据
coll.insert_many(docs)      # 122 条一次插完
print(f"✓ 导入 {len(docs)} 条 → {DB_NAME}.{COLL_NAME}")
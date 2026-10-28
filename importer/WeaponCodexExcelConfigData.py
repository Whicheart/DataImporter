import json
from pymongo import MongoClient

# ---------- 配置 ----------
PATH = "WeaponCodexExcelConfigData.json"    # 数据文件路径
MONGO_URI = "mongodb://localhost:27017/"    # MongoDB 连接地址
DB_NAME = "GI"                              # 数据库名
COLL_NAME = "weapon_codex"                  # 集合名

# ---------- 读取数据 ----------
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 转换：id 作为主键 _id，保留 weaponId 作为图鉴到武器的引用 ----------
docs = []
for rec in data:
    new_rec = {
        "_id": rec["id"]        # 用图鉴条目 ID 作为主键
    }
    for k, v in rec.items():
        if k == "id":
            continue
        # AMGNJIFGKJE 等混淆字段没有已知明文，按原样保留
        new_rec[k] = v

    docs.append(new_rec)

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()                 # 清空旧数据
coll.insert_many(docs)      # 255 条一次插完
print(f"✓ 导入 {len(docs)} 条 → {DB_NAME}.{COLL_NAME}")

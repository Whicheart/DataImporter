import json
from pymongo import MongoClient

# ---------- 配置 ----------
PATH = "AvatarFettersLevelExcelConfigData.json"   # 数据文件路径
MONGO_URI = "mongodb://localhost:27017/"           # MongoDB 连接地址
DB_NAME = "GI"                                     # 数据库名
COLL_NAME = "avatar_fetters_level"                 # 集合名

# ---------- 读取数据 ----------
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 转换：fetterLevel 作为主键 _id，保留 needExp ----------
docs = []
for rec in data:
    new_rec = {
        "_id": rec["fetterLevel"],    # 好感度等级作为主键
        "needExp": rec["needExp"]     # 升到该等级所需好感度
    }
    docs.append(new_rec)

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()                 # 清空旧数据
coll.insert_many(docs)      # 10 条一次插完
print(f"✓ 导入 {len(docs)} 条 → {DB_NAME}.{COLL_NAME}")

# ---------- 验证 ----------
print("\n验证数据：")
print("1级:", coll.find_one({"_id": 1}))
print("10级:", coll.find_one({"_id": 10}))
import json
from pymongo import MongoClient

# ---------- 配置 ----------
PATH = "json/AvatarLevelExcelConfigData.json"  # 数据文件路径（相对仓库根目录）
MONGO_URI = "mongodb://localhost:27017/"       # MongoDB 连接地址
DB_NAME = "GI"                                 # 数据库名
COLL_NAME = "avatar_level"                     # 集合名

# ---------- 读取数据 ----------
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 转换：level 作为主键 _id，保留 exp ----------
docs = []
for rec in data:
    new_rec = {
        "_id": rec["level"],    # 等级作为主键
        "exp": rec["exp"]       # 升到下一级所需经验
    }
    docs.append(new_rec)

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()                 # 清空旧数据
coll.insert_many(docs)      # 90 条一次插完
print(f"✓ 导入 {len(docs)} 条 → {DB_NAME}.{COLL_NAME}")

# ---------- 验证：打印 1 级和 90 级的数据 ----------
print("\n验证数据：")
print("1级:", coll.find_one({"_id": 1}))
print("90级:", coll.find_one({"_id": 90}))
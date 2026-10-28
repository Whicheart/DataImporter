import json
from pymongo import MongoClient

# ---------- 配置 ----------
PATH = "json/FetterStoryExcelConfigData.json"  # 数据文件路径（相对仓库根目录）
MONGO_URI = "mongodb://localhost:27017/"       # MongoDB 连接地址
DB_NAME = "GI"                                 # 数据库名
COLL_NAME = "fetter_story"                     # 集合名

def is_hash_field(k):
    """判断字段是否为 hash：明文名以 Hash 结尾"""
    return k.endswith("Hash")

# ---------- 读取数据 ----------
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 转换 ----------
# 放弃指定 _id，让 MongoDB 自动生成（因为一个角色有多篇故事，avatarId 不唯一）
docs = []
for rec in data:
    new_rec = {}
    for k, v in rec.items():
        if is_hash_field(k) and v is not None:
            new_rec[k] = str(v)
        elif k == "tips" and isinstance(v, list):
            # tips 数组里全是大数 Hash，统一转字符串
            new_rec[k] = [str(item) for item in v]
        else:
            new_rec[k] = v
    docs.append(new_rec)

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()                 # 清空旧数据
coll.insert_many(docs)      # 974 条一次插完
print(f"✓ 导入 {len(docs)} 条 → {DB_NAME}.{COLL_NAME}")
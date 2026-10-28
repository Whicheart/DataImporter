import json
from pymongo import MongoClient

# ---------- 配置 ----------
PATH = "json/MaterialExcelConfigData.json"  # 数据文件路径（相对仓库根目录）
MONGO_URI = "mongodb://localhost:27017/"    # MongoDB 连接地址
DB_NAME = "GI"                              # 数据库名
COLL_NAME = "material"                      # 集合名（严格按文件名）

RENAME_MAP = {
    "LDKKLGEEGAP": "filterType",
    "PANBBKJOBOL": "effectType"
}

def is_hash_field(k):
    """判断字段是否为 hash：明文名以 Hash 结尾"""
    return k.endswith("Hash")

# ---------- 读取数据 ----------
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 转换：id 作为主键 _id；hash 字段转字符串 ----------
docs = []
for rec in data:
    new_rec = {
        "_id": rec["id"]        # 提取物品 ID 作为主键
    }
    for k, v in rec.items():
        if k == "id":
            continue

        actual_key = RENAME_MAP.get(k, k)

        # Hash 字段转字符串；其他的（包括那 5 个混淆的枚举/布尔）原样保留
        new_rec[actual_key] = str(v) if is_hash_field(actual_key) and v is not None else v

    docs.append(new_rec)

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()                 # 清空旧数据
coll.insert_many(docs)      # 10512 条一次插完
print(f"✓ 导入 {len(docs)} 条 → {DB_NAME}.{COLL_NAME}")
import json
from pymongo import MongoClient

# ---------- 配置 ----------
PATH = "json/ReliquarySetExcelConfigData.json"  # 数据文件路径（相对仓库根目录）
MONGO_URI = "mongodb://localhost:27017/"        # MongoDB 连接地址
DB_NAME = "GI"                                  # 数据库名
COLL_NAME = "reliquary_set"                     # 集合名

# 混淆字段 → 明文
RENAME_MAP = {
    "LAJGLFNPLCP": "maxRankLevel",
}


def is_hash_field(k):
    """判断字段是否为 hash：明文名以 Hash 结尾"""
    return k.endswith("Hash")


# ---------- 读取数据 ----------
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 转换：setId → _id，混淆字段改名，*Hash / textList → 字符串 ----------
docs = []
for rec in data:
    new_rec = {"_id": rec["setId"]}
    for k, v in rec.items():
        if k == "setId":
            continue
        actual_key = RENAME_MAP.get(k, k)

        # textList 名字里没有 Hash，但元素全是文本哈希，统一转字符串
        if actual_key == "textList" and isinstance(v, list):
            new_rec[actual_key] = [str(item) for item in v]

        elif is_hash_field(actual_key) and v is not None:
            new_rec[actual_key] = str(v)

        else:
            new_rec[actual_key] = v
    docs.append(new_rec)

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()                 # 清空旧数据
coll.insert_many(docs)      # 66 条一次插完
print(f"✓ 导入 {len(docs)} 条 → {DB_NAME}.{COLL_NAME}")

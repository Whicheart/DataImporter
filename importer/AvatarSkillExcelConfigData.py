import json
from pymongo import MongoClient

# ---------- 配置 ----------
PATH = "AvatarSkillExcelConfigData.json"   # 数据文件路径
MONGO_URI = "mongodb://localhost:27017/"    # MongoDB 连接地址
DB_NAME = "GI"                              # 数据库名
COLL_NAME = "avatar_skill"                  # 集合名（要跟 raw_avatar_excel 风格统一可改 raw_avatar_skill）

OBF_HASH = set()

def is_hash_field(k):
    """判断字段是否为 hash：明文名以 Hash 结尾，或属于混淆 hash 白名单"""
    return k.endswith("Hash") or k in OBF_HASH

# ---------- 读取数据 ----------
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 转换：id → _id 作主键；hash 字段转字符串；其余保留原字段原值 ----------
docs = []
for rec in data:
    new_rec = {"_id": rec["id"]}            # 原 id 字段直接作为 _id 主键
    for k, v in rec.items():
        if k == "id":                       # 已转 _id，跳过原字段
            continue

        if k == "CJJODEPIILB":
            k = "descExtraTextMapHash"

        new_rec[k] = str(v) if is_hash_field(k) and v is not None else v
    docs.append(new_rec)

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()                 # 清空旧数据
coll.insert_many(docs)      # 1149 条一次插完不分批
print(f"✓ 导入 {len(docs)} 条 → {DB_NAME}.{COLL_NAME}")
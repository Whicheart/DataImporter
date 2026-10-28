import json
from pymongo import MongoClient

# ---------- 配置 ----------
PATH = "json/AvatarCostumeExcelConfigData.json"  # 数据文件路径（相对仓库根目录）
MONGO_URI = "mongodb://localhost:27017/"         # MongoDB 连接地址
DB_NAME = "GI"                                   # 数据库名
COLL_NAME = "avatar_costume"                     # 集合名（要统一风格可改 raw_avatar_costume，你自己定）

# 混淆字段中判定为 hash 的（随机大数），需要转字符串
# 经字段分析确认：
#   BAMFPODFABJ  值达 41 亿，超 int32 上限（uint32 hash）
#   ADLCLKDIJLK  19位大数（uint64 hash）
#   KOKPFLNIEFM  19位大数（uint64 hash）
#   PPHKABFHIJP  19位大数（uint64 hash）
# 另外 3 个混淆字段保留原值：
#   HJKKNCODEBP / ONKNBEKJPEG  → 布尔值 true
#   FDBALHEDEDG                → 整数 1, 2, 3
OBF_HASH = {
    "BAMFPODFABJ", "ADLCLKDIJLK", "KOKPFLNIEFM", "PPHKABFHIJP",
}

def is_hash_field(k):
    """判断字段是否为 hash：明文名以 Hash 结尾，或属于混淆 hash 白名单"""
    return k.endswith("Hash") or k in OBF_HASH

# ---------- 读取数据 ----------
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 转换：skinId → _id 作主键；hash 字段转字符串；其余保留原字段原值 ----------
docs = []
for rec in data:
    # 原表没有 id 字段，使用唯一标识 skinId 作为主键 _id
    new_rec = {"_id": rec["skinId"]}
    for k, v in rec.items():
        if k == "skinId":                   # 已转 _id，跳过原字段
            continue
        new_rec[k] = str(v) if is_hash_field(k) and v is not None else v
    docs.append(new_rec)

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()                 # 清空旧数据
coll.insert_many(docs)      # 162 条一次插完不分批
print(f"✓ 导入 {len(docs)} 条 → {DB_NAME}.{COLL_NAME}")
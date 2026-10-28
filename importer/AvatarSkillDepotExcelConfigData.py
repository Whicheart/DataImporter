import json
from pymongo import MongoClient

# ---------- 配置 ----------
PATH = "json/AvatarSkillDepotExcelConfigData.json"  # 数据文件路径（相对仓库根目录）
MONGO_URI = "mongodb://localhost:27017/"            # MongoDB 连接地址
DB_NAME = "GI"                                      # 数据库名
COLL_NAME = "avatar_skill_depot"                    # 集合名（想跟 raw_avatar_excel 风格统一可改 raw_skill_depot）

RENAME_MAP = {
    "LLEFDMDOMGG": "proudSkillGroups",
    "KDCMKCFKPBL": "specialProudSkillGroups",
    "PEAOICMBMKH": "arkheType"
}

OBF_HASH = set()

def is_hash_field(k):
    """判断字段是否为 hash：明文名以 Hash 结尾，或属于混淆 hash 白名单"""
    return k.endswith("Hash") or k in OBF_HASH

# ---------- 读取数据 ----------
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 转换：id → _id 作主键；hash 字段转字符串；其余保留原字段原值 ----------
# 注意：is_hash_field 只作用于顶层字段，嵌套在数组/对象里的字段原样保留
# （LLEFDMDOMGG/KDCMKCFKPBL 里的嵌套字段均为小整数或枚举字符串，无溢出风险）
docs = []
for rec in data:
    new_rec = {"_id": rec["id"]}            # 原 id 字段直接作为 _id 主键
    for k, v in rec.items():
        if k == "id":                       # 已转 _id，跳过原字段
            continue

        actual_key = RENAME_MAP.get(k, k)

        if actual_key == "proudSkillGroups" and isinstance(v, list):
            new_list = []
            for item in v:
                new_item = {}
                for ik, iv in item.items():
                    # 把内部的 DHIEHDPAFGI 改成 unlockPromoteLevel
                    if ik == "DHIEHDPAFGI":
                        new_item["unlockPromoteLevel"] = iv
                    else:
                        new_item[ik] = iv
                new_list.append(new_item)
            new_rec[actual_key] = new_list

        else:
            new_rec[actual_key] = str(v) if is_hash_field(actual_key) and v is not None else v
    docs.append(new_rec)

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()                 # 清空旧数据
coll.insert_many(docs)      # 一次插完不分批
print(f"✓ 导入 {len(docs)} 条 → {DB_NAME}.{COLL_NAME}")
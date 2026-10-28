import json
from pymongo import MongoClient

# ---------- 配置 ----------
PATH = "json/ProudSkillExcelConfigData.json"  # 数据文件路径（相对仓库根目录）
MONGO_URI = "mongodb://localhost:27017/"      # MongoDB 连接地址
DB_NAME = "GI"                                # 数据库名
COLL_NAME = "proud_skill"                     # 集合名

# 混淆字段中判定为 hash 的（大随机数），需要转字符串
OBF_HASH = set()


def is_hash_field(k):
    """判断顶层字段是否为 hash"""
    return k.endswith("Hash") or k in OBF_HASH


# ---------- 读取数据 ----------
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 转换 ----------
docs = []
for rec in data:
    new_rec = {
        "_id": rec["proudSkillId"]  # 用 proudSkillId 作为主键
    }
    for k, v in rec.items():
        if k == "proudSkillId":
            continue

        if k == "CJJODEPIILB":
            k = "descExtraTextMapHash"
        elif k == "NAOILGGDLNA":
            k = "loreDescTextMapHash"

        if k == "addProps" and isinstance(v, list):
            new_props = []
            for prop in v:
                new_prop = {}
                for pk, pv in prop.items():
                    if pk == "GGKIEIJLCJJ":
                        new_prop["value"] = pv
                    else:
                        new_prop[pk] = pv
                new_props.append(new_prop)
            new_rec[k] = new_props

        # 1. 顶层 Hash 字段转字符串
        elif is_hash_field(k) and v is not None:
            new_rec[k] = str(v)

        # 2. 特殊处理 paramDescList（名字没 Hash，但里面全是 Hash 的数组）
        elif k == "paramDescList" and isinstance(v, list):
            new_rec[k] = [str(item) for item in v]

        # 3. 其他字段原样保留
        else:
            new_rec[k] = v

    docs.append(new_rec)

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()  # 清空旧数据
coll.insert_many(docs)  # 6273 条一次插完
print(f"✓ 导入 {len(docs)} 条 → {DB_NAME}.{COLL_NAME}")
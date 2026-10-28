import json
from pymongo import MongoClient

# ---------- 配置 ----------
PATH = "WeaponCurveExcelConfigData.json"    # 数据文件路径
MONGO_URI = "mongodb://localhost:27017/"    # MongoDB 连接地址
DB_NAME = "GI"                              # 数据库名
COLL_NAME = "weapon_curve"                  # 集合名

# ---------- 读取数据 ----------
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 转换：拍平数组，提取为字典 ----------
docs = []
for rec in data:
    # 用等级 level 作为主键 _id
    new_rec = {
        "_id": rec["level"]
    }

    curves_dict = {}
    for info in rec.get("curveInfos", []):
        # 提取成长曲线的类型（如 GROW_CURVE_ATTACK_S5）
        curve_type = info.get("type")
        # 提取被混淆的数值字段 GGKIEIJLCJJ（已知明文 = value）
        curve_value = info.get("GGKIEIJLCJJ")

        if curve_type:
            curves_dict[curve_type] = curve_value

    # 将组装好的字典存入 curves 字段
    new_rec["curves"] = curves_dict
    docs.append(new_rec)

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()  # 清空旧数据
coll.insert_many(docs)  # 插入新数据
print(f"✓ 导入 {len(docs)} 条 → {DB_NAME}.{COLL_NAME}")

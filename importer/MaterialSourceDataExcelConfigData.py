import json
from pymongo import MongoClient

# ---------- 配置 ----------
PATH = "json/MaterialSourceDataExcelConfigData.json"  # 数据文件路径（相对仓库根目录）
MONGO_URI = "mongodb://localhost:27017/"              # MongoDB 连接地址
DB_NAME = "GI"                                        # 数据库名
COLL_NAME = "material_source_data"                    # 集合名


def is_hash_field(k):
    """判断字段是否为 hash：明文名以 Hash 结尾"""
    return k.endswith("Hash")


# ---------- 读取数据 ----------
with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------- 转换：id 作为主键 _id；哈希数组元素转字符串 ----------
docs = []
for rec in data:
    new_rec = {
        "_id": rec["id"]  # 提取物品 ID 作为主键
    }
    for k, v in rec.items():
        if k == "id":
            continue

        # 1. 顶层明文 Hash 字段
        if is_hash_field(k) and v is not None:
            new_rec[k] = str(v)

        # 2. textList 里面全是文本 Hash，需要把数组里的数字转成字符串
        elif k == "textList" and isinstance(v, list):
            new_rec[k] = [str(item) for item in v]

        # 3. 把 HNNPIIJLLEK 重命名为 sourceList，同样把元素转字符串
        elif k == "HNNPIIJLLEK" and isinstance(v, list):
            new_rec["sourceList"] = [str(item) for item in v]

        # 4. 其他字段（包括 CEKAIOGKFBP 的空对象数组、AOFJGAPHNDH 的字符串等）保留原样
        else:
            new_rec[k] = v

    docs.append(new_rec)

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()  # 清空旧数据
coll.insert_many(docs)  # 10512 条一次插完
print(f"✓ 导入 {len(docs)} 条 → {DB_NAME}.{COLL_NAME}")
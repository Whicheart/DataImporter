import json
import os
import re

from pymongo import MongoClient

# ---------- 配置 ----------
MONGO_URI = "mongodb://localhost:27017/"            # MongoDB 连接地址
DB_NAME = "GI"                                      # 数据库名
TEXTMAP_DIR = "../TextMap"                          # 文本表目录（相对 importer 目录）

# TextMap_Medium<lang>.json → text_map_medium_<lang>
FILE_PATTERN = re.compile(r"^TextMap_Medium([A-Za-z0-9]+)\.json$")


def collection_name(filename):
    """由文件名推出目标集合：TextMap_MediumCHS.json → text_map_medium_chs"""
    lang = FILE_PATTERN.match(filename).group(1)
    return f"text_map_medium_{lang.lower()}"


def load_textmap(path):
    """读取文本表，转成 [{"_id": 字符串 id, "text": 原文}] 的数组格式"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [{"_id": str(k), "text": v} for k, v in data.items()]


# ---------- 找文件 ----------
if not os.path.isdir(TEXTMAP_DIR):
    raise SystemExit(f"找不到文本表目录: {TEXTMAP_DIR}")

files = sorted(f for f in os.listdir(TEXTMAP_DIR) if FILE_PATTERN.match(f))
if not files:
    raise SystemExit(f"{TEXTMAP_DIR}/ 下没有 TextMap_Medium<lang>.json")

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]

for filename in files:
    docs = load_textmap(os.path.join(TEXTMAP_DIR, filename))
    coll_name = collection_name(filename)
    coll = db[coll_name]
    coll.drop()                 # 清空旧数据
    coll.insert_many(docs)      # insert_many 自动分批，几十万条也不会超包
    print(f"✓ {filename} → {DB_NAME}.{coll_name}  {len(docs)} 条")

client.close()

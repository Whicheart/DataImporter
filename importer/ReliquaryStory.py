import json
import os
import re

from pymongo import MongoClient

# ---------- 配置 ----------
DATA_DIR = "reliquary story"              # 数据目录（相对仓库根目录）
MONGO_URI = "mongodb://localhost:27017/"  # MongoDB 连接地址
DB_NAME = "GI"                            # 数据库名
COLL_NAME = "reliquary_story"             # 集合名

# 文件名形如 Relic<id>_<x>.txt，<x> 从 1 开始
FILE_PATTERN = re.compile(r"^Relic(\d+)_(\d+)\.txt$")


# ---------- 读取数据 ----------
# 按 id 归拢：{id: [(x, 行数组), ...]}
groups = {}
if not os.path.isdir(DATA_DIR):
    raise FileNotFoundError(f"数据目录不存在：{DATA_DIR}")

for name in sorted(os.listdir(DATA_DIR)):
    m = FILE_PATTERN.match(name)
    if m is None:
        continue
    story_id = int(m.group(1))
    index = int(m.group(2))
    with open(os.path.join(DATA_DIR, name), "r", encoding="utf-8") as f:
        lines = f.read().splitlines()   # 逐行保留，空行也保留
    if lines and not lines[0].strip():  # 首行为空行时跳过
        lines = lines[1:]
    groups.setdefault(story_id, []).append((index, lines))

# ---------- 转换 ----------
# stories 按下标 x 升序排列：stories[0] 来自 Relic<id>_1.txt，stories[1] 来自 _2，依此类推
docs = []
for story_id, parts in sorted(groups.items()):
    parts.sort(key=lambda p: p[0])
    docs.append({
        "_id": story_id,
        "stories": [lines for _, lines in parts],
    })

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()                 # 清空旧数据
coll.insert_many(docs)      # 65 条一次插完
print(f"✓ 导入 {len(docs)} 条 → {DB_NAME}.{COLL_NAME}")

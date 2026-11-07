import os
import re

from collections import defaultdict
from pymongo import MongoClient

# ---------- 配置 ----------
DATA_DIR = "../Readable/CHS"              # 故事文本目录（相对 importer 目录）
MONGO_URI = "mongodb://localhost:27017/"  # MongoDB 连接地址
DB_NAME = "GI"                            # 数据库名

# 文件名形如 <type><id>.txt 或 <type><id>_<idx>.txt，<idx> 从 1 开始
FILE_PATTERN = re.compile(r"^([A-Za-z]+)(\d+)(?:_(\d+))?\.txt$")

# 集合名 = <type> 部分转小写 + 该后缀：Weapon -> weapon_story，Relic -> relic_story
COLL_SUFFIX = "_story"


def collection_name(type_part):
    """由文件名的 <type> 部分推出集合名。"""
    return type_part.lower() + COLL_SUFFIX


def story_order(idx):
    """故事顺序：没有 <idx> 的排最前，其余按 <idx> 数字升序。"""
    return (0, 0) if idx is None else (1, int(idx))


def trim_blank_lines(lines):
    """去掉首个有内容行之前的行、最后一个有内容行之后的行，行间空行保留。"""
    start, end = 0, len(lines)
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return lines[start:end]

# ---------- 读取数据 ----------
# groups[(集合名, 故事 id)] = [(排序键, 文件路径), ...]
if not os.path.isdir(DATA_DIR):
    raise FileNotFoundError(f"数据目录不存在：{DATA_DIR}")

groups = defaultdict(list)
skipped = []
for name in sorted(os.listdir(DATA_DIR)):
    matched = FILE_PATTERN.match(name)
    if matched is None:
        skipped.append(name)
        continue
    type_part = matched.group(1)
    story_id = int(matched.group(2))
    index = matched.group(3)
    groups[(collection_name(type_part), story_id)].append(
        (story_order(index), os.path.join(DATA_DIR, name))
    )

if skipped:
    print(f"⚠ 跳过 {len(skipped)} 个不符合命名的文件：{skipped[:5]}")

if not groups:
    raise RuntimeError(f"目录里没有可导入的故事文件：{DATA_DIR}")

# ---------- 转换：{_id: 故事 id, stories: [第一段的行数组, 第二段的行数组, ...]} ----------
docs_by_coll = defaultdict(list)
for coll_name, story_id in sorted(groups):
    parts = sorted(groups[(coll_name, story_id)])
    stories = []
    for _, path in parts:
        with open(path, "r", encoding="utf-8") as f:
            stories.append(trim_blank_lines(f.read().splitlines()))
    docs_by_coll[coll_name].append({"_id": story_id, "stories": stories})

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
for coll_name in sorted(docs_by_coll):
    docs = docs_by_coll[coll_name]
    coll = db[coll_name]
    coll.drop()                 # 清空旧数据
    coll.insert_many(docs)      # 一次插完
    print(f"✓ 导入 {len(docs)} 条 → {DB_NAME}.{coll_name}")

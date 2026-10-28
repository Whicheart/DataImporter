import os
import re
from pymongo import MongoClient

# ---------- 配置 ----------
DIR_PATH = "weapon story"                 # 故事文本目录（相对仓库根目录）
MONGO_URI = "mongodb://localhost:27017/"  # MongoDB 连接地址
DB_NAME = "GI"                            # 数据库名
COLL_NAME = "weapon_story"                # 集合名

# 文件名形如 Weapon<id>.txt（主干）/ Weapon<id>_1.txt、Weapon<id>_2.txt、Weapon<id>_x.txt（变体）
FILE_PATTERN = re.compile(r"^Weapon(\d+)(?:_(\w+))?\.txt$")

# 全文件为空时的占位文本
BLANK_PLACEHOLDER = "……"


def read_lines(path):
    """按行切分，一行一个字符串，空行保留。

    文件首行的空行是导出时附带的格式噪音，直接去掉；整份文件都是空行时用占位文本。
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if all(not line.strip() for line in lines):
        return [BLANK_PLACEHOLDER]
    return lines


def sort_key(suffix):
    """主干文件排最前，变体排在其后：_1、_2 按数字顺序，_x 等其他变体按字典序。"""
    if suffix is None:
        return (0, 0)
    if suffix.isdigit():
        return (1, int(suffix))
    return (2, suffix)


# ---------- 读取并按武器 id 归组 ----------
# groups = {武器 id: [(排序键, 文件路径), ...]}
groups = {}
for name in sorted(os.listdir(DIR_PATH)):
    matched = FILE_PATTERN.match(name)
    if not matched:
        continue
    weapon_id = int(matched.group(1))
    suffix = matched.group(2)
    groups.setdefault(weapon_id, []).append(
        (sort_key(suffix), os.path.join(DIR_PATH, name))
    )

# ---------- 转换：{_id: 武器 id, stories: [主干的行数组, 变体 1 的行数组, ...]} ----------
docs = []
for weapon_id in sorted(groups):
    stories = [read_lines(path) for _, path in sorted(groups[weapon_id])]
    docs.append({"_id": weapon_id, "stories": stories})

# ---------- 导入 MongoDB ----------
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[COLL_NAME]
coll.drop()                 # 清空旧数据
coll.insert_many(docs)      # 266 条一次插完
print(f"✓ 导入 {len(docs)} 条 → {DB_NAME}.{COLL_NAME}")

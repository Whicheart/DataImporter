import json
import os
from pymongo import MongoClient

# ---------- 配置 ----------
MONGO_URI = "mongodb://localhost:27017/"  # MongoDB 连接地址
DB_NAME = "GI"                            # 数据库名
DATA_DIR = "json"                         # 数据文件目录（相对仓库根目录）

# 文本表文件名（去掉 .json）→ 集合名
COLL_MAP = {
    "TextMap_MediumCHS": "text_map_chs_medium",
    "TextMap_MediumEN": "text_map_en_medium",
}

def collection_name(input_file):
    """根据文件名推断目标集合：已知文件走映射表，未知文件用文件名小写兜底"""
    stem = os.path.splitext(os.path.basename(input_file))[0]
    return COLL_MAP.get(stem, stem.lower())

def choose_json_file():
    """列出当前目录下的 .json 文件，让用户选序号或输入文件名"""
    files = sorted(f for f in os.listdir(DATA_DIR) if f.lower().endswith(".json") and not f.endswith("_array.json"))
    if not files:
        print(f"{DATA_DIR}/ 下没有找到可用的 .json 文件")
        raise SystemExit(1)

    print("可选的 JSON 文件：")
    for i, f in enumerate(files, 1):
        print(f"  [{i}] {f}")

    while True:
        raw = input("\n请输入序号或文件名：").strip()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(files):
                return os.path.join(DATA_DIR, files[idx])
            print("序号越界，请重新输入")
        elif raw in files:
            return os.path.join(DATA_DIR, raw)
        else:
            print("无效输入，请重新输入")

# 1. 让用户选文件
input_file = choose_json_file()
print(f"\n正在处理: {input_file}")

# 2. 读取数据
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 3. 转成数组格式（_id 统一为字符串，text 保留原文）
result = [{"_id": str(k), "text": v} for k, v in data.items()]

# 4. 自动生成输出文件名（去掉原来的 .json 加上 _array.json）
output_file = input_file.replace('.json', '_array.json')

# 5. 写入文件
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False)

print(f"✓ 转换完成！共 {len(result)} 条，已保存至: {output_file}")

# 6. 导入 MongoDB
coll_name = collection_name(input_file)
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
coll = db[coll_name]
coll.drop()                 # 清空旧数据
coll.insert_many(result)    # insert_many 自动分批，241738 条也不会超包
print(f"✓ 导入 {len(result)} 条 → {DB_NAME}.{coll_name}")
client.close()

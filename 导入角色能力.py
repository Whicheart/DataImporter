import os
import json
from pymongo import MongoClient

# ---------- 配置 ----------
ABILITY_DIR = "./AvatarAbilities"
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "GI"
COLL_NAME = "avatar_ability"


def main():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]

    # 1. 严格限制 ID 范围在 10000002 到 10000899 之间提取合法角色代号
    valid_char_keys = set()
    query = {"_id": {"$gte": 10000002, "$lte": 10000899}}

    for doc in db["avatar"].find(query):
        icon = doc.get("iconName")
        if icon and icon.startswith("UI_AvatarIcon_"):
            key = icon.replace("UI_AvatarIcon_", "")
            valid_char_keys.add(key)

    # 特殊处理：旅行者（Player）的代号与普通角色不同
    # 他们是 10000005 / 10000007，但文件名是 Player_Wind, Player_Rock 等
    valid_char_keys.update({
        "Player_Wind", "Player_Rock", "Player_Electric",
        "Player_Grass", "Player_Water", "Player_Fire"
    })

    print(f"根据 ID 范围提取到 {len(valid_char_keys)} 个合法角色代号（含旅行者）。")

    coll = db[COLL_NAME]
    coll.drop()

    docs = []

    # 2. 遍历文件夹进行过滤和导入
    for filename in os.listdir(ABILITY_DIR):
        if not filename.startswith("ConfigAbility_Avatar_") or not filename.endswith(".json"):
            continue

        char_key = filename.replace("ConfigAbility_Avatar_", "").replace(".json", "")

        # 如果代号不在白名单里，直接跳过
        if char_key not in valid_char_keys:
            continue

        filepath = os.path.join(ABILITY_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    for block in data:
                        default_block = block.get("Default", {})
                        ability_name = default_block.get("abilityName", "Unknown")
                        docs.append({
                            "character_key": char_key,
                            "ability_name": ability_name,
                            "data": block
                        })
            except Exception as e:
                print(f"解析 {filename} 失败: {e}")

    if docs:
        coll.insert_many(docs)
        print(f"\n✓ 成功导入 {len(docs)} 条合法角色的技能逻辑数据！")
    else:
        print("没有找到匹配的数据。")


if __name__ == "__main__":
    main()
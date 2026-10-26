from pymongo import MongoClient

# ---------- 配置 ----------
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "GI"


def main():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]

    coll_fetter = db["fetter_info"]
    coll_text = db["text_map_chs_medium"]

    print("正在按 AAEINBDNBHL 字段进行分组统计...")

    # 1. 聚合查询：按 AAEINBDNBHL 分组并计数
    pipeline = [
        {"$group": {"_id": "$AAEINBDNBHL", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    results = list(coll_fetter.aggregate(pipeline))

    print(f"共找到 {len(results)} 种不同的 Hash 值。\n")
    print(f"{'Hash 值':<15} | {'角色数':<5} | {'TextMap 翻译结果'}")
    print("-" * 60)

    success_count = 0
    fail_count = 0

    # 2. 遍历每个 Hash，去文本表里查
    for item in results:
        hash_val = item["_id"]
        count = item["count"]

        # 确保转成字符串去查（防止有些是 int 有些是 str）
        hash_str = str(hash_val) if hash_val is not None else ""

        # 查文本表
        text_doc = coll_text.find_one({"_id": hash_str})

        if text_doc:
            text_val = text_doc.get("text", "")
            # 如果文本太长，截断显示
            if len(text_val) > 30:
                text_val = text_val[:30] + "..."
            print(f"{hash_str:<15} | {count:<8} | ✅ 找到: {text_val}")
            success_count += 1
        else:
            print(f"{hash_str:<15} | {count:<8} | ❌ 未找到")
            fail_count += 1

    # 3. 打印总结
    print("-" * 60)
    print(f"统计完成：成功翻译 {success_count} 个，未找到 {fail_count} 个。")


if __name__ == "__main__":
    main()
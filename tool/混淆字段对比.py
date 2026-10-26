from pymongo import MongoClient

db = MongoClient("mongodb://localhost:27017/")["GI"]
coll = db["avatar"]

OBF = ["HMEEJHKDEJJ", "EMIBHJLIOHL", "KOKPFLNIEFM",
       "OPABFGCNNHB", "JEFOBMDHIFJ", "GOEONNEACMM"]

# 收集所有文档里出现过的全部字段名
all_keys = set()
for doc in coll.find({}):
    all_keys.update(doc.keys())
all_keys.discard("_id")
plain_keys = [k for k in all_keys if k not in OBF]

print(f"明文字段 {len(plain_keys)} 个，混淆字段 {len(OBF)} 个")

# 逐对比较：两个字段都存在的文档中，值是否全部相同
for o in OBF:
    for p in plain_keys:
        total = coll.count_documents({o: {"$exists": True}, p: {"$exists": True}})
        if total == 0:
            continue
        diff = coll.count_documents({
            o: {"$exists": True}, p: {"$exists": True},
            "$expr": {"$ne": [f"${o}", f"${p}"]}
        })
        if diff == 0:
            print(f"★ {o} 完全等于 {p}  （{total} 条全部一致）")

print("检查完毕")
"""公共导入逻辑：FieldMap 驱动的字段清洗、覆盖率预检与文档构建。

所有 ExcelBinOutput/ 下的表共用这一套规则：
    - FieldMap.json 决定每个混淆字段的去向（改名 / 丢弃 / 保留原名 / 占位名）
    - 名字以 TextMapHash 结尾的标量，转字符串
    - HASH_LIST_FIELDS 里登记的哈希数组，逐元素转字符串
    - 任何未登记的混淆字段、未登记的哈希字段，一律在入库前报错退出
"""
import hashlib
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIELD_MAP_PATH = os.path.join(BASE_DIR, "..", "FieldMap.json")

OBF_PATTERN = re.compile(r"^[A-Z]{5,}$")        # 与 tool/FieldAnalysis.py 的判定保持一致
HASH_LIST_FIELDS = {"tips", "textList", "paramDescList", "jumpDescs"}   # 名字不带 TextMapHash 的哈希数组
BIG_INT = 2 ** 53        # 超过它，JSON 按 double 解析时已经丢精度
UINT32_ISH = 2 ** 31     # 游戏内 id 都在 1e8 量级，超过它基本就是哈希

PLACEHOLDER_KINDS = ("TextMapHash", "Type", "isAaaa")


class PreflightError(Exception):
    """所有预检错误的基类：抛出即代表本次入库整体放弃。"""


class UncoveredFieldError(PreflightError):
    """出现了 FieldMap 里没有登记的混淆字段。"""


class HashFieldError(PreflightError):
    """出现了没登记、但看起来是哈希的字段。"""


class SpecError(PreflightError):
    """规格表问题：主键缺失、主键重复、空结果等。"""


# ---------- FieldMap ----------
class FieldMap:
    """把 FieldMap.json 拆成四类：改名、丢弃、保留原名、占位名。"""

    def __init__(self, rename, drop, keep, placeholder):
        self.rename = rename            # obf -> 明文
        self.drop = drop                # set(obf)，值为 ""
        self.keep = keep                # set(obf)，明文与混淆名相同
        self.placeholder = placeholder  # obf -> kind（TextMapHash / Type / isAaaa）

    def is_covered(self, key):
        return (key in self.rename or key in self.drop
                or key in self.keep or key in self.placeholder)

    def describe(self, key):
        if key in self.rename:
            return "改名 %s" % self.rename[key]
        if key in self.drop:
            return "丢弃"
        if key in self.keep:
            return "保留原名"
        if key in self.placeholder:
            return "占位名 %s" % self.placeholder[key]
        return "未登记"


def load_field_map(path=FIELD_MAP_PATH):
    with open(path, "r", encoding="utf-8-sig") as f:
        raw = json.load(f)

    rename, drop, keep, placeholder = {}, set(), set(), {}
    for obf, plain in raw.items():
        if plain == "":
            drop.add(obf)
        elif plain == obf:
            keep.add(obf)
        elif plain in PLACEHOLDER_KINDS:
            placeholder[obf] = plain
        else:
            rename[obf] = plain
    return FieldMap(rename, drop, keep, placeholder)


# ---------- 占位名 ----------
def _derive_letters(token, salt, size=4):
    """由令牌派生固定的小写字母串：看起来随机，但每次运行结果一致。"""
    digest = hashlib.md5(("%s#%d" % (token, salt)).encode("utf-8")).hexdigest()
    return "".join(chr(ord("a") + int(c, 16)) for c in digest[:size])


class Context:
    """一次运行内共享的状态：占位名缓存与已占用字段名。"""

    def __init__(self, field_map, used_names=None):
        self.fm = field_map
        self.memo = {}
        self.used = set(used_names or ())
        self.used.update(field_map.rename.values())

    def placeholder_name(self, token):
        if token in self.memo:
            return self.memo[token]

        kind = self.fm.placeholder[token]
        salt = 0
        while True:
            letters = _derive_letters(token, salt)
            if kind == "TextMapHash":
                name = letters + "TextMapHash"
            elif kind == "Type":
                name = letters + "Type"
            else:
                name = "is" + letters.capitalize()
            if name not in self.used:
                break
            salt += 1

        self.memo[token] = name
        self.used.add(name)
        return name


# ---------- 字段清洗 ----------
def _convert_scalar(key, value):
    """标量转换：哈希标量转字符串；哈希数组的元素也走这里。"""
    if value is None:
        return value
    if key.endswith("Hash"):
        return str(value)
    if key in HASH_LIST_FIELDS:
        return str(value)
    return value


def _clean_pair(ctx, key, value):
    """返回 (新字段名, 新值)；命中丢弃时返回 (None, None)。"""
    fm = ctx.fm
    if key in fm.drop:
        return None, None
    if key in fm.rename:
        key = fm.rename[key]
    elif key in fm.keep:
        pass
    elif key in fm.placeholder:
        key = ctx.placeholder_name(key)
    elif OBF_PATTERN.match(key):
        raise UncoveredFieldError("混淆字段未登记：%s" % key)
    return key, _clean_value(ctx, key, value)


def _clean_value(ctx, key, value):
    if isinstance(value, dict):
        return _clean_dict(ctx, value)
    if isinstance(value, list):
        return [_clean_value(ctx, key, item) for item in value]
    return _convert_scalar(key, value)


def _clean_dict(ctx, record):
    out = {}
    for key, value in record.items():
        new_key, new_value = _clean_pair(ctx, key, value)
        if new_key is not None:
            out[new_key] = new_value
    return out


def clean_record(ctx, record, skip_key=None):
    """把一条记录清洗成可入库的字段字典（不含 _id）。"""
    out = {}
    for key, value in record.items():
        if skip_key is not None and key == skip_key:
            continue
        new_key, new_value = _clean_pair(ctx, key, value)
        if new_key is not None:
            out[new_key] = new_value
    return out


# ---------- 读取 ----------
def load_records(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def resolve_key(field_map, record, name):
    """在记录里定位“映射后等于 name”的原始键，兼容用混淆名存放主键的表。"""
    if name is None:
        return None
    if name in record:
        return name
    for key in record:
        if OBF_PATTERN.match(key) and field_map.rename.get(key) == name:
            return key
    return None


# ---------- 预检 ----------
def _walk_keys(value, sink):
    """递归收集所有层级里出现的混淆字段名（用于覆盖率检查）。"""
    if isinstance(value, dict):
        for key, child in value.items():
            if OBF_PATTERN.match(key):
                sink[key] = sink.get(key, 0) + 1
            _walk_keys(child, sink)
    elif isinstance(value, list):
        for item in value:
            _walk_keys(item, sink)


def _walk_plain_keys(value, sink):
    """收集所有非混淆字段名，用来防止随机占位名与明文撞名。"""
    if isinstance(value, dict):
        for key, child in value.items():
            if not OBF_PATTERN.match(key):
                sink.add(key)
            _walk_plain_keys(child, sink)
    elif isinstance(value, list):
        for item in value:
            _walk_plain_keys(item, sink)


def scan_coverage(specs, records_by_path, field_map):
    """闸 2：混淆字段覆盖率。返回 (缺失明细, 明文键集合, 出现的混淆令牌计数)。"""
    missing = {}        # token -> 出现次数
    plain_keys = set()
    seen = {}

    for spec in specs:
        for record in records_by_path[spec.path]:
            _walk_keys(record, seen)
            _walk_plain_keys(record, plain_keys)

    for token, count in seen.items():
        if not field_map.is_covered(token):
            missing[token] = count
    return missing, plain_keys, seen


def _looks_like_hash(key, value):
    """判断一个字段是否“看起来是哈希但没被登记”。"""
    if key.endswith("Hash") or key in HASH_LIST_FIELDS:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        if abs(value) > BIG_INT:
            return "标量 %d 超过 2^53，但字段名不带 TextMapHash" % value
        return None
    if isinstance(value, list) and value and all(
            isinstance(x, int) and not isinstance(x, bool) for x in value):
        biggest = max(abs(x) for x in value)
        if biggest > UINT32_ISH:
            return "整数数组元素最大 %d 超过 2^31，但未登记为哈希数组" % biggest
    return None


def scan_hash_fields(specs, records_by_path, field_map):
    """闸 3：哈希字段命名覆盖（标量 >2^53、数组 >2^31 都必须被登记）。"""
    problems = []

    def visit(value, path):
        if isinstance(value, dict):
            for key, child in value.items():
                if OBF_PATTERN.match(key):
                    if key in field_map.drop:
                        continue                    # 反正要丢，不参与检查
                    if key in field_map.rename:
                        key = field_map.rename[key]
                    elif key in field_map.placeholder:
                        kind = field_map.placeholder[key]
                        if kind == "TextMapHash":
                            key = "xTextMapHash"
                        elif kind == "Type":
                            key = "xType"
                        else:
                            key = "isX"
                reason = _looks_like_hash(key, child)
                if reason:
                    problems.append((path, key, reason))
                visit(child, path)
        elif isinstance(value, list):
            for item in value:
                visit(item, path)

    for spec in specs:
        for record in records_by_path[spec.path]:
            visit(record, spec.path)
    return problems


def check_spec_keys(specs, records_by_path, field_map):
    """闸 4：主键/分组键必须存在（允许主键以混淆名存放）。"""
    problems = []
    for spec in specs:
        name = spec.group_by or spec.id_key
        if name is None:
            continue
        for index, record in enumerate(records_by_path[spec.path]):
            if resolve_key(field_map, record, name) is None:
                if spec.group_by and spec.default_group is not None:
                    continue                    # 分组键可缺省，构建时补默认值
                problems.append((spec.path, index, "缺少主键 %s" % name))
                break
    return problems


# ---------- 构建 ----------
def flatten_curves(body):
    """把 curveInfos 数组拍平成 {曲线类型: 数值} 的 curves 字典。"""
    infos = body.pop("curveInfos", [])
    body["curves"] = {
        info.get("type"): info.get("value")
        for info in infos
        if isinstance(info, dict)
    }
    return body


def build_docs(spec, records, ctx):
    """按规格把一组记录构建成待入库文档。"""
    if spec.pending:
        raise SpecError("%s：%s" % (spec.coll, spec.pending))

    docs = []

    if spec.group_by:
        groups = {}
        for record in records:
            record = dict(record)
            raw_group = resolve_key(ctx.fm, record, spec.group_by)
            if raw_group is None:
                if spec.default_group is None:
                    raise SpecError("%s：缺少分组键 %s" % (spec.path, spec.group_by))
                key = spec.default_group
            else:
                key = record.pop(raw_group)
            level = record.pop(spec.level_key, spec.default_level)
            body = clean_record(ctx, record)
            body[spec.level_key] = level
            groups.setdefault(key, []).append(body)

        for key, levels in groups.items():
            levels.sort(key=lambda item: item.get(spec.level_key, spec.default_level))
            docs.append({"_id": key, "levels": levels})
        return docs

    for record in records:
        raw_id = resolve_key(ctx.fm, record, spec.id_key)
        body = clean_record(ctx, record, skip_key=raw_id)
        if spec.transform is not None:
            body = spec.transform(body)
        if spec.id_key is None:
            docs.append(body)
        else:
            if raw_id is None:
                raise SpecError("%s：缺少主键 %s" % (spec.path, spec.id_key))
            doc = {"_id": record[raw_id]}
            doc.update(body)
            docs.append(doc)
    return docs


def check_docs(spec, docs):
    """构建后的自检：空结果、_id 重复。"""
    if not docs:
        raise SpecError("%s：构建结果为空，拒绝写入（可能是读错了文件）" % spec.coll)

    if spec.group_by or spec.id_key is not None:
        seen = set()
        for doc in docs:
            key = doc["_id"]
            if key in seen:
                raise SpecError("%s：主键重复 %r" % (spec.coll, key))
            seen.add(key)

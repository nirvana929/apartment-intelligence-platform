"""
敏感字段脱敏模块

本模块负责对查询结果中的敏感字段进行脱敏处理，确保：
1. 手机号只显示前3位和后4位，中间用星号替代
2. 身份证号绝不返回（在 SQL 守卫层就已经拦截）
3. 其他敏感字段根据业务需要进行脱敏

脱敏策略：
- 手机号：138****1234
- 姓名：只显示姓，名用星号替代（如 张**）
- 地址：保留省市区，详细地址部分脱敏

注意：身份证号等高危字段在 SQL 守卫层就已经完全拦截，不会进入脱敏流程
"""

import re
from dataclasses import dataclass
from typing import Any


# ============================================================================
# 脱敏规则配置
# ============================================================================

# 手机号正则表达式
# 匹配 11 位手机号，捕获前3位和后4位
PHONE_PATTERN = re.compile(r"^(\d{3})\d{4}(\d{4})$")

# 身份证号正则表达式（18位）
# 匹配 18 位身份证号，用于检测和拦截
ID_CARD_PATTERN = re.compile(r"^\d{17}[\dXx]$")


# 精确的敏感字段名集合（不使用子串匹配，避免 apartment_name 等被误脱敏）
SENSITIVE_PHONE_FIELDS = {"phone", "tel", "mobile"}
SENSITIVE_NAME_FIELDS = {"name", "username", "nickname"}
SENSITIVE_ADDRESS_FIELDS = {"address", "address_detail"}


def get_sensitive_fields_from_policy(table_names: set[str] | None = None) -> set[str]:
    """
    从 table_policy 获取敏感字段名集合，供 redact_row/redact_rows 使用。

    Args:
        table_names: 要扫描的表名集合，为 None 时扫描所有白名单表

    Returns:
        敏感字段名集合（包含 sensitive 和 blocked 字段）
    """
    from .table_policy import ALLOWED_TABLES

    fields: set[str] = set()
    for table in ALLOWED_TABLES:
        if table_names and table.name not in table_names:
            continue
        for col in table.allowed_columns:
            if col.is_sensitive or col.is_blocked:
                fields.add(col.name)
    return fields


def redact_phone(phone: str) -> str:
    """
    手机号脱敏

    将手机号中间4位替换为星号，只保留前3位和后4位。

    Args:
        phone: 原始手机号字符串

    Returns:
        脱敏后的手机号，格式如 138****1234

    Example:
        >>> redact_phone("13812345678")
        '138****5678'
        >>> redact_phone("15000001111")
        '150****1111'
    """
    if not phone:
        return phone

    # 确保是字符串类型
    phone_str = str(phone).strip()

    # 尝试匹配手机号格式
    match = PHONE_PATTERN.match(phone_str)
    if match:
        # 匹配成功，替换中间4位为星号
        return f"{match.group(1)}****{match.group(2)}"

    # 如果不是标准手机号格式，返回原值
    # （可能是座机号或其他格式，不做脱敏）
    return phone_str


def redact_name(name: str) -> str:
    """
    姓名脱敏

    保留姓氏，名字用星号替代。
    - 2字姓名：张*
    - 3字姓名：张**
    - 4字及以上：保留第一个字，其余用星号

    Args:
        name: 原始姓名字符串

    Returns:
        脱敏后的姓名

    Example:
        >>> redact_name("张三")
        '张*'
        >>> redact_name("张三丰")
        '张**'
        >>> redact_name("欧阳锋")
        '欧**'
    """
    if not name:
        return name

    name_str = str(name).strip()

    # 空字符串直接返回
    if not name_str:
        return name_str

    # 获取字符数（考虑中文字符）
    char_count = len(name_str)

    if char_count == 1:
        # 只有一个字，返回原值
        return name_str
    elif char_count == 2:
        # 2字姓名，保留姓，名用星号
        return f"{name_str[0]}*"
    else:
        # 3字及以上，保留第一个字，其余用星号
        return f"{name_str[0]}{'*' * (char_count - 1)}"


def redact_address(address: str) -> str:
    """
    地址脱敏

    保留省市区信息，详细地址部分用星号替代。
    假设地址格式为：XX省XX市XX区详细地址

    Args:
        address: 原始地址字符串

    Returns:
        脱敏后的地址

    Example:
        >>> redact_address("北京市朝阳区建国路100号")
        '北京市朝阳区***'
        >>> redact_address("上海市浦东新区张江高科技园区")
        '上海市浦东新区***'
    """
    if not address:
        return address

    addr_str = str(address).strip()

    # 尝试匹配省市区模式
    # 匹配：XX省/XX市/XX区 后面的内容
    patterns = [
        # 匹配：XX省XX市XX区...
        re.compile(r"^([一-龥]+省[一-龥]+市[一-龥]+[区县市]).*$"),
        # 匹配：XX市XX区...
        re.compile(r"^([一-龥]+市[一-龥]+[区县市]).*$"),
        # 匹配：XX区...
        re.compile(r"^([一-龥]+[区县市]).*$"),
    ]

    for pattern in patterns:
        match = pattern.match(addr_str)
        if match:
            # 保留省市区部分，详细地址用星号替代
            return f"{match.group(1)}***"

    # 如果无法识别格式，返回部分脱敏
    if len(addr_str) > 6:
        return f"{addr_str[:6]}***"

    return addr_str


def is_id_card(value: str) -> bool:
    """
    检测是否为身份证号

    用于在结果返回前检测是否意外包含了身份证号。

    Args:
        value: 待检测的字符串

    Returns:
        True 如果是身份证号格式，否则 False
    """
    if not value:
        return False

    return bool(ID_CARD_PATTERN.match(str(value).strip()))


# ============================================================================
# 结果集脱敏
# ============================================================================



def redact_row(row: dict[str, Any], sensitive_fields: set[str] | None = None) -> dict[str, Any]:
    """
    对单行数据进行脱敏处理

    根据字段名自动识别敏感字段并进行脱敏。

    Args:
        row: 原始数据行（字典格式）
        sensitive_fields: 需要脱敏的字段名集合（可选，如果为 None 则自动识别）

    Returns:
        脱敏后的数据行

    Example:
        >>> row = {"id": 1, "name": "张三", "phone": "13812345678"}
        >>> redact_row(row)
        {'id': 1, 'name': '张*', 'phone': '138****5678'}
    """
    if not row:
        return row

    result = {}

    for field_name, value in row.items():
        if value is None:
            result[field_name] = None
            continue

        # 身份证号：高危字段，直接替换
        if isinstance(value, str) and is_id_card(value):
            result[field_name] = "[已拦截-身份证号]"
            continue

        # 精确匹配敏感字段名（不使用子串匹配，避免 apartment_name 等被误脱敏）
        field_lower = field_name.lower()
        should_redact = False

        if sensitive_fields and field_name in sensitive_fields:
            should_redact = True
        elif field_lower in SENSITIVE_PHONE_FIELDS:
            should_redact = True
        elif field_lower in SENSITIVE_NAME_FIELDS:
            should_redact = True
        elif field_lower in SENSITIVE_ADDRESS_FIELDS:
            should_redact = True

        if should_redact and isinstance(value, str):
            if field_lower in SENSITIVE_PHONE_FIELDS:
                result[field_name] = redact_phone(value)
            elif field_lower in SENSITIVE_NAME_FIELDS:
                result[field_name] = redact_name(value)
            elif field_lower in SENSITIVE_ADDRESS_FIELDS:
                result[field_name] = redact_address(value)
            else:
                result[field_name] = value
        else:
            result[field_name] = value

    return result


def redact_rows(rows: list[dict[str, Any]], sensitive_fields: set[str] | None = None) -> list[dict[str, Any]]:
    """
    对多行数据进行脱敏处理

    Args:
        rows: 原始数据行列表
        sensitive_fields: 需要脱敏的字段名集合（可选）

    Returns:
        脱敏后的数据行列表
    """
    if not rows:
        return rows

    return [redact_row(row, sensitive_fields) for row in rows]


# ============================================================================
# 脱敏统计
# ============================================================================

@dataclass
class RedactionStats:
    """
    脱敏统计信息

    用于日志记录和审计追踪，记录脱敏操作的详细信息。

    Attributes:
        total_rows: 总行数
        total_fields: 总字段数
        redacted_fields: 被脱敏的字段数
        blocked_fields: 被拦截的字段数（如身份证号）
    """
    total_rows: int = 0
    total_fields: int = 0
    redacted_fields: int = 0
    blocked_fields: int = 0


def redact_rows_with_stats(
    rows: list[dict[str, Any]],
    sensitive_fields: set[str] | None = None
) -> tuple[list[dict[str, Any]], RedactionStats]:
    """
    对多行数据进行脱敏处理，并返回统计信息

    Args:
        rows: 原始数据行列表
        sensitive_fields: 需要脱敏的字段名集合（可选）

    Returns:
        (脱敏后的数据行列表, 脱敏统计信息)
    """
    if not rows:
        return rows, RedactionStats()

    stats = RedactionStats(total_rows=len(rows))
    result = []

    for row in rows:
        stats.total_fields += len(row)
        redacted_row = {}

        for field_name, value in row.items():
            if value is None:
                redacted_row[field_name] = None
                continue

            # 检查身份证号
            if isinstance(value, str) and is_id_card(value):
                redacted_row[field_name] = "[已拦截-身份证号]"
                stats.blocked_fields += 1
                continue

            # 精确匹配敏感字段名
            field_lower = field_name.lower()
            should_redact = False

            if sensitive_fields and field_name in sensitive_fields:
                should_redact = True
            elif field_lower in SENSITIVE_PHONE_FIELDS:
                should_redact = True
            elif field_lower in SENSITIVE_NAME_FIELDS:
                should_redact = True
            elif field_lower in SENSITIVE_ADDRESS_FIELDS:
                should_redact = True

            if should_redact and isinstance(value, str):
                if field_lower in SENSITIVE_PHONE_FIELDS:
                    redacted_row[field_name] = redact_phone(value)
                elif field_lower in SENSITIVE_NAME_FIELDS:
                    redacted_row[field_name] = redact_name(value)
                elif field_lower in SENSITIVE_ADDRESS_FIELDS:
                    redacted_row[field_name] = redact_address(value)
                else:
                    redacted_row[field_name] = value
                stats.redacted_fields += 1
            else:
                redacted_row[field_name] = value

        result.append(redacted_row)

    return result, stats

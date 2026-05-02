"""
表白名单策略模块

本模块定义了 AptInsight 系统中允许访问的数据库表和列的白名单。
这是 SQL 安全策略的核心组件，确保 LLM 生成的 SQL 只能访问预定义的表和字段。

安全原则：
1. 默认拒绝 - 不在白名单中的表和列一律拒绝访问
2. 最小权限 - 只暴露业务分析必需的字段
3. 敏感隔离 - 密码、身份证号等敏感字段绝不暴露
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ColumnPolicy:
    """
    列策略 - 定义单个列的访问权限

    Attributes:
        name: 列名（数据库中的实际字段名）
        description: 列的中文描述（用于日志和错误提示）
        is_sensitive: 是否为敏感字段（敏感字段会被脱敏处理）
        is_blocked: 是否完全禁止访问（如密码字段，绝不返回）
    """
    name: str
    description: str
    is_sensitive: bool = False
    is_blocked: bool = False


@dataclass(frozen=True)
class TablePolicy:
    """
    表策略 - 定义单个表的访问权限

    Attributes:
        name: 表名（数据库中的实际表名）
        description: 表的中文描述
        allowed_columns: 允许访问的列列表
        alias: 表的常用别名（用于 SQL 解析时的别名匹配）
    """
    name: str
    description: str
    allowed_columns: frozenset[ColumnPolicy]
    alias: Optional[str] = None


def _col(name: str, desc: str, sensitive: bool = False, blocked: bool = False) -> ColumnPolicy:
    """快捷函数：创建列策略对象"""
    return ColumnPolicy(name=name, description=desc, is_sensitive=sensitive, is_blocked=blocked)


# ============================================================================
# 核心业务表白名单
# ============================================================================
# 这里定义了系统允许访问的所有业务表及其字段
# 新增表时必须在此处注册，否则 SQL 守卫会拒绝执行

ALLOWED_TABLES: frozenset[TablePolicy] = frozenset({

    # ----- 公寓信息表 -----
    # 存储公寓的基本信息，包括名称、地址、地理位置等
    TablePolicy(
        name="apartment_info",
        description="公寓信息表",
        alias="ai",
        allowed_columns=frozenset({
            _col("id", "公寓ID"),
            _col("name", "公寓名称"),
            _col("introduction", "公寓介绍"),
            _col("province_id", "省份ID"),
            _col("province_name", "省份名称"),
            _col("city_id", "城市ID"),
            _col("city_name", "城市名称"),
            _col("district_id", "区县ID"),
            _col("district_name", "区县名称"),
            _col("address_detail", "详细地址"),
            _col("latitude", "经度"),  # 注意：数据库注释有误，实际存储经度
            _col("longitude", "纬度"),  # 注意：数据库注释有误，实际存储纬度
            _col("phone", "公寓前台电话", sensitive=True),  # 敏感：需要脱敏
            _col("is_release", "是否发布"),
            # 通用字段
            _col("create_time", "创建时间"),
            _col("update_time", "更新时间"),
            _col("is_deleted", "逻辑删除标记"),
        }),
    ),

    # ----- 房间信息表 -----
    # 存储房间的基本信息，包括房间号、租金、所属公寓等
    TablePolicy(
        name="room_info",
        description="房间信息表",
        alias="ri",
        allowed_columns=frozenset({
            _col("id", "房间ID"),
            _col("room_number", "房间号"),
            _col("rent", "租金（元/月）"),
            _col("apartment_id", "所属公寓ID"),
            _col("is_release", "是否发布"),
            # 通用字段
            _col("create_time", "创建时间"),
            _col("update_time", "更新时间"),
            _col("is_deleted", "逻辑删除标记"),
        }),
    ),

    # ----- 预约看房信息表 -----
    # 存储用户的预约看房记录
    TablePolicy(
        name="view_appointment",
        description="预约看房信息表",
        alias="va",
        allowed_columns=frozenset({
            _col("id", "预约ID"),
            _col("user_id", "用户ID"),
            _col("name", "用户姓名", sensitive=True),  # 敏感：需要脱敏
            _col("phone", "用户手机号", sensitive=True),  # 敏感：需要脱敏
            _col("apartment_id", "预约公寓ID"),
            _col("appointment_time", "预约时间"),
            _col("additional_info", "备注"),
            _col("appointment_status", "预约状态"),  # 1待看房 2已取消 3已看房
            # 通用字段
            _col("create_time", "创建时间"),
            _col("update_time", "更新时间"),
            _col("is_deleted", "逻辑删除标记"),
        }),
    ),

    # ----- 租约信息表 -----
    # 存储租约合同的核心信息
    TablePolicy(
        name="lease_agreement",
        description="租约信息表",
        alias="la",
        allowed_columns=frozenset({
            _col("id", "租约ID"),
            _col("phone", "承租人手机号", sensitive=True),  # 敏感：需要脱敏
            _col("name", "承租人姓名", sensitive=True),  # 敏感：需要脱敏
            _col("identification_number", "身份证号", blocked=True),  # 严禁返回！
            _col("apartment_id", "签约公寓ID"),
            _col("room_id", "签约房间ID"),
            _col("lease_start_date", "租约开始日期"),
            _col("lease_end_date", "租约结束日期"),
            _col("lease_term_id", "租期ID"),
            _col("rent", "租金（元/月）"),
            _col("deposit", "押金"),
            _col("payment_type_id", "支付类型ID"),
            _col("status", "租约状态"),  # 见 LeaseStatus 枚举
            _col("source_type", "租约来源"),  # 1新签 2续约
            _col("additional_info", "备注"),
            # 通用字段
            _col("create_time", "创建时间"),
            _col("update_time", "更新时间"),
            _col("is_deleted", "逻辑删除标记"),
        }),
    ),

    # ----- 租客评价表 -----
    # 存储租客对公寓和房间的评价
    TablePolicy(
        name="tenant_review",
        description="租客评价表",
        alias="tr",
        allowed_columns=frozenset({
            _col("id", "评价ID"),
            _col("user_id", "评价用户ID"),
            _col("apartment_id", "公寓ID"),
            _col("room_id", "房间ID"),
            _col("rating", "评分"),
            _col("content", "评价内容"),
            # 通用字段
            _col("create_time", "创建时间"),
            _col("update_time", "更新时间"),
            _col("is_deleted", "逻辑删除标记"),
        }),
    ),

    # ----- 浏览历史表 -----
    # 记录用户浏览房间的行为数据
    TablePolicy(
        name="browsing_history",
        description="浏览历史表",
        alias="bh",
        allowed_columns=frozenset({
            _col("id", "浏览记录ID"),
            _col("user_id", "用户ID"),
            _col("room_id", "浏览房间ID"),
            _col("browse_time", "浏览时间"),
            # 通用字段
            _col("create_time", "创建时间"),
            _col("update_time", "更新时间"),
            _col("is_deleted", "逻辑删除标记"),
        }),
    ),

    # ----- 地区表 -----
    # 省份信息表
    TablePolicy(
        name="province_info",
        description="省份信息表",
        alias="pi",
        allowed_columns=frozenset({
            _col("id", "省份ID"),
            _col("name", "省份名称"),
        }),
    ),

    # 城市信息表
    TablePolicy(
        name="city_info",
        description="城市信息表",
        alias="ci",
        allowed_columns=frozenset({
            _col("id", "城市ID"),
            _col("name", "城市名称"),
            _col("province_id", "所属省份ID"),
        }),
    ),

    # 区县信息表
    TablePolicy(
        name="district_info",
        description="区县信息表",
        alias="di",
        allowed_columns=frozenset({
            _col("id", "区域ID"),
            _col("name", "区域名称"),
            _col("city_id", "所属城市ID"),
        }),
    ),

    # ----- 配置字典表 -----
    # 租期配置表
    TablePolicy(
        name="lease_term",
        description="租期配置表",
        alias="lt",
        allowed_columns=frozenset({
            _col("id", "租期ID"),
            _col("month_count", "租期月数"),
            _col("unit", "单位"),
        }),
    ),

    # 支付方式表
    TablePolicy(
        name="payment_type",
        description="支付方式表",
        alias="pt",
        allowed_columns=frozenset({
            _col("id", "支付方式ID"),
            _col("name", "付款方式名称"),
            _col("pay_month_count", "每次支付租期数"),
            _col("additional_info", "付费说明"),
        }),
    ),

    # 标签信息表
    TablePolicy(
        name="label_info",
        description="标签信息表",
        alias="li",
        allowed_columns=frozenset({
            _col("id", "标签ID"),
            _col("type", "类型"),  # 1公寓 2房间
            _col("name", "标签名称"),
        }),
    ),

    # 配套设施表
    TablePolicy(
        name="facility_info",
        description="配套设施表",
        alias="fi",
        allowed_columns=frozenset({
            _col("id", "配套ID"),
            _col("type", "类型"),  # 1公寓 2房间
            _col("name", "配套名称"),
            _col("icon", "图标"),
        }),
    ),

    # ----- 关系表 -----
    # 公寓配套关系表
    TablePolicy(
        name="apartment_facility",
        description="公寓配套关系表",
        alias="af",
        allowed_columns=frozenset({
            _col("apartment_id", "公寓ID"),
            _col("facility_id", "配套ID"),
        }),
    ),

    # 公寓标签关系表
    TablePolicy(
        name="apartment_label",
        description="公寓标签关系表",
        alias="al",
        allowed_columns=frozenset({
            _col("apartment_id", "公寓ID"),
            _col("label_id", "标签ID"),
        }),
    ),

    # 房间配套关系表
    TablePolicy(
        name="room_facility",
        description="房间配套关系表",
        alias="rf",
        allowed_columns=frozenset({
            _col("room_id", "房间ID"),
            _col("facility_id", "配套ID"),
        }),
    ),

    # 房间标签关系表
    TablePolicy(
        name="room_label",
        description="房间标签关系表",
        alias="rl",
        allowed_columns=frozenset({
            _col("room_id", "房间ID"),
            _col("label_id", "标签ID"),
        }),
    ),
})


# ============================================================================
# 快速查找索引
# ============================================================================
# 为了提高查询效率，预先构建表名和别名的索引

# 表名 -> 表策略 的映射
TABLE_BY_NAME: dict[str, TablePolicy] = {
    table.name: table for table in ALLOWED_TABLES
}

# 表别名 -> 表策略 的映射（用于 SQL 解析时快速查找）
TABLE_BY_ALIAS: dict[str, TablePolicy] = {
    table.alias: table for table in ALLOWED_TABLES if table.alias
}


def get_table_policy(table_name: str) -> Optional[TablePolicy]:
    """
    根据表名获取表策略

    Args:
        table_name: 表名（支持别名）

    Returns:
        TablePolicy 如果找到，否则 None
    """
    # 先尝试直接匹配表名
    if table_name in TABLE_BY_NAME:
        return TABLE_BY_NAME[table_name]

    # 再尝试匹配别名
    return TABLE_BY_ALIAS.get(table_name)


def is_column_allowed(table_name: str, column_name: str) -> bool:
    """
    检查指定表的列是否在白名单中

    Args:
        table_name: 表名
        column_name: 列名

    Returns:
        True 如果列被允许访问，否则 False
    """
    table = get_table_policy(table_name)
    if not table:
        return False

    return any(col.name == column_name for col in table.allowed_columns)


def is_column_sensitive(table_name: str, column_name: str) -> bool:
    """
    检查指定列是否为敏感字段

    Args:
        table_name: 表名
        column_name: 列名

    Returns:
        True 如果列是敏感字段，否则 False
    """
    table = get_table_policy(table_name)
    if not table:
        return False

    for col in table.allowed_columns:
        if col.name == column_name:
            return col.is_sensitive

    return False


def is_column_blocked(table_name: str, column_name: str) -> bool:
    """
    检查指定列是否被完全禁止访问

    Args:
        table_name: 表名
        column_name: 列名

    Returns:
        True 如果列被禁止访问，否则 False
    """
    table = get_table_policy(table_name)
    if not table:
        return False

    for col in table.allowed_columns:
        if col.name == column_name:
            return col.is_blocked

    return False


def get_sensitive_columns(table_name: str) -> list[ColumnPolicy]:
    """
    获取指定表的所有敏感列

    Args:
        table_name: 表名

    Returns:
        敏感列列表
    """
    table = get_table_policy(table_name)
    if not table:
        return []

    return [col for col in table.allowed_columns if col.is_sensitive]


def get_blocked_columns(table_name: str) -> list[ColumnPolicy]:
    """
    获取指定表的所有禁止访问列

    Args:
        table_name: 表名

    Returns:
        禁止访问列列表
    """
    table = get_table_policy(table_name)
    if not table:
        return []

    return [col for col in table.allowed_columns if col.is_blocked]

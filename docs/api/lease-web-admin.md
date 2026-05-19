# lease web-admin API 文档

**服务**: lease web-admin
**端口**: 8080
**技术栈**: Spring Boot 3, Java 17, MyBatis-Plus
**数据库**: MySQL `lease`

## 认证

JWT Token 通过 `/admin/login` 获取，后续请求在 `Authorization` header 中携带。

## 登录

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/admin/login` | 登录 (返回 JWT) |
| GET | `/admin/login/captcha` | 获取验证码 |
| GET | `/admin/info` | 当前管理员信息 |

## 公寓管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/admin/apartment/saveOrUpdate` | 创建/更新公寓 |
| GET | `/admin/apartment/pageItem` | 公寓分页列表 |
| GET | `/admin/apartment/getDetailById?id={id}` | 公寓详情 |
| DELETE | `/admin/apartment/removeById?id={id}` | 删除公寓 |
| POST | `/admin/apartment/updateReleaseStatusById` | 更新发布状态 |
| GET | `/admin/apartment/listInfoByDistrictId?districtId={id}` | 按区域查公寓 |

## 房间管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/admin/room/saveOrUpdate` | 创建/更新房间 |
| GET | `/admin/room/pageItem` | 房间分页列表 |
| GET | `/admin/room/getDetailById?id={id}` | 房间详情 |
| DELETE | `/admin/room/removeById?id={id}` | 删除房间 |
| POST | `/admin/room/updateReleaseStatusById` | 更新发布状态 |
| GET | `/admin/room/listBasicByApartmentId?apartmentId={id}` | 公寓下的房间列表 |

## 预约管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/appointment/page` | 预约分页列表 |
| POST | `/admin/appointment/updateStatusById` | 更新预约状态 |

## 租约管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/admin/agreement/saveOrUpdate` | 创建/更新租约 |
| GET | `/admin/agreement/page` | 租约分页列表 |
| GET | `/admin/agreement/getById?id={id}` | 租约详情 |
| DELETE | `/admin/agreement/removeById?id={id}` | 删除租约 |
| POST | `/admin/agreement/updateStatusById` | 更新租约状态 |

## 系统管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/system/user/page` | 系统用户列表 |
| POST | `/admin/system/user/saveOrUpdate` | 创建/更新用户 |
| GET | `/admin/system/post/page` | 岗位列表 |
| POST | `/admin/system/post/saveOrUpdate` | 创建/更新岗位 |

## 属性/标签/设施/费用

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/attr/list` | 属性列表 |
| GET | `/admin/fee/list` | 费用列表 |
| GET | `/admin/facility/list` | 设施列表 |
| GET | `/admin/label/list` | 标签列表 |

## 文件上传

文件通过 MinIO 存储，连接信息:
- 地址: `http://127.0.0.1:9000`
- Bucket: `lease`
- 凭证: `minioadmin` / `minioadmin`

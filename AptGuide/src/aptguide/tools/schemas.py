from pydantic import BaseModel


class AppointmentCreateRequest(BaseModel):
    """预约创建请求"""
    room_id: int
    appointment_time: str
    user_id: str
    remark: str | None = None


class AppointmentCreateResponse(BaseModel):
    """预约创建响应"""
    appointment_id: str
    room_id: int
    room_title: str
    appointment_time: str
    status: str
    created_at: str | None = None


class AppointmentQueryRequest(BaseModel):
    """预约查询请求"""
    user_id: str


class AppointmentQueryResponse(BaseModel):
    """预约查询响应"""
    appointments: list[dict]


class LeaseQueryRequest(BaseModel):
    """租约查询请求"""
    user_id: str


class LeaseQueryResponse(BaseModel):
    """租约查询响应"""
    leases: list[dict]

package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;

@Data
public class AppointmentCreateRequest {
    private Long apartmentId;
    private Long roomId;
    private String appointmentTime;
    private String remark;
}

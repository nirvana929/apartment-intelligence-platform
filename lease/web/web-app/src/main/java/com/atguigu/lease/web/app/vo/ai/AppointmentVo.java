package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;

@Data
public class AppointmentVo {
    private Long appointmentId;
    private String appointmentNo;
    private String status;
    private String appointmentTime;
    private String apartmentName;
    private String roomNumber;
}

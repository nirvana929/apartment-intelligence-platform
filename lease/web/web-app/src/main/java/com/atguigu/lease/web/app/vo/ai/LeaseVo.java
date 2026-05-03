package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;

@Data
public class LeaseVo {
    private Long leaseId;
    private String status;
    private String apartmentName;
    private String roomNumber;
    private String startDate;
    private String endDate;
    private Integer rent;
    private String paymentType;
    private Integer renewalWindowDays;
}

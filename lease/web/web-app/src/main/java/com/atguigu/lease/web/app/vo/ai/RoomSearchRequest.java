package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;
import java.util.List;

@Data
public class RoomSearchRequest {
    private Long cityId;
    private Long districtId;
    private Integer maxRent;
    private Integer minRent;
    private String paymentType;
    private Integer leaseTermMonths;
    private List<String> tags;
    private List<Long> roomIds;
    private Integer limit = 5;
}

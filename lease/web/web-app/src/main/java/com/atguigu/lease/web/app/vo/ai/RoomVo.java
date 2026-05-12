package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;
import java.util.List;

@Data
public class RoomVo {
    private Long roomId;
    private String roomNumber;
    private Long apartmentId;
    private String apartmentName;
    private Integer rent;
    private List<String> paymentTypes;
    private List<Integer> leaseTerms;
    private Integer area;
    private String layout;
    private List<String> tags;
    private String thumbnailUrl;
    private Boolean isAppointable;
    private Long cityId;
    private String cityName;
    private Long districtId;
    private String districtName;
    private String areaLabel;
    private List<String> facilities;
    private String audienceSummary;
    private String dataSource;
}

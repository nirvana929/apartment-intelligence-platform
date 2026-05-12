package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;
import java.util.List;

@Data
public class RoomSyncVo {
    private Long roomId;
    private String roomNumber;
    private Long apartmentId;
    private String apartmentName;
    private Long cityId;
    private String cityName;
    private Long districtId;
    private String districtName;
    private String areaLabel;
    private Integer rent;
    private Integer area;
    private String layout;
    private List<String> paymentTypes;
    private List<Integer> leaseTerms;
    private List<String> tags;
    private List<String> facilities;
    private String thumbnailUrl;
    private Boolean isRelease;
    private Boolean isAppointable;
    private String audienceSummary;
    private String dataSource;
    private Long updatedAt;
}

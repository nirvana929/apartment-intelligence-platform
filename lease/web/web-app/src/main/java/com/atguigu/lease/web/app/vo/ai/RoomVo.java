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
}

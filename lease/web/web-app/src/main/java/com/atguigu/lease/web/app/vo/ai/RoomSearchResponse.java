package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;
import java.util.List;

@Data
public class RoomSearchResponse {
    private List<RoomVo> rooms;
    private Integer total;
}

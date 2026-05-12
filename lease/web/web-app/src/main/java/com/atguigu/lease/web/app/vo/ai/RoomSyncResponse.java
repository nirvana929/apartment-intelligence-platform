package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;
import java.util.List;

@Data
public class RoomSyncResponse {
    private List<RoomSyncVo> rooms;
    private Integer total;
    private String syncVersion;
}

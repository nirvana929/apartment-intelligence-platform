package com.atguigu.lease.web.app.controller.ai;

import com.atguigu.lease.common.result.Result;
import com.atguigu.lease.web.app.service.RoomInfoService;
import com.atguigu.lease.web.app.vo.ai.RoomSearchRequest;
import com.atguigu.lease.web.app.vo.ai.RoomSearchResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;

@Tag(name = "AI工具接口")
@RestController
@RequestMapping("/internal/ai/tools")
public class AiToolController {

    private final RoomInfoService service;

    public AiToolController(RoomInfoService service) {
        this.service = service;
    }

    @Operation(summary = "搜索房间")
    @PostMapping("/room/search")
    public Result<RoomSearchResponse> searchRooms(@RequestBody RoomSearchRequest request,
                                                  @RequestHeader("X-User-Id") Long userId) {
        // TODO: Task 3 will implement real search logic
        RoomSearchResponse response = new RoomSearchResponse();
        response.setRooms(new ArrayList<>());
        response.setTotal(0);
        return Result.ok(response);
    }

    @Operation(summary = "健康检查")
    @GetMapping("/health")
    public Result<String> health() {
        return Result.ok("ok");
    }
}

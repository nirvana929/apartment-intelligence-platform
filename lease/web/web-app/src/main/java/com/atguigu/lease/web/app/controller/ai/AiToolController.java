package com.atguigu.lease.web.app.controller.ai;

import com.atguigu.lease.common.result.Result;
import com.atguigu.lease.model.entity.LabelInfo;
import com.atguigu.lease.model.entity.LeaseTerm;
import com.atguigu.lease.model.entity.PaymentType;
import com.atguigu.lease.model.enums.ReleaseStatus;
import com.atguigu.lease.web.app.service.RoomInfoService;
import com.atguigu.lease.web.app.vo.ai.RoomSearchRequest;
import com.atguigu.lease.web.app.vo.ai.RoomSearchResponse;
import com.atguigu.lease.web.app.vo.ai.RoomVo;
import com.atguigu.lease.web.app.vo.room.RoomDetailVo;
import com.atguigu.lease.web.app.vo.room.RoomItemVo;
import com.atguigu.lease.web.app.vo.room.RoomQueryVo;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

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
                                                  // userId is part of the internal API contract; reserved for future per-user filtering
                                                  @RequestHeader("X-User-Id") Long userId) {
        List<RoomItemVo> roomItems;

        if (request.getRoomIds() != null && !request.getRoomIds().isEmpty()) {
            // When specific room IDs are requested, fetch them directly
            roomItems = request.getRoomIds().stream()
                    .map(id -> {
                        RoomItemVo item = new RoomItemVo();
                        item.setId(id);
                        return item;
                    })
                    .collect(Collectors.toList());
        } else {
            // Build query VO from request parameters
            RoomQueryVo queryVo = new RoomQueryVo();
            queryVo.setCityId(request.getCityId());
            queryVo.setDistrictId(request.getDistrictId());
            if (request.getMinRent() != null) {
                queryVo.setMinRent(BigDecimal.valueOf(request.getMinRent()));
            }
            if (request.getMaxRent() != null) {
                queryVo.setMaxRent(BigDecimal.valueOf(request.getMaxRent()));
            }

            int limit = (request.getLimit() != null && request.getLimit() > 0) ? request.getLimit() : 5;
            Page<RoomItemVo> page = new Page<>(1, limit);
            IPage<RoomItemVo> pageResult = service.pageItem(page, queryVo);
            roomItems = pageResult.getRecords();
        }

        // Convert each room item to full RoomVo by fetching details
        List<RoomVo> roomVos = new ArrayList<>();
        for (RoomItemVo item : roomItems) {
            RoomDetailVo detail = service.getDetailById(item.getId());
            if (detail == null) {
                continue;
            }
            roomVos.add(convertToRoomVo(detail));
        }

        // Apply post-filters for criteria not supported by the DB query
        roomVos = applyPostFilters(roomVos, request);

        RoomSearchResponse response = new RoomSearchResponse();
        response.setRooms(roomVos);
        response.setTotal(roomVos.size());
        return Result.ok(response);
    }

    @Operation(summary = "健康检查")
    @GetMapping("/health")
    public Result<String> health() {
        return Result.ok("ok");
    }

    private RoomVo convertToRoomVo(RoomDetailVo detail) {
        RoomVo vo = new RoomVo();
        vo.setRoomId(detail.getId());
        vo.setRoomNumber(detail.getRoomNumber());
        vo.setApartmentId(detail.getApartmentId());
        vo.setApartmentName(detail.getApartmentItemVo() != null
                ? detail.getApartmentItemVo().getName() : null);
        vo.setRent(detail.getRent() != null ? detail.getRent().intValue() : null);

        // Payment types
        List<PaymentType> paymentTypeList = detail.getPaymentTypeList();
        vo.setPaymentTypes(paymentTypeList != null
                ? paymentTypeList.stream()
                        .map(PaymentType::getName)
                        .filter(Objects::nonNull)
                        .collect(Collectors.toList())
                : Collections.emptyList());

        // Lease terms
        List<LeaseTerm> leaseTermList = detail.getLeaseTermList();
        vo.setLeaseTerms(leaseTermList != null
                ? leaseTermList.stream()
                        .map(LeaseTerm::getMonthCount)
                        .filter(Objects::nonNull)
                        .collect(Collectors.toList())
                : Collections.emptyList());

        // Tags from labels
        vo.setTags(detail.getLabelInfoList() != null
                ? detail.getLabelInfoList().stream()
                        .map(LabelInfo::getName)
                        .filter(Objects::nonNull)
                        .collect(Collectors.toList())
                : Collections.emptyList());

        // Thumbnail: first graph URL
        vo.setThumbnailUrl(detail.getGraphVoList() != null && !detail.getGraphVoList().isEmpty()
                ? detail.getGraphVoList().get(0).getUrl() : null);

        // Area and layout are stored in EAV, skip for now
        vo.setArea(null);
        vo.setLayout(null);

        // Appointable: only released rooms can be appointed
        vo.setIsAppointable(ReleaseStatus.RELEASED.equals(detail.getIsRelease()));

        return vo;
    }

    private List<RoomVo> applyPostFilters(List<RoomVo> rooms, RoomSearchRequest request) {
        List<RoomVo> filtered = rooms;

        // Filter by lease term if specified
        if (request.getLeaseTermMonths() != null) {
            filtered = filtered.stream()
                    .filter(room -> room.getLeaseTerms() != null
                            && room.getLeaseTerms().contains(request.getLeaseTermMonths()))
                    .collect(Collectors.toList());
        }

        // Filter by tags if specified
        if (request.getTags() != null && !request.getTags().isEmpty()) {
            filtered = filtered.stream()
                    .filter(room -> room.getTags() != null
                            && room.getTags().containsAll(request.getTags()))
                    .collect(Collectors.toList());
        }

        return filtered;
    }
}

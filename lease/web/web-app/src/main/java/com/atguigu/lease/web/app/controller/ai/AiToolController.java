package com.atguigu.lease.web.app.controller.ai;

import com.atguigu.lease.common.result.Result;
import com.atguigu.lease.model.entity.LabelInfo;
import com.atguigu.lease.model.entity.LeaseTerm;
import com.atguigu.lease.model.entity.PaymentType;
import com.atguigu.lease.model.entity.ViewAppointment;
import com.atguigu.lease.model.enums.AppointmentStatus;
import com.atguigu.lease.model.enums.ReleaseStatus;
import com.atguigu.lease.model.entity.UserInfo;
import com.atguigu.lease.web.app.service.LeaseAgreementService;
import com.atguigu.lease.web.app.service.RoomInfoService;
import com.atguigu.lease.web.app.service.UserInfoService;
import com.atguigu.lease.web.app.service.ViewAppointmentService;
import com.atguigu.lease.web.app.vo.agreement.AgreementItemVo;
import com.atguigu.lease.web.app.vo.ai.AppointmentCreateRequest;
import com.atguigu.lease.web.app.vo.ai.AppointmentVo;
import com.atguigu.lease.web.app.vo.ai.LeaseVo;
import com.atguigu.lease.web.app.vo.ai.RoomSearchRequest;
import com.atguigu.lease.web.app.vo.ai.RoomSearchResponse;
import com.atguigu.lease.web.app.vo.ai.RoomVo;
import com.atguigu.lease.web.app.vo.appointment.AppointmentItemVo;
import com.atguigu.lease.web.app.vo.room.RoomDetailVo;
import com.atguigu.lease.web.app.vo.room.RoomItemVo;
import com.atguigu.lease.web.app.vo.room.RoomQueryVo;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

@Tag(name = "AI工具接口")
@RestController
@RequestMapping("/internal/ai/tools")
public class AiToolController {

    private final RoomInfoService service;
    private final ViewAppointmentService appointmentService;
    private final LeaseAgreementService leaseService;
    private final UserInfoService userInfoService;

    public AiToolController(RoomInfoService service,
                            ViewAppointmentService appointmentService,
                            LeaseAgreementService leaseService,
                            UserInfoService userInfoService) {
        this.service = service;
        this.appointmentService = appointmentService;
        this.leaseService = leaseService;
        this.userInfoService = userInfoService;
    }

    @Operation(summary = "搜索房间")
    @PostMapping("/room/search")
    public Result<RoomSearchResponse> searchRooms(@RequestBody RoomSearchRequest request,
                                                  @RequestHeader(value = "X-User-Id", required = false) Long userId) {
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

    @Operation(summary = "创建看房预约")
    @PostMapping("/appointment/create")
    public Result<Map<String, Object>> createAppointment(@RequestBody AppointmentCreateRequest request,
                                                          @RequestHeader("X-User-Id") Long userId) {
        ViewAppointment appointment = new ViewAppointment();
        appointment.setUserId(userId);
        appointment.setApartmentId(request.getApartmentId());
        appointment.setAppointmentStatus(AppointmentStatus.WAITING);

        // 解析预约时间
        if (request.getAppointmentTime() != null) {
            try {
                SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm");
                Date time = sdf.parse(request.getAppointmentTime());
                appointment.setAppointmentTime(time);
            } catch (ParseException e) {
                return Result.fail(202, "时间格式不正确，应为 yyyy-MM-dd HH:mm");
            }
        }

        appointment.setAdditionalInfo(request.getRemark());
        appointmentService.save(appointment);

        Map<String, Object> data = new HashMap<>();
        data.put("appointment_id", appointment.getId());
        data.put("status", appointment.getAppointmentStatus().name());
        data.put("appointment_time", request.getAppointmentTime());
        return Result.ok(data);
    }

    @Operation(summary = "查询当前用户预约列表")
    @GetMapping("/appointment/list-mine")
    public Result<List<AppointmentVo>> listMyAppointments(@RequestHeader("X-User-Id") Long userId) {
        List<AppointmentItemVo> items = appointmentService.listItem(userId);
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        List<AppointmentVo> result = items.stream().map(item -> {
            AppointmentVo vo = new AppointmentVo();
            vo.setAppointmentId(item.getId());
            vo.setAppointmentNo(null); // not available in AppointmentItemVo
            vo.setStatus(item.getAppointmentStatus() != null ? item.getAppointmentStatus().name() : null);
            vo.setAppointmentTime(item.getAppointmentTime() != null ? sdf.format(item.getAppointmentTime()) : null);
            vo.setApartmentName(item.getApartmentName());
            vo.setRoomNumber(null); // not available in AppointmentItemVo
            return vo;
        }).collect(Collectors.toList());
        return Result.ok(result);
    }

    @Operation(summary = "查询当前用户租约列表")
    @GetMapping("/lease/list-mine")
    public Result<List<LeaseVo>> listMyLeases(@RequestHeader("X-User-Id") Long userId) {
        UserInfo user = userInfoService.getById(userId);
        if (user == null || user.getPhone() == null) {
            return Result.ok(Collections.emptyList());
        }
        List<AgreementItemVo> items = leaseService.listItem(user.getPhone());
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
        List<LeaseVo> result = items.stream().map(item -> {
            LeaseVo vo = new LeaseVo();
            vo.setLeaseId(item.getId());
            vo.setStatus(item.getLeaseStatus() != null ? item.getLeaseStatus().name() : null);
            vo.setApartmentName(item.getApartmentName());
            vo.setRoomNumber(item.getRoomNumber());
            vo.setStartDate(item.getLeaseStartDate() != null ? sdf.format(item.getLeaseStartDate()) : null);
            vo.setEndDate(item.getLeaseEndDate() != null ? sdf.format(item.getLeaseEndDate()) : null);
            vo.setRent(item.getRent() != null ? item.getRent().intValue() : null);
            vo.setPaymentType(null); // not available in AgreementItemVo
            vo.setRenewalWindowDays(null); // not available in AgreementItemVo
            return vo;
        }).collect(Collectors.toList());
        return Result.ok(result);
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

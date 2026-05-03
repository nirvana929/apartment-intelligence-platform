package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
public class ChatResponse {
    private String reply;
    private List<Map<String, Object>> cards;
    private List<Map<String, Object>> actions;
    private Map<String, Object> pendingConfirmation;
    private List<String> sources;
    private String sessionId;
}

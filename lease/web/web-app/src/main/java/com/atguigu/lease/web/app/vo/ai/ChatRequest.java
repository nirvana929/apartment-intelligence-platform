package com.atguigu.lease.web.app.vo.ai;

import lombok.Data;

@Data
public class ChatRequest {
    private String message;
    private String sessionId;
}

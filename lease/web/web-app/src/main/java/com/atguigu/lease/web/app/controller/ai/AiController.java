package com.atguigu.lease.web.app.controller.ai;

import com.atguigu.lease.common.login.LoginUserHolder;
import com.atguigu.lease.common.result.Result;
import com.atguigu.lease.web.app.vo.ai.ChatRequest;
import com.atguigu.lease.web.app.vo.ai.ChatResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

@Tag(name = "AI对话接口")
@RestController
@RequestMapping("/app/ai")
public class AiController {

    @Value("${ai.guide.url:http://localhost:8100}")
    private String aptGuideUrl;

    @Value("${ai.internal.token:}")
    private String internalToken;

    @Operation(summary = "AI对话")
    @PostMapping("/chat")
    public Result<ChatResponse> chat(@RequestBody ChatRequest request) {

        // Get current logged-in user
        Long userId = LoginUserHolder.getLoginUser().getUserId();

        // Build request body for AptGuide
        Map<String, Object> body = new HashMap<>();
        body.put("message", request.getMessage());
        body.put("sessionId", request.getSessionId());
        body.put("userId", userId);

        // Call AptGuide service
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            if (internalToken != null && !internalToken.isEmpty()) {
                headers.set("X-Internal-Token", internalToken);
            }

            HttpEntity<Map<String, Object>> httpEntity = new HttpEntity<>(body, headers);
            RestTemplate restTemplate = new RestTemplate();
            ChatResponse response = restTemplate.postForObject(
                    aptGuideUrl + "/api/chat",
                    httpEntity,
                    ChatResponse.class
            );

            if (response != null) {
                return Result.ok(response);
            }
        } catch (Exception e) {
            // Log error and fall through to mock response
        }

        // Fallback mock response
        ChatResponse mockResponse = new ChatResponse();
        mockResponse.setReply("您好！我是AI找房助手，请问有什么可以帮您？");
        mockResponse.setCards(new ArrayList<>());
        mockResponse.setActions(new ArrayList<>());
        mockResponse.setSources(new ArrayList<>());
        mockResponse.setSessionId(request.getSessionId());

        return Result.ok(mockResponse);
    }
}

# Understanding Contract

## Principle

The LLM is the only component that interprets natural language into intent. Code validates the contract; it does not infer intent from string matching.

## Required Output

```json
{
  "route": "rag",
  "task": "room_search",
  "domain": "room",
  "action": "search",
  "confidence": 0.91,
  "hard_filters": {
    "max_rent": 3000,
    "district_id": 1,
    "area_text": "珠江新城"
  },
  "soft_preferences": ["有阳台", "采光好"],
  "retrieval_queries": ["珠江新城 3000以内 有阳台 采光好 房源"],
  "risk": {
    "level": "low",
    "response_mode": "normal_answer"
  },
  "clarification": {
    "needed": false,
    "question": ""
  },
  "reason": "User is asking to search rooms with constraints."
}
```

## Failure Policy

Return or convert to clarification when:

- model call fails;
- JSON parsing fails;
- schema validation fails;
- confidence is below threshold;
- route/task/action fields contradict each other;
- the model states that the request is ambiguous.

Clarification response:

```json
{
  "route": "clarify",
  "task": "clarify",
  "domain": "unknown",
  "action": "ask_clarification",
  "confidence": 0.0,
  "clarification": {
    "needed": true,
    "question": "请补充一下：您是想找房、咨询租房规则，还是处理预约/租约相关事项？"
  }
}
```

## Explicitly Forbidden

- Inferring route from `if "房" in message`.
- Inferring task from `if "吗" in message`.
- Inferring filters from regex or keyword tables as a fallback.
- Recovering from LLM failure with a heuristic classifier.

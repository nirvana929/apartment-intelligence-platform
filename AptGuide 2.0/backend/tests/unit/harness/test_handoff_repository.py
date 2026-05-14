from aptguide2.harness.handoff_repository import HandoffRepository


async def test_create_ticket_and_reply() -> None:
    repo = HandoffRepository()

    ticket = await repo.create_ticket(
        user_id="u1",
        session_id="s1",
        trigger="user_initiated",
        summary={"current_message": "转人工"},
    )
    await repo.add_message(ticket.ticket_id, sender="operator", content="您好，我来帮您。")

    detail = await repo.get_ticket(ticket.ticket_id)
    assert detail.ticket_id == ticket.ticket_id
    assert detail.status == "open"
    assert detail.messages[-1]["content"] == "您好，我来帮您。"


async def test_close_ticket_marks_closed() -> None:
    repo = HandoffRepository()
    ticket = await repo.create_ticket("u1", "s1", "user_initiated", {})

    await repo.close_ticket(ticket.ticket_id)

    assert (await repo.get_ticket(ticket.ticket_id)).status == "closed"


async def test_list_tickets_filters_by_status() -> None:
    repo = HandoffRepository()
    await repo.create_ticket("u1", "s1", "user_initiated", {})
    ticket2 = await repo.create_ticket("u2", "s2", "user_initiated", {})
    await repo.close_ticket(ticket2.ticket_id)

    open_tickets = await repo.list_tickets(status="open")
    closed_tickets = await repo.list_tickets(status="closed")

    assert len(open_tickets) == 1
    assert len(closed_tickets) == 1

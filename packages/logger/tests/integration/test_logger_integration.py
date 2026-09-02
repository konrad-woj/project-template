import asyncio
import json
import logging

import structlog

from logger import async_timer, configure_logger, timer


@timer
def _slow_sum(values: list[int]) -> int:
    return sum(values)


@async_timer
async def _slow_product(values: list[int]) -> int:
    await asyncio.sleep(0)
    result = 1
    for value in values:
        result *= value
    return result


async def test_configured_logger_emits_json_with_timer_context(capsys) -> None:
    configure_logger("INFO")
    logger: structlog.stdlib.BoundLogger = structlog.get_logger()

    assert _slow_sum([1, 2, 3]) == 6
    assert await _slow_product([2, 3, 4]) == 24
    logger.info("integration check", request_id="abc-123")

    captured = capsys.readouterr()
    records = [json.loads(line) for line in (captured.err + captured.out).splitlines() if line.startswith("{")]

    assert any(record["message"] == "integration check" and record["request_id"] == "abc-123" for record in records)
    by_message = {record["message"]: record for record in records}
    assert by_message["[END]"]["func_name"] == "_slow_sum"
    assert by_message["[TASK END]"]["task_name"] == "_slow_product"
    assert "elapsed" in by_message["[END]"]
    assert "elapsed" in by_message["[TASK END]"]
    assert logging.getLogger().level == logging.INFO

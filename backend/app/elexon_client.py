import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

from app.config import ELEXON_BASE_URL, DATA_DIR


class ElexonClient:
    def __init__(self):
        self.base_url = ELEXON_BASE_URL

    async def fetch(self, endpoint, params):
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient(
            timeout=60,
            follow_redirects=True
        ) as client:

            for attempt in range(4):
                try:
                    response = await client.get(
                        url,
                        params=params,
                        headers={"Accept": "application/json"}
                    )

                    response.raise_for_status()
                    result = response.json()

                    if isinstance(result, list):
                        return result

                    if isinstance(result, dict):
                        return result.get("data", [])

                    raise ValueError(
                        "Unexpected Elexon response format"
                    )

                except (
                    httpx.HTTPError,
                    ValueError
                ):
                    if attempt == 3:
                        raise

                    await asyncio.sleep(2 ** attempt)

    async def get_actuals(self, start, end):
        return await self.fetch(
            "/datasets/FUELHH/stream",
            {
                "publishDateTimeFrom": start,
                "publishDateTimeTo": end
            }
        )

    async def get_forecasts(self, start, end):
        return await self.fetch(
            "/datasets/WINDFOR/stream",
            {
                "publishDateTimeFrom": start,
                "publishDateTimeTo": end
            }
        )


def save_json(filename, data):
    path = DATA_DIR / filename

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    return path
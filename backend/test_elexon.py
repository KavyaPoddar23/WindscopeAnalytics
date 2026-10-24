import asyncio

from app.elexon_client import ElexonClient


async def main():
    client = ElexonClient()

    start = "2026-01-05T00:00:00Z"
    end = "2026-01-06T00:00:00Z"

    print("Fetching actual wind generation...")

    actuals = await client.get_actuals(start, end)

    wind_actuals = [
        row for row in actuals
        if row.get("fuelType") == "WIND"
    ]

    print("Actual wind records:", len(wind_actuals))

    if wind_actuals:
        print("Sample actual:", wind_actuals[0])

    print("\nFetching forecasts...")

    forecasts = await client.get_forecasts(start, end)

    print("Forecast records:", len(forecasts))

    if forecasts:
        print("Sample forecast:", forecasts[0])


if __name__ == "__main__":
    asyncio.run(main())
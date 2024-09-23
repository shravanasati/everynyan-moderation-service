import os
from src.engines.base import IModerationEngine
import httpx


class IBMMaxModerationEngine(IModerationEngine):
    def __init__(self, httpx_client: httpx.AsyncClient) -> None:
        CONTAINER_HOST = os.environ.get("MAX_COMMENT_CLASSIFIER_HOST", "localhost")
        CONTAINER_ADDR = f"http://{CONTAINER_HOST}:5000"
        self.PREDICTION_ENDPOINT = CONTAINER_ADDR + "/model/predict"
        self.client = httpx_client

    async def should_purge(self, text: str) -> bool:
        resp = await self.client.post(self.PREDICTION_ENDPOINT, json={"text": [text]})
        resp.raise_for_status()
        json_resp = resp.json()
        predictions: dict[str, float] = json_resp["results"][0]["predictions"]
        detected_toxic_labels = {k for k, v in predictions.items() if v > 0.8}
        print(text, predictions)

        purge_conditions = (
            len(detected_toxic_labels) >= 4,
            "severe_toxic" in detected_toxic_labels,
            predictions['toxic'] >= 0.98 and len(detected_toxic_labels) > 2
        )
        return any(purge_conditions)


async def test():
    async with httpx.AsyncClient() as client:
        engine = IBMMaxModerationEngine(client)
        print(await engine.should_purge("don't let those bitch ass hoes lie to you"))
        print(
            await engine.should_purge(
                "bitch ass nigga go die in a shitty hole alone no one will every help you"
            )
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(test())

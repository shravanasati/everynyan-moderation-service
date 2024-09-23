from pathlib import Path
from fastapi.testclient import TestClient
import pandas as pd
from .main import app
import pytest_check as check


def test_moderation():
    dataset = Path(__file__).parent / "labeled_data.csv"
    df = pd.read_csv(dataset).sample(10)
    tweets = df["tweet"]
    classes = df["class"]
    expected_purges = classes.apply(lambda x: x != 0)

    with TestClient(app) as client:
        for i in df.index:
            content = tweets[i]
            expected_purge = expected_purges[i]
            response = client.post("/moderate", json={"content": content})
            check.equal(response.status_code, 200)
            check.equal(response.json()["purge"], expected_purge)

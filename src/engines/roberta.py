from src.engines.base import IModerationEngine
from transformers import pipeline


class BertModerationEngine(IModerationEngine):
    def __init__(self) -> None:
        model_path = "prabhaskenche/pk-toxic-comment-classification-using-RoBERTa"
        self.pipeline = pipeline("text-classification", model=model_path)
        print(self.pipeline("You are a nerd"))

    def should_purge(self, text: str):
        label = self.pipeline(text)[0]["label"]
        print(text, label)
        return label == "toxic"


if __name__ == "__main__":
    engine = BertModerationEngine()

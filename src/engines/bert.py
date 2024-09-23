from src.engines.base import IModerationEngine
from transformers import (
    BertForSequenceClassification,
    BertTokenizer,
    TextClassificationPipeline,
)


class BertModerationEngine(IModerationEngine):
    def __init__(self) -> None:
        model_path = "JungleLee/bert-toxic-comment-classification"
        tokenizer = BertTokenizer.from_pretrained(model_path)
        model = BertForSequenceClassification.from_pretrained(model_path, num_labels=2)

        self.pipeline = TextClassificationPipeline(model=model, tokenizer=tokenizer)
        # print(
        #     self.pipeline(
        #         "I really like purva from cse-a class"
        #     )
        # )

    def should_purge(self, text: str):
        label = self.pipeline(text)[0]['label']
        print(text, label)
        return label == 'toxic'


if __name__ == "__main__":
    engine = BertModerationEngine()

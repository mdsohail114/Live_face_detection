"""Train or rebuild the demonstration risk-classification model."""

from ai_model import train_and_save_model
from config import Config


def main():
    Config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    Config.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    accuracy = train_and_save_model()
    print("Demo dataset:", Config.DATASET_PATH)
    print("Saved model:", Config.MODEL_PATH)
    print(f"Hold-out accuracy on synthetic data: {accuracy:.3f}")
    print(
        "Note: this accuracy is for the demonstration dataset only "
        "and does not measure real-world emergency prediction."
    )


if __name__ == "__main__":
    main()

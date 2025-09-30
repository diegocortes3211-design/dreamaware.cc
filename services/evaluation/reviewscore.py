#!/usr/bin/env python3
import os
import json
import glob
from huggingface_hub import InferenceClient

def assess(review_text, client, model_name):
    """
    Assesses a review using a specified Hugging Face model.
    """
    prompt = (
        "You are given a peer review. "
        "Return a JSON object with keys:\n"
        " - misinformed (bool)\n"
        " - issues (list of strings, e.g. 'incorrect premise', 'redundant question')\n"
        "Review:\n\"\"\"\n"
        f"{review_text}\n"
        "\"\"\""
    )
    response = client.text_generation(model=model_name, prompt=prompt)

    # The response from the model can be a raw string or an object
    # with a 'generated_text' attribute.
    if hasattr(response, 'generated_text'):
        return json.loads(response.generated_text)
    return json.loads(response)

def main():
    """
    Main function to run the review assessment process.
    """
    input_dir = os.getenv("INPUT_DIR", "data/reviews/incoming")
    output_file = os.getenv("OUTPUT_FILE", "reports/reviewscore.jsonl")
    hf_model = os.getenv("HF_MODEL", "ReviewScore-v1")

    client = InferenceClient()

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_file, "w") as out_f:
        for path in glob.glob(os.path.join(input_dir, "*.jsonl")):
            with open(path, "r") as in_f:
                for line in in_f:
                    record = json.loads(line)
                    if "review" in record:
                        result = assess(record["review"], client, hf_model)
                        output_record = {
                            "id": record.get("id"),
                            "misinformed": result.get("misinformed"),
                            "issues": result.get("issues")
                        }
                        out_f.write(json.dumps(output_record) + "\n")

if __name__ == "__main__":
    main()
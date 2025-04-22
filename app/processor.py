
import os
import json
from pathlib import Path
from mistralai import Mistral
from dotenv import load_dotenv
from pydantic import BaseModel, field_validator, ValidationError
import re

# Load API key from .env
load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    raise ValueError("❌ API Key not found in .env file!")

# Initialize Mistral client
client = Mistral(api_key=api_key)

def load_custom_prompt(json_path: str) -> str:
    if not Path(json_path).is_file():
        return None
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            prompt_data = json.load(f)
        return prompt_data.get("prompt", "").strip() or None
    except Exception as e:
        print(f"⚠️ Failed to load prompt from file: {e}. Using default prompt.")
        return None

def generate_prompt_from_input_schema(markdown_text, schema_path: str) -> str:
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        fields = "\n".join([f"  - {k} ({type(v).__name__})" for k, v in schema.items()])
    except Exception as e:
        print(f"⚠️ Failed to load schema from file: {e}. Using fallback prompt.")
        return generate_default_prompt(markdown_text)

    return (
        "You are an assistant extracting structured information from a medical PET/CT scan report.\n"
        "Respond ONLY with valid JSON. Do not include explanations or comments.\n"
        "Please extract and return the following fields in valid JSON format:\n"
        f"{fields}\n\n"
        "Text:\n"
        f"{markdown_text}"
    )

def generate_default_prompt(markdown_text: str) -> str:
    return (
        "You are an assistant extracting structured information from a medical PET/CT scan report.\n"
        "Respond ONLY with valid JSON. Do not include explanations or comments.\n"
        "Please extract and return the following fields in strict JSON format:\n"
        "  - name (string)\n"
        "  - sex (Male/Female/Other)\n"
        "  - age (integer)\n"
        "  - summary (a brief summary of diagnosis or findings)\n\n"
        "Text:\n"
        f"{markdown_text}"
    )

def parse_structured_output(llm_response_content: str) -> dict:
    try:
        match = re.search(r'\{.*\}', llm_response_content, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            return parsed
        else:
            raise ValueError("No JSON object found in response.")
    except Exception as e:
        print(f"❌ Error parsing LLM output: {e}")
        return None

def process_pdf_and_generate_summary(pdf_path, schema_file_path=None):
    pdf_file = Path(pdf_path)
    assert pdf_file.is_file(), f"{pdf_path} does not exist!"

    uploaded_file = client.files.upload(
        file={
            "file_name": pdf_file.stem,
            "content": pdf_file.read_bytes(),
        },
        purpose="ocr",
    )

    signed_url = client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)

    pdf_response = client.ocr.process(
        document={"document_url": signed_url.url},
        model="mistral-ocr-latest",
        include_image_base64=False
    )

    response_dict = json.loads(pdf_response.model_dump_json())

    markdown_blocks = []
    if 'pages' in response_dict:
        for page in response_dict['pages']:
            if 'markdown' in page and page['markdown'].strip():
                markdown_blocks.append(page['markdown'].strip())

    md_output_path = pdf_file.with_suffix('.md')
    with open(md_output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Summary of {pdf_file.name}\n\n")
        if markdown_blocks:
            f.write("\n\n---\n\n".join(markdown_blocks))
        else:
            f.write("❌ No markdown content extracted from the PDF.")
    print(f"✅ Markdown summary saved to: {md_output_path}")

    full_markdown = "\n".join(markdown_blocks)

    prompt_to_use = generate_prompt_from_input_schema(full_markdown, schema_file_path) \
        if schema_file_path else generate_default_prompt(full_markdown)

    response = client.chat.complete(
        model="mistral-medium",
        messages=[{"role": "user", "content": prompt_to_use}],
        max_tokens=300
    )

    parsed_output = parse_structured_output(response.choices[0].message.content)
    if not parsed_output:
        print("❌ Failed to extract structured data. Aborting.")
        return

    json_output_path = pdf_file.with_name(pdf_file.stem + '_structured.json')
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(parsed_output, f, indent=4, ensure_ascii=False)
    print(f"✅ Structured JSON saved to: {json_output_path}")


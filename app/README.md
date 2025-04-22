# 🧠 PET Scan Report Summarization API

This project provides a FastAPI-based web service for extracting structured information from PET/CT scan PDFs using OCR and LLMs.

## 🚀 Features

- Upload a PET/CT scan PDF
- Extract markdown summary using OCR
- Use Mistral LLM to extract structured JSON info
- Downloadable structured data

## 🔧 Setup

```bash
git clone https://github.com/yourusername/pet-scan-api.git
cd pet-scan-api
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 🔑 Add your Mistral API Key

Create a `.env` file in the root directory:

```
MISTRAL_API_KEY=your_api_key_here
```

## ▶️ Run the API

```bash
uvicorn app.main:app --reload
```

## 📬 API Usage

- Endpoint: `POST /summarize/`
- Form field: `file` (PDF)

Example with `curl`:
```bash
curl -X POST "http://127.0.0.1:8000/summarize/" -F "file=@test_ct_9.pdf"
```

## 🧪 Sample Files

- `test_ct_9.pdf`: Sample PET scan PDF
- `pet_ct_2.json`: Optional schema to guide extraction

## 📂 Output

- Markdown summary saved locally as `.md`
- Structured JSON saved as `_structured.json`
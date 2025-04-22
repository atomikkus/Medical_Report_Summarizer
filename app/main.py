
from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import JSONResponse
from pathlib import Path
import tempfile
import json

from app.processor import process_pdf_and_generate_summary

app = FastAPI(title="PET Scan Summarizer API")

@app.post("/summarize/")
async def summarize_pdf(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(await file.read())

        output = process_pdf_and_generate_summary(str(temp_path))

        return JSONResponse(content=output if output else {"error": "Extraction failed"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/results/")
def get_summary_files(filename: str = Query(..., description="Original PDF filename without extension")):
    try:
        base_path = Path(filename)
        md_path = base_path.with_suffix('.md')
        json_path = base_path.with_name(base_path.stem + '_structured.json')

        if not md_path.exists() or not json_path.exists():
            return JSONResponse(status_code=404, content={"error": "Files not found."})

        with open(md_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        with open(json_path, 'r', encoding='utf-8') as f:
            json_content = json.load(f)

        return JSONResponse(content={
            "filename": filename,
            "markdown_summary": markdown_content,
            "structured_json": json_content
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

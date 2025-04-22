
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pathlib import Path
import tempfile

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


## Add get request for getting the summary of the pdf and the md file and wrap both in a json response

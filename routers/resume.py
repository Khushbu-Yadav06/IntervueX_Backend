
from fastapi import APIRouter, UploadFile, File, HTTPException

from services.resume_service import extract_resume_text

router = APIRouter(
    prefix="/api/resume",
    tags=["Resume"]
)


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):

    # Check whether the uploaded file is a PDF
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    # Read the uploaded file
    pdf_bytes = await file.read()

    # Check whether the file is empty
    if not pdf_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded PDF is empty."
        )

    try:
        # Extract text from the PDF
        resume_text = extract_resume_text(pdf_bytes)

        if not resume_text:
            raise HTTPException(
                status_code=400,
                detail="No readable text found in the PDF. It may be scanned or empty."
            )

        return {
            "status": "success",
            "message": "Resume uploaded and processed successfully.",
            "filename": file.filename,
            "extracted_text": resume_text
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to read the uploaded PDF."
        )

    finally:
        await file.close()

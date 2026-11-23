
import fitz

def extract_resume_text(pdf_bytes: bytes) -> str:
    """
    Extract text from an uploaded PDF resume.
    """

    extracted_text = []

    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:

        for page in document:
            page_text = page.get_text("text")

            if page_text.strip():
                extracted_text.append(page_text)

    return "\n".join(extracted_text).strip()
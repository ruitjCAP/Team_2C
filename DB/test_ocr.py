
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io


# Optional: only needed on Windows if Tesseract is not in PATH
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text_from_pdf(pdf_path, output_txt_path=None, ocr_language="eng"):
    """
    Extracts text from a PDF.

    It reads:
    1. Selectable/searchable PDF text
    2. Text inside images or scanned pages using OCR

    Args:
        pdf_path: Path to the PDF file
        output_txt_path: Optional path to save extracted text
        ocr_language: OCR language, for example:
            "eng" for English
            "por" for Portuguese
            "eng+por" for English and Portuguese

    Returns:
        Full extracted text as a string
    """

    document = fitz.open(pdf_path)
    full_text = []

    for page_number in range(len(document)):
        page = document[page_number]

        full_text.append(f"\n--- Page {page_number + 1} ---\n")

        # 2. OCR the whole page as an image
        # This helps with scanned PDFs or text inside images


        pix = page.get_pixmap(dpi=300)
        image = Image.open(io.BytesIO(pix.tobytes("png")))

        ocr_text = pytesseract.image_to_string(image, lang=ocr_language)

        if ocr_text.strip():
            full_text.append(ocr_text)
        else:
            full_text.append("[No OCR text found]")

        full_text.append(f"\n--- END Page {page_number + 1} ---\n")

    document.close()

    result = "\n".join(full_text)

    if output_txt_path:
        with open(output_txt_path, "w", encoding="utf-8") as file:
            file.write(result)

    return result


if __name__ == "__main__":

    pdf_file = "pdfs/Policies_OCR.pdf"
  
    output_file = "extracted_text.txt"

    text = extract_text_from_pdf(
        pdf_path=pdf_file,
        output_txt_path=output_file,
        ocr_language="eng"
    )

    print(text)
    print(f"\nText saved to: {output_file}")
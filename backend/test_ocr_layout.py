import os
import sys

# Ensure src is in the python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

import fitz  # PyMuPDF
from rapidocr_onnxruntime import RapidOCR

def run():
    pdf_path = None
    import glob
    possible_dirs = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "data")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
    ]
    for d in possible_dirs:
        if os.path.exists(d):
            matches = glob.glob(os.path.join(d, "*basics-of-data-science-kpk.pdf"))
            if matches:
                pdf_path = matches[0]
                break

    if not pdf_path:
        print("PDF file basics-of-data-science-kpk.pdf not found.")
        return

    doc = fitz.open(pdf_path)
    # Page 7 is index 6
    page = doc[6]
    
    zoom = 2
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    
    engine = RapidOCR()
    ocr_result, _ = engine(img_bytes)
    
    if not ocr_result:
        print("No OCR results found.")
        return
        
    print(f"--- OCR Analysis for Page 7 (Page Num: {page.number + 1}) ---")
    print(f"{'Text':<40} | {'Height (px)':<12} | {'Width (px)':<12} | {'Coordinates'}")
    print("-" * 90)
    
    heights = []
    for line in ocr_result:
        box, text, conf = line
        # Bounding box is [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
        x1, y1 = box[0]
        x2, y2 = box[1]
        x3, y3 = box[2]
        x4, y4 = box[3]
        
        # Calculate width and height of bounding box
        width = int(((x2 - x1) + (x3 - x4)) / 2)
        height = int(((y4 - y1) + (y3 - y2)) / 2)
        heights.append(height)
        
        print(f"{text[:38]:<40} | {height:<12} | {width:<12} | {box}")
        
    avg_height = sum(heights) / len(heights)
    print(f"\nAverage Box Height: {avg_height:.2f}px")

if __name__ == "__main__":
    run()

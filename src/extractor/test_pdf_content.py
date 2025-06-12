# test_pdf_content.py 파일 생성
import pdfplumber

pdf_path = "../../data/input/MF PE Cyclone_20250609.pdf"

with pdfplumber.open(pdf_path) as pdf:
    text = pdf.pages[0].extract_text()
    
    print("PDF 텍스트 확인:")
    print("=" * 50)
    
    # 32-C-2222 찾기
    if '32-C-2222' in text:
        print("✓ 32-C-2222 발견!")
        idx = text.find('32-C-2222')
        print(f"위치: {text[idx-20:idx+30]}")
    else:
        print("✗ 32-C-2222 없음")
        
    # 24.6 찾기
    if '24.6' in text:
        print("\n✓ 24.6 발견!")
        idx = text.find('24.6')
        print(f"위치: {text[idx-20:idx+30]}")
    else:
        print("\n✗ 24.6 없음")
        
    # 412, 413 찾기
    if '412' in text:
        print("\n✓ 412 발견!")
    if '413' in text:
        print("✓ 413 발견!")
        
    # Item No 패턴 찾기
    import re
    item_match = re.search(r'Item\s*No[:\s]*([^\n]+)', text)
    if item_match:
        print(f"\nItem No 찾음: '{item_match.group(1)}'")
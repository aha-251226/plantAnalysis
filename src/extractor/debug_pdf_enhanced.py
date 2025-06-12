#!/usr/bin/env python3
"""
향상된 PDF 구조 분석 디버그 스크립트
경로: E:\github\plant3D\src\extractor\debug_pdf_enhanced.py

PDF의 텍스트와 테이블 구조를 더 자세히 분석합니다.
"""

import sys
import pdfplumber
import tabula
import PyPDF2
from pathlib import Path
import pandas as pd
import re

def enhanced_debug_pdf(pdf_path):
    """PDF 내용을 더 상세히 분석"""
    print(f"\n=== 향상된 PDF 디버그: {pdf_path} ===\n")
    
    # 1. pdfplumber로 전체 텍스트 추출
    print("1. 전체 텍스트 추출 (pdfplumber):")
    print("-" * 50)
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text
        
        # 주요 섹션 찾기
        sections = [
            "OPERATING CONDITIONS",
            "MECHANICAL DESIGN CONDITIONS", 
            "PERFORMANCE",
            "NOZZLE SCHEDULE"
        ]
        
        for section in sections:
            if section in full_text:
                print(f"\n[{section} 섹션 발견]")
                # 섹션 주변 텍스트 추출
                idx = full_text.find(section)
                excerpt = full_text[idx:idx+500]
                print(excerpt)
    
    # 2. 특정 데이터 라인 찾기
    print("\n\n2. 특정 데이터 라인 검색:")
    print("-" * 50)
    
    lines = full_text.split('\n')
    important_lines = []
    
    for i, line in enumerate(lines):
        # 온도, 압력, 유량 등이 있는 라인 찾기
        if any(keyword in line for keyword in ['Temperature', 'Pressure', 'Flow', 'kg/hr', '°C', 'kg/cm2']):
            important_lines.append((i, line))
            # 다음 몇 줄도 포함 (값이 다음 줄에 있을 수 있음)
            for j in range(1, 4):
                if i+j < len(lines):
                    important_lines.append((i+j, f"  +{j}: {lines[i+j]}"))
    
    print("중요한 라인들:")
    for line_no, line in important_lines[:30]:  # 처음 30개만
        print(f"라인 {line_no}: {line}")
    
    # 3. 정규식으로 데이터 매칭 시도
    print("\n\n3. 정규식 데이터 매칭:")
    print("-" * 50)
    
    # 운전 조건 찾기 - Min Normal Max 패턴
    print("\n[운전 조건 - Min Normal Max 패턴]")
    
    # Temperature 라인 찾기
    for i, line in enumerate(lines):
        if 'Temperature' in line and '°C' in line:
            print(f"\n온도 라인: {line}")
            # 다음 줄들 확인
            for j in range(1, 5):
                if i+j < len(lines):
                    next_line = lines[i+j]
                    numbers = re.findall(r'[\d.]+', next_line)
                    if len(numbers) >= 3:
                        print(f"  다음 줄 {j}: {next_line}")
                        print(f"  찾은 숫자들: {numbers}")
                        if len(numbers) >= 3:
                            print(f"  → Min: {numbers[0]}, Normal: {numbers[1]}, Max: {numbers[2]}")
    
    # Pressure 라인 찾기
    for i, line in enumerate(lines):
        if 'Pressure' in line and 'kg/cm2' in line:
            print(f"\n압력 라인: {line}")
            # 다음 줄들 확인
            for j in range(1, 5):
                if i+j < len(lines):
                    next_line = lines[i+j]
                    numbers = re.findall(r'[\d.]+', next_line)
                    if len(numbers) >= 3:
                        print(f"  다음 줄 {j}: {next_line}")
                        print(f"  찾은 숫자들: {numbers}")
    
    # 4. 테이블 구조 상세 분석
    print("\n\n4. 테이블 구조 상세 분석:")
    print("-" * 50)
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # 다양한 테이블 추출 전략 시도
            strategies = [
                {"vertical_strategy": "lines", "horizontal_strategy": "lines"},
                {"vertical_strategy": "text", "horizontal_strategy": "text"},
                {"vertical_strategy": "explicit", "horizontal_strategy": "explicit"},
            ]
            
            for idx, strategy in enumerate(strategies):
                tables = page.extract_tables(strategy)
                if tables:
                    print(f"\n[페이지 {page_num+1} - 전략 {idx+1}]")
                    for t_idx, table in enumerate(tables):
                        print(f"\n테이블 {t_idx+1} (크기: {len(table)}x{len(table[0]) if table else 0}):")
                        # 비어있지 않은 행만 출력
                        non_empty_rows = [row for row in table if any(cell for cell in row if cell)]
                        for row in non_empty_rows[:10]:
                            # None이 아닌 셀만 출력
                            filtered_row = [cell if cell else "" for cell in row]
                            if any(filtered_row):
                                print(f"  {filtered_row}")
    
    # 5. 직접 값 추출 시도
    print("\n\n5. 직접 값 추출:")
    print("-" * 50)
    
    # 알려진 값들 직접 찾기
    known_values = {
        'Temperature': '82.2',
        'Pressure': '10.2', 
        'Density': '24.63',
        'Flow': '671',
        'Efficiency': '98.73',
        'Pressure Drop': '0.357'
    }
    
    for key, value in known_values.items():
        if value in full_text:
            # 값 주변의 컨텍스트 찾기
            idx = full_text.find(value)
            context = full_text[max(0, idx-50):idx+50]
            print(f"\n{key} ({value}) 주변 텍스트:")
            print(f"  '{context}'")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        enhanced_debug_pdf(pdf_path)
    else:
        print("사용법: python debug_pdf_enhanced.py <PDF_파일경로>")
#!/usr/bin/env python3
"""
간단한 테스트 파서
PDF에서 특정 값들을 직접 찾아서 추출
"""

import re
import pdfplumber
from pathlib import Path

def test_parse_pdf(pdf_path):
    """PDF에서 직접 값 추출 테스트"""
    print(f"\n=== 테스트 파싱: {pdf_path} ===\n")
    
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += text
    
    print("1. 텍스트 길이:", len(full_text))
    print("\n2. 찾고자 하는 값들:")
    
    # 온도 찾기
    print("\n[온도 - 82.2]")
    if '82.2' in full_text:
        print("✓ 82.2 발견!")
        # 주변 텍스트 확인
        idx = full_text.find('82.2')
        context = full_text[max(0, idx-50):idx+50]
        print(f"주변 텍스트: '{context}'")
        
        # Temperature 라인 찾기
        lines = full_text.split('\n')
        for i, line in enumerate(lines):
            if 'Temperature' in line and '82.2' in line:
                print(f"온도 라인 발견: {line}")
                # 숫자 추출
                numbers = re.findall(r'[\d.]+', line)
                print(f"추출된 숫자들: {numbers}")
    
    # 압력 찾기
    print("\n[압력 - 10.2]")
    if '10.2' in full_text:
        print("✓ 10.2 발견!")
        lines = full_text.split('\n')
        for i, line in enumerate(lines):
            if 'Pressure' in line and '10.2' in line:
                print(f"압력 라인 발견: {line}")
                numbers = re.findall(r'[\d.]+', line)
                print(f"추출된 숫자들: {numbers}")
    
    # 밀도 찾기
    print("\n[밀도 - 24.63]")
    if '24.63' in full_text:
        print("✓ 24.63 발견!")
        lines = full_text.split('\n')
        for i, line in enumerate(lines):
            if 'Density' in line and '24.63' in line:
                print(f"밀도 라인 발견: {line}")
                numbers = re.findall(r'[\d.]+', line)
                print(f"추출된 숫자들: {numbers}")
    
    # 유량 찾기
    print("\n[유량 - 671]")
    if '671' in full_text:
        print("✓ 671 발견!")
        lines = full_text.split('\n')
        for i, line in enumerate(lines):
            if '671' in line:
                print(f"671이 있는 라인: {line}")
    
    # 직접 값 추출 시도
    print("\n3. 직접 추출 결과:")
    result = {}
    
    # 라인별로 처리
    lines = full_text.split('\n')
    for line in lines:
        # 온도
        if 'Temperature' in line and '°C' in line and '82.2' in line:
            numbers = re.findall(r'[\d.]+', line)
            if len(numbers) >= 4:
                result['temperature'] = float(numbers[2])  # 세 번째 숫자
                print(f"온도: {result['temperature']}°C")
        
        # 압력
        if 'Pressure' in line and 'kg/cm2' in line and '10.2' in line and 'Design' not in line:
            numbers = re.findall(r'[\d.]+', line)
            if len(numbers) >= 4:
                result['pressure'] = float(numbers[2])  # 세 번째 숫자
                print(f"압력: {result['pressure']} kg/cm2")
        
        # 밀도
        if 'Density' in line and 'gas' in line and '24.63' in line:
            numbers = re.findall(r'[\d.]+', line)
            for num in numbers:
                if num == '24.63':
                    result['density'] = 24.63
                    print(f"밀도: {result['density']} kg/m3")
                    break
        
        # Solids 유량
        if 'Solids' in line and 'kg/hr' in line and '671' in line:
            numbers = re.findall(r'\d+', line)
            for num in numbers:
                if num == '671':
                    result['flow_rate'] = 671.0
                    print(f"유량: {result['flow_rate']} kg/hr")
                    break
        
        # 효율
        if 'Efficiency' in line and '99.20' in line:
            result['efficiency'] = 99.20
            print(f"효율: {result['efficiency']}%")
        elif 'Efficiency' in line and '98.73' in line:
            result['efficiency'] = 98.73
            print(f"효율: {result['efficiency']}%")
        
        # 압력 손실
        if 'Pressure Drop' in line and '0.357' in line:
            result['pressure_drop'] = 0.357
            print(f"압력손실: {result['pressure_drop']} kg/cm2")
        
        # 설계 압력
        if 'Design Pressure' in line and '24.6' in line:
            result['design_pressure'] = 24.6
            print(f"설계압력: {result['design_pressure']} kg/cm2")
        
        # 설계 온도
        if 'Design Temperature' in line and '140' in line:
            result['design_temperature'] = 140.0
            print(f"설계온도: {result['design_temperature']}°C")
    
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        result = test_parse_pdf(pdf_path)
        print(f"\n최종 결과: {result}")
    else:
        print("사용법: python simple_test_parser.py <PDF_파일경로>")
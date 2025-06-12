#!/usr/bin/env python3
"""
__init__.py 파일 이름 수정 스크립트
경로: E:\github\plant3D\fix_init_files.py

잘못 생성된 **init**.py 파일들을 __init__.py로 수정합니다.
"""

import os
from pathlib import Path

def fix_init_files():
    """잘못된 init 파일들을 수정"""
    
    # Python 패키지 폴더들
    package_dirs = [
        "src",
        "src/extractor",
        "src/modeler",
        "src/simulator",
        "src/webserver"
    ]
    
    fixed_count = 0
    created_count = 0
    
    for package_dir in package_dirs:
        dir_path = Path(package_dir)
        
        if not dir_path.exists():
            print(f"⚠️  폴더가 없습니다: {package_dir}")
            continue
            
        # 잘못된 파일 찾기
        wrong_files = list(dir_path.glob("*init*.py"))
        
        # 올바른 __init__.py 경로
        correct_init = dir_path / "__init__.py"
        
        # 잘못된 파일이 있으면 삭제
        for wrong_file in wrong_files:
            if wrong_file.name != "__init__.py":
                print(f"🗑️  삭제: {wrong_file}")
                try:
                    wrong_file.unlink()
                    fixed_count += 1
                except Exception as e:
                    print(f"   ❌ 삭제 실패: {e}")
        
        # __init__.py가 없으면 생성
        if not correct_init.exists():
            try:
                # 파일 생성
                with open(str(correct_init), 'w', encoding='utf-8') as f:
                    f.write("# -*- coding: utf-8 -*-\n")
                print(f"✅ 생성: {correct_init}")
                created_count += 1
            except Exception as e:
                print(f"❌ 생성 실패: {correct_init} - {e}")
        else:
            print(f"✓  이미 존재: {correct_init}")
    
    # 결과 출력
    print("\n========== 작업 완료 ==========")
    print(f"삭제된 파일: {fixed_count}개")
    print(f"생성된 파일: {created_count}개")
    
    # 최종 확인
    print("\n현재 __init__.py 파일 목록:")
    for package_dir in package_dirs:
        init_file = Path(package_dir) / "__init__.py"
        if init_file.exists():
            print(f"✓ {init_file}")
        else:
            print(f"✗ {init_file} (없음)")


if __name__ == "__main__":
    print("__init__.py 파일 수정 작업을 시작합니다...")
    print(f"현재 디렉토리: {os.getcwd()}")
    
    # 현재 디렉토리가 plant3D인지 확인
    if not os.path.exists("config.yaml"):
        print("\n❌ 오류: plant3D 루트 디렉토리에서 실행해주세요.")
        print("cd E:\\github\\plant3D 명령 후 다시 실행하세요.")
    else:
        fix_init_files()
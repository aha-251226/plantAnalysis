#!/usr/bin/env python3
"""
Plant3D 프로젝트 폴더 구조 생성 스크립트
경로: E:\github\plant3D\setup_folders.py

사용법: python setup_folders.py
"""

import os
import sys
import yaml
from pathlib import Path


def load_config():
    """config.yaml 파일 로드"""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("Error: config.yaml 파일을 찾을 수 없습니다.")
        print("현재 디렉토리가 E:\\github\\plant3D 인지 확인하세요.")
        sys.exit(1)


def create_folder_structure():
    """프로젝트 폴더 구조 생성"""
    
    # 생성할 폴더 목록
    folders = [
        # 데이터 폴더
        "data",
        "data/input",
        "data/extracted",
        "data/templates",
        "data/templates/cyclone",
        "data/templates/pump",
        "data/templates/vessel",
        
        # 소스 코드 폴더
        "src",
        "src/extractor",
        "src/modeler",
        "src/simulator",
        "src/webserver",
        "src/webserver/static",
        "src/webserver/static/js",
        "src/webserver/static/css",
        "src/webserver/templates",
        
        # 출력 폴더
        "output",
        "output/models",
        "output/reports",
        "output/temp",
        
        # 로그 폴더
        "logs",
        
        # 문서 폴더
        "docs",
        "docs/images",
        
        # Unity 프로젝트 폴더 (기본 구조만)
        "UnityProject",
        "UnityProject/Plant3DViewer",
        "UnityProject/Plant3DViewer/Assets",
        "UnityProject/Plant3DViewer/Assets/Scripts",
        "UnityProject/Plant3DViewer/Assets/Models",
        "UnityProject/Plant3DViewer/Assets/Materials",
    ]
    
    # 폴더 생성
    created_folders = []
    existing_folders = []
    
    for folder in folders:
        folder_path = Path(folder)
        if not folder_path.exists():
            folder_path.mkdir(parents=True, exist_ok=True)
            created_folders.append(folder)
            print(f"✓ 생성됨: {folder}")
        else:
            existing_folders.append(folder)
            print(f"• 이미 존재: {folder}")
    
    # __init__.py 파일 생성 (Python 패키지로 만들기)
    python_packages = [
        "src",
        "src/extractor",
        "src/modeler", 
        "src/simulator",
        "src/webserver"
    ]
    
    for package in python_packages:
        init_file = Path(package) / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# -*- coding: utf-8 -*-\n")
            print(f"✓ __init__.py 생성: {package}")
    
    # 기본 README 파일 생성
    readme_files = {
        "data/input/README.md": "# 입력 폴더\n\nPDF 파일을 여기에 넣으세요.",
        "data/extracted/README.md": "# 추출 데이터 폴더\n\nPDF에서 추출된 JSON 데이터가 저장됩니다.",
        "data/templates/README.md": "# 장비 템플릿 폴더\n\n장비별 3D 모델 템플릿이 저장됩니다.",
        "output/models/README.md": "# 3D 모델 출력 폴더\n\n생성된 3D 모델 파일이 저장됩니다.",
        "output/reports/README.md": "# 리포트 폴더\n\n분석 리포트가 저장됩니다.",
    }
    
    for readme_path, content in readme_files.items():
        readme_file = Path(readme_path)
        if not readme_file.exists():
            readme_file.write_text(content, encoding='utf-8')
            print(f"✓ README 생성: {readme_path}")
    
    # .gitignore 파일 생성
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.env

# 로그
logs/
*.log

# 임시 파일
output/temp/
*.tmp

# 대용량 파일
*.pdf
*.fbx
*.obj
*.step

# Unity
UnityProject/Plant3DViewer/Library/
UnityProject/Plant3DViewer/Temp/
UnityProject/Plant3DViewer/Logs/
UnityProject/Plant3DViewer/Build/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
    
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        gitignore_path.write_text(gitignore_content)
        print("✓ .gitignore 파일 생성")
    
    # 요약 출력
    print("\n========== 폴더 구조 생성 완료 ==========")
    print(f"✓ 생성된 폴더: {len(created_folders)}개")
    print(f"• 기존 폴더: {len(existing_folders)}개")
    print(f"✓ 생성된 파일: {len(readme_files) + len(python_packages) + 1}개")
    print("\n다음 단계: main.py 파일을 생성하세요.")


if __name__ == "__main__":
    print("Plant3D 프로젝트 폴더 구조를 생성합니다...")
    print(f"현재 디렉토리: {os.getcwd()}")
    
    # 현재 디렉토리 확인
    if not os.path.exists("config.yaml"):
        print("\n경고: config.yaml 파일이 없습니다.")
        print("먼저 config.yaml 파일을 생성하세요.")
        sys.exit(1)
    
    # 폴더 구조 생성
    create_folder_structure()
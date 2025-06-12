#!/usr/bin/env python3
"""
Plant3D - PDF to 3D Digital Twin Pipeline
메인 실행 파일
경로: E:\github\plant3D\main.py
"""

import os
import sys
import argparse
import yaml
import logging
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 로거 설정
from loguru import logger


class Plant3DPipeline:
    """Plant3D 파이프라인 메인 클래스"""
    
    def __init__(self, config_path="config.yaml"):
        """초기화"""
        self.config = self.load_config(config_path)
        self.setup_logging()
        self.validate_environment()
        
    def load_config(self, config_path):
        """설정 파일 로드"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"설정 파일 로드 완료: {config_path}")
                return config
        except FileNotFoundError:
            logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logger.error(f"설정 파일 파싱 오류: {e}")
            sys.exit(1)
            
    def setup_logging(self):
        """로깅 설정"""
        log_config = self.config.get('logging', {})
        log_level = log_config.get('level', 'INFO')
        log_file = log_config.get('file', 'logs/plant3d.log')
        
        # 로그 디렉토리 생성
        log_dir = Path(log_file).parent
        log_dir.mkdir(exist_ok=True, parents=True)
        
        # loguru 설정
        logger.remove()  # 기본 핸들러 제거
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        logger.add(
            log_file,
            level=log_level,
            rotation="10 MB",
            retention="7 days",
            compression="zip"
        )
        
    def validate_environment(self):
        """환경 검증"""
        logger.info("환경 검증 시작...")
        
        # FreeCAD 확인
        freecad_path = self.config['programs']['freecad']['windows']
        if not Path(freecad_path).exists():
            logger.warning(f"FreeCAD를 찾을 수 없습니다: {freecad_path}")
            logger.warning("3D 모델링 기능이 제한될 수 있습니다.")
        else:
            logger.info(f"FreeCAD 확인: {freecad_path}")
            
        # Unity 확인
        unity_path = self.config['programs']['unity']['windows']
        if not Path(unity_path).exists():
            logger.warning(f"Unity를 찾을 수 없습니다: {unity_path}")
            logger.warning("시뮬레이션 기능이 제한될 수 있습니다.")
        else:
            logger.info(f"Unity 확인: {unity_path}")
            
        # 필수 폴더 확인
        required_folders = [
            'data/input',
            'data/extracted',
            'data/templates',
            'output/models',
            'output/reports'
        ]
        
        for folder in required_folders:
            folder_path = Path(folder)
            if not folder_path.exists():
                logger.warning(f"폴더가 없습니다: {folder}")
                logger.info("setup_folders.py를 실행하여 폴더 구조를 생성하세요.")
                
        logger.info("환경 검증 완료")
        
    def process_pdf(self, pdf_path):
        """PDF 처리 파이프라인"""
        logger.info(f"PDF 처리 시작: {pdf_path}")
        
        # 파일 존재 확인
        if not Path(pdf_path).exists():
            logger.error(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
            return False
            
        try:
            # 1단계: PDF 데이터 추출
            logger.info("1단계: PDF 데이터 추출")
            # TODO: extractor 모듈 호출
            
            # 2단계: 3D 모델 생성
            logger.info("2단계: 3D 모델 생성")
            # TODO: modeler 모듈 호출
            
            # 3단계: Unity 처리
            logger.info("3단계: Unity 시뮬레이션")
            # TODO: simulator 모듈 호출
            
            logger.success("PDF 처리 완료!")
            return True
            
        except Exception as e:
            logger.error(f"처리 중 오류 발생: {e}")
            return False
            
    def start_server(self):
        """웹 서버 시작"""
        logger.info("웹 서버 시작...")
        
        try:
            # TODO: webserver 모듈 호출
            host = self.config['webserver']['host']
            port = self.config['webserver']['port']
            logger.info(f"서버 주소: http://{host}:{port}")
            
            # 임시 메시지
            logger.warning("웹 서버 모듈이 아직 구현되지 않았습니다.")
            
        except Exception as e:
            logger.error(f"서버 시작 실패: {e}")
            
    def show_status(self):
        """시스템 상태 표시"""
        logger.info("=== Plant3D 시스템 상태 ===")
        
        # 환경 정보
        logger.info(f"프로젝트 경로: {project_root}")
        logger.info(f"Python 버전: {sys.version.split()[0]}")
        
        # 모듈 상태
        modules = {
            'PDF Extractor': False,  # TODO: 실제 상태 확인
            '3D Modeler': False,
            'Unity Simulator': False,
            'Web Server': False
        }
        
        for module, status in modules.items():
            status_text = "✓ 준비됨" if status else "✗ 미구현"
            logger.info(f"{module}: {status_text}")
            
        # 처리 통계
        logger.info("\n=== 처리 통계 ===")
        # TODO: 실제 통계 구현
        logger.info("총 처리 PDF: 0")
        logger.info("생성된 모델: 0")
        

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="Plant3D - PDF to 3D Digital Twin Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  python main.py process --pdf data/input/cyclone.pdf
  python main.py server
  python main.py status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='실행할 명령')
    
    # process 명령
    process_parser = subparsers.add_parser('process', help='PDF 파일 처리')
    process_parser.add_argument('--pdf', required=True, help='처리할 PDF 파일 경로')
    process_parser.add_argument('--output', help='출력 폴더 (기본: output/models)')
    
    # server 명령
    server_parser = subparsers.add_parser('server', help='웹 서버 시작')
    server_parser.add_argument('--port', type=int, help='포트 번호 (기본: 8080)')
    
    # status 명령
    status_parser = subparsers.add_parser('status', help='시스템 상태 확인')
    
    args = parser.parse_args()
    
    # Pipeline 초기화
    pipeline = Plant3DPipeline()
    
    # 명령 실행
    if args.command == 'process':
        pipeline.process_pdf(args.pdf)
    elif args.command == 'server':
        pipeline.start_server()
    elif args.command == 'status':
        pipeline.show_status()
    else:
        parser.print_help()
        

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n프로그램이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.exception(f"예상치 못한 오류: {e}")
#!/usr/bin/env python3
"""
FLUX.1 이미지 생성기
기존 PDF 분석을 보완하는 참조 이미지 생성

경로: E:\github\plant3D\src\extractor\flux_image_generator.py
"""

import os
import json
import requests
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경변수 로딩 (선택적)
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("환경변수 로드 완료")
except ImportError:
    logger.warning("python-dotenv가 설치되지 않았습니다.")


@dataclass
class GeneratedImage:
    """생성된 이미지 정보"""
    prompt: str
    image_path: str
    confidence_score: float
    generation_time: float
    model_used: str
    metadata: Dict


class FluxImageGenerator:
    """FLUX.1 기반 사이클론 참조 이미지 생성기"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('REPLICATE_API_TOKEN')
        if not self.api_key:
            logger.warning("REPLICATE_API_TOKEN이 설정되지 않았습니다.")
        
        # 출력 디렉토리 설정
        self.output_dir = Path("data/generated_images")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FLUX 이미지 생성기 초기화 완료: {self.output_dir}")
    
    def test_connection(self) -> bool:
        """API 연결 테스트"""
        if not self.api_key:
            logger.error("API 키가 없습니다.")
            return False
        
        try:
            url = "https://api.replicate.com/v1/predictions"
            headers = {"Authorization": f"Token {self.api_key}"}
            
            # 간단한 GET 요청으로 API 접근 테스트
            response = requests.get("https://api.replicate.com/v1/models", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ API 연결 성공")
                return True
            else:
                logger.error(f"❌ API 연결 실패: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ API 테스트 실패: {e}")
            return False
    
    def generate_simple_test(self) -> bool:
        """간단한 테스트 이미지 생성"""
        if not self.api_key:
            logger.error("API 키가 필요합니다.")
            return False
        
        try:
            logger.info("🎨 테스트 이미지 생성 시작...")
            
            # 간단한 프롬프트
            prompt = "industrial cyclone separator, technical drawing, white background"
            
            # 이미지 생성 시도
            image_data = self._generate_single_image(prompt)
            
            if image_data:
                # 테스트 이미지 저장
                test_path = self.output_dir / "test_cyclone.png"
                with open(test_path, 'wb') as f:
                    f.write(image_data)
                
                logger.info(f"✅ 테스트 이미지 저장: {test_path}")
                return True
            else:
                logger.error("❌ 이미지 생성 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 테스트 실패: {e}")
            return False
    
    def _generate_single_image(self, prompt: str) -> Optional[bytes]:
        """단일 이미지 생성"""
        try:
            url = "https://api.replicate.com/v1/predictions"
            
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 무료 및 저렴한 모델들 우선 시도
            models_to_try = [
                "stability-ai/sdxl-turbo",  # 무료 모델
                "bytedance/sdxl-lightning-4step",  # 빠른 모델
                "lucataco/sdxl-niji",  # 대체 모델
                "black-forest-labs/flux-schnell"  # 마지막에 시도
            ]
            
            for model in models_to_try:
                logger.info(f"모델 시도: {model}")
                
                # 모델에 따른 다른 파라미터
                if "flux" in model:
                    data = {
                        "version": model,
                        "input": {
                            "prompt": prompt,
                            "num_outputs": 1,
                            "aspect_ratio": "1:1",
                            "output_format": "png"
                        }
                    }
                else:  # stable-diffusion
                    data = {
                        "version": model,
                        "input": {
                            "prompt": prompt,
                            "width": 1024,
                            "height": 1024,
                            "num_outputs": 1
                        }
                    }
                
                logger.info(f"요청 데이터: {data}")
                
                # 예측 요청
                response = requests.post(url, headers=headers, json=data, timeout=30)
                
                logger.info(f"응답 상태: {response.status_code}")
                
                if response.status_code in [200, 201]:  # 200과 201 모두 성공
                    # 성공! 계속 진행
                    break
                else:
                    logger.warning(f"모델 {model} 실패: {response.status_code}")
                    logger.warning(f"응답: {response.text}")
                    if model == models_to_try[-1]:  # 마지막 모델도 실패
                        logger.error("모든 모델 시도 실패")
                        return None
                    continue
            
            prediction = response.json()
            prediction_id = prediction["id"]
            logger.info(f"예측 ID: {prediction_id}")
            
            # 결과 대기
            max_wait = 60
            wait_time = 0
            
            while wait_time < max_wait:
                status_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
                status_response = requests.get(status_url, headers=headers, timeout=30)
                status_data = status_response.json()
                
                status = status_data.get("status")
                logger.info(f"상태: {status}")
                
                if status == "succeeded":
                    output = status_data.get("output")
                    if output:
                        # 출력 형식에 따라 처리
                        if isinstance(output, list) and len(output) > 0:
                            image_url = output[0]
                        elif isinstance(output, str):
                            image_url = output
                        else:
                            logger.error(f"예상치 못한 출력 형식: {output}")
                            return None
                        
                        # 이미지 다운로드
                        img_response = requests.get(image_url, timeout=30)
                        img_response.raise_for_status()
                        logger.info(f"이미지 다운로드 성공: {len(img_response.content)} bytes")
                        return img_response.content
                    else:
                        logger.error("출력 이미지가 없습니다.")
                        return None
                
                elif status == "failed":
                    error = status_data.get('error', 'Unknown error')
                    logger.error(f"이미지 생성 실패: {error}")
                    return None
                
                # 대기
                time.sleep(3)
                wait_time += 3
            
            logger.error("이미지 생성 시간 초과")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"네트워크 오류: {e}")
            return None
        except Exception as e:
            logger.error(f"API 호출 실패: {e}")
            return None


def test_flux_basic():
    """기본 테스트 함수"""
    print("🚀 FLUX.1 기본 테스트 시작")
    print("=" * 40)
    
    # API 키 확인
    api_key = os.getenv('REPLICATE_API_TOKEN')
    if not api_key:
        print("❌ REPLICATE_API_TOKEN 환경변수가 설정되지 않았습니다.")
        print("1. https://replicate.com에서 API 키 발급")
        print("2. 환경변수 설정: set REPLICATE_API_TOKEN=your_key")
        return False
    
    # 생성기 초기화
    generator = FluxImageGenerator(api_key)
    
    # 연결 테스트
    if not generator.test_connection():
        print("❌ API 연결 실패")
        return False
    
    # 이미지 생성 테스트
    if generator.generate_simple_test():
        print("✅ FLUX.1 테스트 성공!")
        return True
    else:
        print("❌ 이미지 생성 실패")
        return False


if __name__ == "__main__":
    test_flux_basic()
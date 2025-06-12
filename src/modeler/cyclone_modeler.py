#!/usr/bin/env python3
"""
사이클론 3D 모델 생성기 (수정된 버전)
경로: E:\github\plant3D\src\modeler\cyclone_modeler.py

추출된 JSON 데이터를 기반으로 3D 모델 생성
"""

import json
import numpy as np
from pathlib import Path
import trimesh
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import os

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CycloneGeometry:
    """사이클론 기하학적 파라미터"""
    # 메인 바디 치수
    cylinder_diameter: float  # mm
    cylinder_height: float  # mm
    cone_height: float  # mm
    cone_outlet_diameter: float  # mm
    
    # 입구 치수
    inlet_width: float  # mm
    inlet_height: float  # mm
    inlet_length: float  # mm (접선 방향)
    
    # 출구 치수
    gas_outlet_diameter: float  # mm (상부)
    gas_outlet_height: float  # mm (vortex finder)
    solids_outlet_diameter: float  # mm (하부)
    
    # 벽 두께
    wall_thickness: float = 10.0  # mm
    
    # 노즐 정보
    nozzles: List[Dict] = None
    
    def __post_init__(self):
        """초기화 후 검증"""
        if self.nozzles is None:
            self.nozzles = []
        self._validate()
    
    def _validate(self):
        """치수 검증"""
        if self.cylinder_diameter <= 0:
            raise ValueError("실린더 직경은 0보다 커야 합니다")
        if self.cone_outlet_diameter >= self.cylinder_diameter:
            raise ValueError("콘 출구 직경은 실린더 직경보다 작아야 합니다")


class CycloneModeler:
    """사이클론 3D 모델 생성 클래스"""
    
    def __init__(self, json_path: str):
        """
        Args:
            json_path: 추출된 데이터 JSON 파일 경로
        """
        self.json_path = Path(json_path)
        self.data = self._load_data()
        self.geometry = self._calculate_geometry()
        self.mesh = None
        
    def _load_data(self) -> Dict:
        """JSON 데이터 로드 (향상된 오류 처리)"""
        # 기본 데이터 구조
        default_data = {
            'tag_number': 'MF-PE-CYCLONE-001',
            'service': 'PE Cyclone Separator',
            'dimensions': {
                'inlet_height_mm': 279.0,
                'inlet_width_mm': 140.0
            },
            'nozzles': [],
            'efficiency': 'N/A',
            'pressure_drop': 'N/A'
        }
        
        # 파일 존재 확인
        if not self.json_path.exists():
            logger.warning(f"JSON 파일을 찾을 수 없습니다: {self.json_path}")
            logger.info("기본값으로 3D 모델을 생성합니다.")
            return default_data
        
        # 파일 크기 확인
        file_size = self.json_path.stat().st_size
        if file_size == 0:
            logger.warning(f"JSON 파일이 비어있습니다: {self.json_path}")
            logger.info("기본값으로 3D 모델을 생성합니다.")
            return default_data
        
        logger.info(f"JSON 파일 크기: {file_size} bytes")
        
        # JSON 로드 시도
        try:
            # 여러 인코딩으로 시도
            encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin1']
            
            for encoding in encodings:
                try:
                    with open(self.json_path, 'r', encoding=encoding) as f:
                        content = f.read().strip()
                    
                    if not content:
                        logger.warning("파일 내용이 비어있습니다.")
                        break
                    
                    # JSON 파싱
                    data = json.loads(content)
                    logger.info(f"JSON 파일 로드 성공 ({encoding} 인코딩): {self.json_path.name}")
                    
                    # 데이터 타입 확인
                    if not isinstance(data, dict):
                        logger.warning(f"JSON 루트가 딕셔너리가 아님: {type(data)}. 기본값 사용.")
                        return default_data
                    
                    # 필수 키 보완
                    for key, default_value in default_data.items():
                        if key not in data:
                            logger.info(f"키 '{key}' 추가: {default_value}")
                            data[key] = default_value
                    
                    logger.info(f"로드된 데이터 키: {list(data.keys())}")
                    return data
                    
                except UnicodeDecodeError:
                    continue
                except json.JSONDecodeError as e:
                    if encoding == encodings[-1]:  # 마지막 인코딩
                        logger.error(f"JSON 파싱 오류: {e}")
                        logger.error(f"오류 위치: line {e.lineno}, column {e.colno}")
                        break
                    continue
            
            # 모든 시도 실패
            logger.warning("JSON 파일 로드 실패. 기본값 사용.")
            return default_data
            
        except Exception as e:
            logger.error(f"JSON 로드 중 예외 발생: {e}")
            logger.info("기본값으로 3D 모델을 생성합니다.")
            return default_data
        
    def _calculate_geometry(self) -> CycloneGeometry:
        """추출된 데이터에서 기하학적 파라미터 계산"""
        # 기본값 설정 (일반적인 사이클론 비율 사용)
        # Fisher-Klosterman Size 11 기준
        base_diameter = 279.0  # mm (11 inches)
        
        # 입구 크기 (PDF에서 추출된 값 사용)
        inlet_height = 279.0  # mm
        inlet_width = 140.0  # mm
        
        # 치수 정보가 있으면 사용
        try:
            if self.data.get('dimensions'):
                dims = self.data['dimensions']
                if 'inlet_height_mm' in dims:
                    inlet_height = float(dims['inlet_height_mm'])
                    logger.info(f"입구 높이 사용: {inlet_height} mm")
                if 'inlet_width_mm' in dims:
                    inlet_width = float(dims['inlet_width_mm'])
                    logger.info(f"입구 너비 사용: {inlet_width} mm")
        except (ValueError, TypeError) as e:
            logger.warning(f"치수 정보 파싱 오류: {e}. 기본값 사용.")
        
        # 표준 사이클론 비율 적용
        # Stairmand 고효율 사이클론 비율 참조
        cylinder_diameter = base_diameter
        cylinder_height = cylinder_diameter * 1.5  # D * 1.5
        cone_height = cylinder_diameter * 2.5  # D * 2.5
        cone_outlet_diameter = cylinder_diameter * 0.375  # D * 0.375
        
        # 가스 출구 (vortex finder)
        gas_outlet_diameter = cylinder_diameter * 0.5  # D * 0.5
        gas_outlet_height = cylinder_diameter * 0.5  # D * 0.5
        
        # 고체 출구
        solids_outlet_diameter = cone_outlet_diameter
        
        # 입구 길이 (접선 방향)
        inlet_length = cylinder_diameter * 0.5
        
        # 노즐 정보 변환
        nozzles = []
        try:
            if self.data.get('nozzles') and isinstance(self.data['nozzles'], list):
                for nozzle in self.data['nozzles']:
                    if isinstance(nozzle, dict):
                        # 인치를 mm로 변환
                        size_str = nozzle.get('size', '0"')
                        try:
                            size_inch = float(size_str.replace('"', '').replace('inch', '').strip())
                            size_mm = size_inch * 25.4
                        except ValueError:
                            size_mm = 50.0  # 기본값
                        
                        nozzles.append({
                            'tag': nozzle.get('tag', ''),
                            'service': nozzle.get('service', ''),
                            'diameter': size_mm,
                            'rating': nozzle.get('rating', ''),
                            'type': self._get_nozzle_type(nozzle.get('service', ''))
                        })
        except Exception as e:
            logger.warning(f"노즐 정보 처리 오류: {e}")
        
        geometry = CycloneGeometry(
            cylinder_diameter=cylinder_diameter,
            cylinder_height=cylinder_height,
            cone_height=cone_height,
            cone_outlet_diameter=cone_outlet_diameter,
            inlet_width=inlet_width,
            inlet_height=inlet_height,
            inlet_length=inlet_length,
            gas_outlet_diameter=gas_outlet_diameter,
            gas_outlet_height=gas_outlet_height,
            solids_outlet_diameter=solids_outlet_diameter,
            nozzles=nozzles
        )
        
        logger.info(f"기하학적 파라미터 계산 완료")
        logger.info(f"  - 실린더 직경: {cylinder_diameter:.1f} mm")
        logger.info(f"  - 전체 높이: {cylinder_height + cone_height:.1f} mm")
        logger.info(f"  - 입구 크기: {inlet_width:.1f} x {inlet_height:.1f} mm")
        
        return geometry
        
    def _get_nozzle_type(self, service: str) -> str:
        """노즐 서비스명에서 타입 결정"""
        service_lower = service.lower()
        if 'inlet' in service_lower:
            return 'inlet'
        elif 'outlet' in service_lower and 'gas' in service_lower:
            return 'gas_outlet'
        elif 'outlet' in service_lower and 'solid' in service_lower:
            return 'solids_outlet'
        else:
            return 'other'
            
    def create_3d_model(self) -> trimesh.Trimesh:
        """3D 모델 생성"""
        logger.info("3D 모델 생성 시작...")
        
        try:
            # 각 부품 생성
            cylinder = self._create_cylinder()
            cone = self._create_cone()
            inlet = self._create_inlet()
            gas_outlet = self._create_gas_outlet()
            solids_outlet = self._create_solids_outlet()
            
            # 부품 결합
            mesh = trimesh.util.concatenate([
                cylinder,
                cone,
                inlet,
                gas_outlet,
                solids_outlet
            ])
            
            # 메시 정리
            mesh.remove_duplicate_faces()
            mesh.remove_degenerate_faces()
            mesh.fix_normals()
            
            self.mesh = mesh
            logger.info(f"3D 모델 생성 완료 - 정점: {len(mesh.vertices)}, 면: {len(mesh.faces)}")
            
            return mesh
            
        except Exception as e:
            logger.error(f"3D 모델 생성 중 오류: {e}")
            raise
        
    def _create_cylinder(self) -> trimesh.Trimesh:
        """실린더 부분 생성"""
        try:
            # 외부 실린더
            outer_cylinder = trimesh.creation.cylinder(
                radius=self.geometry.cylinder_diameter / 2,
                height=self.geometry.cylinder_height,
                sections=64
            )
            
            # 내부 실린더 (중공)
            inner_cylinder = trimesh.creation.cylinder(
                radius=(self.geometry.cylinder_diameter / 2) - self.geometry.wall_thickness,
                height=self.geometry.cylinder_height + 1,  # 약간 더 길게
                sections=64
            )
            
            # 불리언 차집합으로 중공 실린더 생성
            cylinder = outer_cylinder.difference(inner_cylinder)
            
            # 위치 조정 (원점이 바닥 중심)
            cylinder.apply_translation([0, 0, self.geometry.cylinder_height / 2])
            
            return cylinder
            
        except Exception as e:
            logger.error(f"실린더 생성 오류: {e}")
            # 간단한 실린더로 대체
            return trimesh.creation.cylinder(
                radius=self.geometry.cylinder_diameter / 2,
                height=self.geometry.cylinder_height,
                sections=32
            )
        
    def _create_cone(self) -> trimesh.Trimesh:
        """원뿔 부분 생성"""
        try:
            # 절두원뿔 생성 (truncated cone)
            cone = trimesh.creation.cone(
                radius=self.geometry.cylinder_diameter / 2,
                height=self.geometry.cone_height,
                sections=64
            )
            
            # 원뿔을 뒤집고 위치 조정
            cone.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
            cone.apply_translation([0, 0, -self.geometry.cone_height / 2])
            
            return cone
            
        except Exception as e:
            logger.error(f"원뿔 생성 오류: {e}")
            # 간단한 원뿔로 대체
            return trimesh.creation.cone(
                radius=self.geometry.cylinder_diameter / 2,
                height=self.geometry.cone_height,
                sections=32
            )
        
    def _create_inlet(self) -> trimesh.Trimesh:
        """접선 입구 생성"""
        try:
            # 사각형 덕트
            inlet_box = trimesh.creation.box(extents=[
                self.geometry.inlet_length,
                self.geometry.inlet_width,
                self.geometry.inlet_height
            ])
            
            # 실린더 벽과 연결되는 위치로 이동
            x_offset = (self.geometry.cylinder_diameter / 2) + (self.geometry.inlet_length / 2) - (self.geometry.wall_thickness / 2)
            z_offset = self.geometry.cylinder_height - (self.geometry.inlet_height / 2) - 50  # 상단에서 50mm 아래
            
            inlet_box.apply_translation([x_offset, 0, z_offset])
            
            return inlet_box
            
        except Exception as e:
            logger.error(f"입구 생성 오류: {e}")
            # 간단한 박스로 대체
            return trimesh.creation.box(extents=[100, 50, 100])
        
    def _create_gas_outlet(self) -> trimesh.Trimesh:
        """가스 출구 (vortex finder) 생성"""
        try:
            # 파이프
            pipe = trimesh.creation.cylinder(
                radius=self.geometry.gas_outlet_diameter / 2,
                height=self.geometry.gas_outlet_height + 100,  # 위로 연장
                sections=32
            )
            
            # 위치 조정 (실린더 상단)
            z_offset = self.geometry.cylinder_height + 50
            pipe.apply_translation([0, 0, z_offset])
            
            return pipe
            
        except Exception as e:
            logger.error(f"가스 출구 생성 오류: {e}")
            # 간단한 실린더로 대체
            return trimesh.creation.cylinder(
                radius=50,
                height=100,
                sections=16
            )
        
    def _create_solids_outlet(self) -> trimesh.Trimesh:
        """고체 출구 생성"""
        try:
            # 파이프
            pipe = trimesh.creation.cylinder(
                radius=self.geometry.solids_outlet_diameter / 2,
                height=200,  # 아래로 연장
                sections=32
            )
            
            # 위치 조정 (원뿔 하단)
            z_offset = -self.geometry.cone_height - 100
            pipe.apply_translation([0, 0, z_offset])
            
            return pipe
            
        except Exception as e:
            logger.error(f"고체 출구 생성 오류: {e}")
            # 간단한 실린더로 대체
            return trimesh.creation.cylinder(
                radius=40,
                height=100,
                sections=16
            )
        
    def save_model(self, output_dir: str = "output/models", formats: List[str] = None):
        """3D 모델을 파일로 저장"""
        if self.mesh is None:
            raise ValueError("먼저 create_3d_model()을 실행하세요")
            
        if formats is None:
            formats = ['stl', 'obj']  # 문제가 적은 형식들만
            
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tag_number = self.data.get('tag_number', 'unknown').replace('-', '_').replace(' ', '_')
        base_filename = f"cyclone_{tag_number}_{timestamp}"
        
        saved_files = []
        
        for fmt in formats:
            try:
                file_path = output_path / f"{base_filename}.{fmt}"
                self.mesh.export(file_path)
                saved_files.append(str(file_path))
                logger.info(f"{fmt.upper()} 파일 저장: {file_path}")
                
            except Exception as e:
                logger.error(f"{fmt} 저장 실패: {e}")
                
        return saved_files
        
    def get_model_info(self) -> Dict:
        """모델 정보 반환"""
        if self.mesh is None:
            raise ValueError("먼저 create_3d_model()을 실행하세요")
            
        info = {
            'tag_number': self.data.get('tag_number', 'N/A'),
            'service': self.data.get('service', 'N/A'),
            'geometry': {
                'cylinder_diameter': self.geometry.cylinder_diameter,
                'total_height': self.geometry.cylinder_height + self.geometry.cone_height,
                'inlet_size': f"{self.geometry.inlet_width} x {self.geometry.inlet_height} mm",
                'nozzle_count': len(self.geometry.nozzles)
            },
            'mesh': {
                'vertices': len(self.mesh.vertices),
                'faces': len(self.mesh.faces),
                'volume': float(self.mesh.volume) if hasattr(self.mesh, 'volume') else 0,
                'surface_area': float(self.mesh.area) if hasattr(self.mesh, 'area') else 0,
                'bounds': self.mesh.bounds.tolist() if hasattr(self.mesh, 'bounds') else []
            },
            'performance': {
                'efficiency': self.data.get('efficiency', 'N/A'),
                'pressure_drop': self.data.get('pressure_drop', 'N/A')
            }
        }
        
        return info


def create_cyclone_from_json(json_path: str, output_dir: str = "output/models") -> Dict:
    """JSON 파일에서 사이클론 3D 모델 생성 (헬퍼 함수)"""
    try:
        # 모델러 생성
        modeler = CycloneModeler(json_path)
        
        # 3D 모델 생성
        mesh = modeler.create_3d_model()
        
        # 파일 저장
        saved_files = modeler.save_model(output_dir)
        
        # 모델 정보
        info = modeler.get_model_info()
        info['saved_files'] = saved_files
        
        return info
        
    except Exception as e:
        logger.error(f"모델 생성 실패: {e}")
        raise


if __name__ == "__main__":
    # 테스트
    import sys
    
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        # 기본 JSON 파일 경로 (프로젝트 루트에서 실행하는 경우)
        json_file = "src/extractor/data/extracted/MF PE Cyclone_20250609_extracted.json"
        print(f"기본 JSON 파일 사용: {json_file}")
        
    try:
        print(f"JSON 파일: {json_file}")
        
        # 파일 존재 확인
        json_path = Path(json_file)
        if not json_path.exists():
            print(f"❌ JSON 파일을 찾을 수 없습니다: {json_path.absolute()}")
            print("다음 경로들을 확인해주세요:")
            possible_paths = [
                "src/extractor/data/extracted/MF PE Cyclone_20250609_extracted.json",
                "extractor/data/extracted/MF PE Cyclone_20250609_extracted.json", 
                "../extractor/data/extracted/MF PE Cyclone_20250609_extracted.json"
            ]
            for path in possible_paths:
                exists = "✅" if Path(path).exists() else "❌"
                print(f"  {exists} {path}")
            sys.exit(1)
        
        info = create_cyclone_from_json(json_file)
        
        print("\n" + "="*50)
        print("🎯 사이클론 3D 모델 생성 완료")
        print("="*50)
        print(f"📋 태그 번호: {info['tag_number']}")
        print(f"🔧 서비스: {info['service']}")
        print(f"\n📐 기하학적 정보:")
        print(f"  • 실린더 직경: {info['geometry']['cylinder_diameter']:.1f} mm")
        print(f"  • 전체 높이: {info['geometry']['total_height']:.1f} mm")
        print(f"  • 입구 크기: {info['geometry']['inlet_size']}")
        print(f"  • 노즐 개수: {info['geometry']['nozzle_count']}개")
        print(f"\n🔺 메시 정보:")
        print(f"  • 정점 수: {info['mesh']['vertices']:,}")
        print(f"  • 면 수: {info['mesh']['faces']:,}")
        if info['mesh']['volume'] > 0:
            print(f"  • 부피: {info['mesh']['volume']:,.2f} mm³")
        print(f"\n💾 저장된 파일:")
        for file in info['saved_files']:
            print(f"  📄 {file}")
        
        print(f"\n✅ 성공적으로 완료되었습니다!")
            
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        print("\n상세 오류 정보:")
        traceback.print_exc()
        sys.exit(1)
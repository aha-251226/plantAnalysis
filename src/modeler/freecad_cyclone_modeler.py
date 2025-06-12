#!/usr/bin/env python3
"""
FreeCAD 기반 정밀 사이클론 3D 모델러 (수정됨)
각 부품 개별 저장 + Unity 호환
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import logging
from datetime import datetime

# FreeCAD import 시도
try:
    # FreeCAD 1.0 경로 추가
    import sys
    import os
    sys.path.append(r'C:\Program Files\FreeCAD 1.0\bin')
    sys.path.append(r'C:\Program Files\FreeCAD 1.0\Mod')
    
    # 환경변수도 설정
    os.environ['FREECAD_USER_HOME'] = r'C:\Program Files\FreeCAD 1.0'
    
    import FreeCAD
    import Part
    FREECAD_AVAILABLE = True
    print("✅ FreeCAD 1.0 로드 성공!")
    
except ImportError as e:
    print(f"❌ FreeCAD 로드 실패: {e}")
    FREECAD_AVAILABLE = False
except Exception as e:
    print(f"❌ 기타 오류: {e}")
    FREECAD_AVAILABLE = False

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FreeCADCycloneModeler:
    """FreeCAD 기반 정밀 사이클론 모델러"""
    
    def __init__(self, json_data: Dict):
        if not FREECAD_AVAILABLE:
            raise ImportError("FreeCAD가 필요합니다")
            
        self.data = json_data
        self.doc = None
        self.dimensions = self._calculate_precise_dimensions()
        
    def _calculate_precise_dimensions(self) -> Dict:
        """JSON 데이터 기반 정밀 치수 계산"""
        model_size = int(self.data.get('model', '11'))
        base_diameter = model_size * 25.4  # inches to mm
        
        inlet_height = self.data['dimensions']['inlet_height_mm']
        inlet_width = self.data['dimensions']['inlet_width_mm']
        
        cylinder_diameter = base_diameter
        cylinder_height = cylinder_diameter * 1.5
        cone_height = cylinder_diameter * 2.5
        cone_outlet_diameter = cylinder_diameter * 0.375
        
        gas_outlet_diameter = cylinder_diameter * 0.5
        gas_outlet_height = cylinder_diameter * 0.625
        gas_outlet_extension = cylinder_diameter * 0.5
        
        wall_thickness = 12.7  # mm (1/2")
        
        return {
            'cylinder_diameter': cylinder_diameter,
            'cylinder_height': cylinder_height,
            'cone_height': cone_height,
            'cone_outlet_diameter': cone_outlet_diameter,
            'wall_thickness': wall_thickness,
            'inlet_width': inlet_width,
            'inlet_height': inlet_height,
            'inlet_length': cylinder_diameter * 0.4,
            'gas_outlet_diameter': gas_outlet_diameter,
            'gas_outlet_height': gas_outlet_height,
            'gas_outlet_extension': gas_outlet_extension,
            'solids_outlet_diameter': cone_outlet_diameter,
            'total_height': cylinder_height + cone_height
        }
    
    def create_3d_model(self) -> str:
        """3D 모델 생성"""
        logger.info("FreeCAD 정밀 3D 모델 생성 시작...")
        
        doc_name = f"Cyclone_{self.data['tag_number'].replace('-', '_')}"
        self.doc = FreeCAD.newDocument(doc_name)
        
        try:
            # 부품들 생성
            main_body = self._create_main_body()
            inlet_duct = self._create_inlet_duct()
            gas_outlet = self._create_gas_outlet()
            solids_outlet = self._create_solids_outlet()
            
            self.doc.recompute()
            logger.info("FreeCAD 모델 생성 완료")
            return self._save_model()
            
        except Exception as e:
            logger.error(f"모델 생성 실패: {e}")
            raise
    
    def _create_main_body(self):
        """메인 바디 생성"""
        logger.info("메인 바디 생성...")
        
        dim = self.dimensions
        
        # 실린더 부분
        outer_cylinder = Part.makeCylinder(
            dim['cylinder_diameter'] / 2,
            dim['cylinder_height'],
            FreeCAD.Vector(0, 0, 0)
        )
        
        inner_radius = (dim['cylinder_diameter'] / 2) - dim['wall_thickness']
        inner_cylinder = Part.makeCylinder(
            inner_radius,
            dim['cylinder_height'] + 1,
            FreeCAD.Vector(0, 0, -0.5)
        )
        
        cylinder_shell = outer_cylinder.cut(inner_cylinder)
        
        # 원뿔 부분
        cone_top_radius = dim['cylinder_diameter'] / 2
        cone_bottom_radius = dim['cone_outlet_diameter'] / 2
        
        outer_cone = Part.makeCone(
            cone_top_radius,
            cone_bottom_radius,
            dim['cone_height'],
            FreeCAD.Vector(0, 0, -dim['cone_height'])
        )
        
        inner_cone_top = cone_top_radius - dim['wall_thickness']
        inner_cone_bottom = cone_bottom_radius - dim['wall_thickness']
        
        inner_cone = Part.makeCone(
            inner_cone_top,
            inner_cone_bottom,
            dim['cone_height'] + 1,
            FreeCAD.Vector(0, 0, -dim['cone_height'] - 0.5)
        )
        
        cone_shell = outer_cone.cut(inner_cone)
        
        # 결합
        main_body = cylinder_shell.fuse(cone_shell)
        
        body_obj = self.doc.addObject("Part::Feature", "MainBody")
        body_obj.Shape = main_body
        body_obj.Label = "Cyclone_Main_Body"
        
        return body_obj
    
    def _create_inlet_duct(self):
        """입구 덕트 생성"""
        logger.info("입구 덕트 생성...")
        
        dim = self.dimensions
        
        duct_length = dim['inlet_length']
        duct_width = dim['inlet_width']
        duct_height = dim['inlet_height']
        
        outer_box = Part.makeBox(
            duct_length,
            duct_width,
            duct_height,
            FreeCAD.Vector(0, 0, 0)
        )
        
        wall_t = dim['wall_thickness']
        inner_box = Part.makeBox(
            duct_length + 1,
            duct_width - 2 * wall_t,
            duct_height - 2 * wall_t,
            FreeCAD.Vector(-0.5, wall_t, wall_t)
        )
        
        duct = outer_box.cut(inner_box)
        
        cylinder_radius = dim['cylinder_diameter'] / 2
        x_offset = cylinder_radius - wall_t
        z_offset = dim['cylinder_height'] - duct_height - 50
        
        duct.translate(FreeCAD.Vector(x_offset, -duct_width/2, z_offset))
        
        inlet_obj = self.doc.addObject("Part::Feature", "InletDuct")
        inlet_obj.Shape = duct
        inlet_obj.Label = "Inlet_Duct"
        
        return inlet_obj
    
    def _create_gas_outlet(self):
        """가스 출구 생성"""
        logger.info("가스 출구 생성...")
        
        dim = self.dimensions
        
        outer_radius = dim['gas_outlet_diameter'] / 2
        inner_radius = outer_radius - dim['wall_thickness']
        total_height = dim['gas_outlet_height'] + dim['gas_outlet_extension']
        
        outer_pipe = Part.makeCylinder(
            outer_radius,
            total_height,
            FreeCAD.Vector(0, 0, -dim['gas_outlet_height'])
        )
        
        inner_pipe = Part.makeCylinder(
            inner_radius,
            total_height + 1,
            FreeCAD.Vector(0, 0, -dim['gas_outlet_height'] - 0.5)
        )
        
        vortex_finder = outer_pipe.cut(inner_pipe)
        
        gas_outlet_obj = self.doc.addObject("Part::Feature", "GasOutlet")
        gas_outlet_obj.Shape = vortex_finder
        gas_outlet_obj.Label = "Gas_Outlet"
        
        return gas_outlet_obj
    
    def _create_solids_outlet(self):
        """고체 출구 생성"""
        logger.info("고체 출구 생성...")
        
        dim = self.dimensions
        
        outer_radius = dim['solids_outlet_diameter'] / 2
        inner_radius = outer_radius - dim['wall_thickness']
        pipe_height = 200
        
        outer_pipe = Part.makeCylinder(
            outer_radius,
            pipe_height,
            FreeCAD.Vector(0, 0, -dim['cone_height'] - pipe_height)
        )
        
        inner_pipe = Part.makeCylinder(
            inner_radius,
            pipe_height + 1,
            FreeCAD.Vector(0, 0, -dim['cone_height'] - pipe_height - 0.5)
        )
        
        solids_pipe = outer_pipe.cut(inner_pipe)
        
        solids_outlet_obj = self.doc.addObject("Part::Feature", "SolidsOutlet")
        solids_outlet_obj.Shape = solids_pipe
        solids_outlet_obj.Label = "Solids_Outlet"
        
        return solids_outlet_obj
    
    def _save_model(self) -> str:
        """모델 저장 (개별 부품 + 조립체)"""
        output_dir = Path("output/freecad_models")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        tag = self.data['tag_number'].replace('-', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # FreeCAD 파일 저장
        fcstd_path = output_dir / f"cyclone_{tag}_{timestamp}.FCStd"
        self.doc.saveAs(str(fcstd_path))
        
        # Unity용 개별 부품 저장
        unity_dir = output_dir / f"cyclone_{tag}_{timestamp}_parts"
        unity_dir.mkdir(exist_ok=True)
        
        saved_parts = []
        for obj in self.doc.Objects:
            if hasattr(obj, 'Shape') and obj.Shape:
                part_name = obj.Label.replace(' ', '_').replace('(', '').replace(')', '')
                
                obj_path = unity_dir / f"{part_name}.obj"
                try:
                    import Mesh
                    mesh = self.doc.addObject("Mesh::Feature", f"Mesh_{part_name}")
                    mesh.Mesh = Mesh.Mesh(obj.Shape.tessellate(0.1))
                    mesh.Mesh.write(str(obj_path))
                    self.doc.removeObject(mesh.Name)
                    
                    saved_parts.append(part_name)
                    logger.info(f"부품 저장: {obj_path}")
                except Exception as e:
                    logger.warning(f"부품 {part_name} 저장 실패: {e}")
        
        # 전체 조립체 저장
        assembly_path = unity_dir / f"cyclone_{tag}_assembly.obj"
        try:
            shapes = [obj.Shape for obj in self.doc.Objects if hasattr(obj, 'Shape')]
            if shapes:
                compound = Part.makeCompound(shapes)
                import Mesh
                assembly_mesh = self.doc.addObject("Mesh::Feature", "AssemblyMesh")
                assembly_mesh.Mesh = Mesh.Mesh(compound.tessellate(0.1))
                assembly_mesh.Mesh.write(str(assembly_path))
                self.doc.removeObject(assembly_mesh.Name)
                logger.info(f"조립체 저장: {assembly_path}")
        except Exception as e:
            logger.warning(f"조립체 저장 실패: {e}")
        
        logger.info(f"Unity용 부품들: {unity_dir}")
        logger.info(f"개별 부품: {len(saved_parts)}개")
        
        return str(fcstd_path)
    
    def get_model_info(self) -> Dict:
        """모델 정보 반환"""
        dim = self.dimensions
        
        return {
            'tag_number': self.data['tag_number'],
            'model': f"Fisher-Klosterman Size {self.data['model']}",
            'dimensions': {
                'cylinder_diameter': f"{dim['cylinder_diameter']:.1f} mm",
                'total_height': f"{dim['total_height']:.1f} mm",
                'inlet_size': f"{dim['inlet_width']:.0f} x {dim['inlet_height']:.0f} mm",
                'wall_thickness': f"{dim['wall_thickness']:.1f} mm"
            }
        }


def create_freecad_cyclone_model(json_path: str) -> Dict:
    """FreeCAD 사이클론 모델 생성"""
    if not FREECAD_AVAILABLE:
        raise ImportError("FreeCAD가 설치되지 않았습니다")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    modeler = FreeCADCycloneModeler(json_data)
    model_path = modeler.create_3d_model()
    
    info = modeler.get_model_info()
    info['model_path'] = model_path
    
    return info


if __name__ == "__main__":
    import sys
    
    if not FREECAD_AVAILABLE:
        print("❌ FreeCAD가 설치되지 않았습니다.")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        json_file = "../extractor/data/extracted/MF PE Cyclone_20250609_extracted.json"
    
    try:
        print("🔧 FreeCAD 정밀 사이클론 3D 모델 생성")
        print("=" * 50)
        
        info = create_freecad_cyclone_model(json_file)
        
        print("✅ 모델 생성 완료!")
        print(f"📋 태그: {info['tag_number']}")
        print(f"🏭 모델: {info['model']}")
        print(f"💾 저장 위치: {info['model_path']}")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
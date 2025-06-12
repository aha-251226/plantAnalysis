#!/usr/bin/env python3
"""
FreeCAD to Unity 자동 연동 시스템
경로: E:/github/plant3D/src/modeler/unity_integration.py

FreeCAD에서 생성된 3D 모델을 Unity로 자동 import 및 배치
"""

import os
import shutil
import json
import subprocess
from pathlib import Path
from typing import Dict, List
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnityIntegration:
    """Unity 자동 연동 클래스"""
    
    def __init__(self):
        # 프로젝트 경로 설정
        self.project_root = Path(__file__).parent.parent.parent
        self.unity_project_path = self.project_root / "UnityProject" / "Plant3DViewer"
        self.unity_assets_path = self.unity_project_path / "Assets"
        
        # Unity 폴더 구조 생성
        self.models_folder = self.unity_assets_path / "Models" / "Cyclones"
        self.scripts_folder = self.unity_assets_path / "Scripts"
        self.scenes_folder = self.unity_assets_path / "Scenes"
        
        self._ensure_unity_folders()
        
    def _ensure_unity_folders(self):
        """Unity 프로젝트 폴더 구조 생성"""
        folders = [
            self.models_folder,
            self.scripts_folder,
            self.scenes_folder,
            self.unity_assets_path / "Materials",
            self.unity_assets_path / "Prefabs" / "Cyclones"
        ]
        
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Unity 폴더 생성: {folder}")
    
    def import_cyclone_model(self, model_path: str, model_info: Dict) -> str:
        """FreeCAD 모델을 Unity로 import"""
        logger.info("Unity로 모델 import 시작...")
        
        model_path = Path(model_path)
        
        # 폴더인지 파일인지 확인
        if model_path.is_dir():
            # 폴더인 경우: 모든 OBJ 파일을 복사
            obj_files = list(model_path.glob("*.obj"))
            if not obj_files:
                raise FileNotFoundError(f"OBJ 파일을 찾을 수 없습니다: {model_path}")
            
            copied_files = []
            for obj_file in obj_files:
                unity_filename = obj_file.name
                unity_model_path = self.models_folder / unity_filename
                
                # 파일 복사
                shutil.copy2(obj_file, unity_model_path)
                copied_files.append(str(unity_model_path))
                logger.info(f"모델 복사 완료: {unity_model_path}")
                
                # Unity Asset Database 갱신을 위한 메타 파일 생성
                self._create_meta_file(unity_model_path, model_info)
            
            logger.info(f"총 {len(copied_files)}개 OBJ 파일 복사 완료")
            return str(self.models_folder)
            
        else:
            # 단일 파일인 경우
            if not model_path.exists():
                raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {model_path}")
            
            tag = model_info['tag_number'].replace('-', '_')
            unity_filename = f"Cyclone_{tag}{model_path.suffix}"
            unity_model_path = self.models_folder / unity_filename
            
            # 모델 파일 복사
            shutil.copy2(model_path, unity_model_path)
            logger.info(f"모델 복사 완료: {unity_model_path}")
            
            # Unity Asset Database 갱신을 위한 메타 파일 생성
            self._create_meta_file(unity_model_path, model_info)
            
            return str(unity_model_path)
    
    def _create_meta_file(self, model_path: Path, model_info: Dict):
        """Unity .meta 파일 생성 (import 설정)"""
        meta_content = f"""fileFormatVersion: 2
guid: {self._generate_unity_guid()}
ModelImporter:
  serializedVersion: 21300
  internalIDToNameTable: []
  externalObjects: {{}}
  materials:
    materialImportMode: 1
    materialName: 0
    materialSearch: 1
    materialLocation: 1
  animations:
    legacyGenerateAnimations: 4
    bakeSimulation: 0
    resampleCurves: 1
    optimizeGameObjects: 0
    motionNodeName: 
    rigImportErrors: 
    rigImportWarnings: 
    animationImportErrors: 
    animationImportWarnings: 
    animationRetargetingWarnings: 
    animationDoRetargetingWarnings: 0
    importAnimatedCustomProperties: 0
    importConstraints: 0
    animationCompression: 1
    animationRotationError: 0.5
    animationPositionError: 0.5
    animationScaleError: 0.5
    animationWrapMode: 0
    extraExposedTransformPaths: []
    extraUserProperties: []
    clipAnimations: []
    isReadable: 0
  meshes:
    lODScreenPercentages: []
    globalScale: 0.001
    meshCompression: 0
    addColliders: 1
    useSRGBMaterialColor: 1
    sortHierarchyByName: 1
    importVisibility: 1
    importBlendShapes: 1
    importCameras: 1
    importLights: 1
    nodeNameCollisionStrategy: 1
    fileIdsGeneration: 2
    swapUVChannels: 0
    generateSecondaryUV: 0
    useFileUnits: 1
    keepQuads: 0
    weldVertices: 1
    bakeAxisConversion: 0
    preserveHierarchy: 0
    skinWeightsMode: 0
    maxBonesPerVertex: 4
    minBoneWeight: 0.001
    optimizeBones: 1
    meshOptimizationFlags: -1
    indexFormat: 0
    secondaryUVAngleDistortion: 8
    secondaryUVAreaDistortion: 15.000001
    secondaryUVHardAngle: 88
    secondaryUVMarginMethod: 1
    secondaryUVMinLightmapResolution: 40
    secondaryUVMinObjectScale: 1
    secondaryUVPackMargin: 4
    useFileScale: 1
  tangentSpace:
    normalSmoothAngle: 60
    normalImportMode: 0
    tangentImportMode: 3
    normalCalculationMode: 4
    legacyComputeAllNormalsFromSmoothingGroupsWhenMeshHasBlendShapes: 0
    blendShapeNormalImportMode: 1
    normalSmoothingSource: 0
  referencedClips: []
  importAnimation: 1
  humanDescription:
    serializedVersion: 3
    human: []
    skeleton: []
    armTwist: 0.5
    foreArmTwist: 0.5
    upperLegTwist: 0.5
    legTwist: 0.5
    armStretch: 0.05
    legStretch: 0.05
    feetSpacing: 0
    globalScale: 0.001
    rootMotionBoneName: 
    hasTranslationDoF: 0
    hasExtraRoot: 0
    skeletonHasParents: 1
  lastHumanDescriptionAvatarSource: {{instanceID: 0}}
  autoGenerateAvatarMappingIfUnspecified: 1
  animationType: 2
  humanoidOversampling: 1
  avatarSetup: 0
  addHumanoidExtraRootOnlyWhenUsingAvatar: 1
  additionalBone: 0
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""
        
        meta_path = Path(str(model_path) + ".meta")
        with open(meta_path, 'w', encoding='utf-8') as f:
            f.write(meta_content)
        
        logger.info(f"Unity meta 파일 생성: {meta_path}")
    
    def _create_cyclone_script(self, model_info: Dict) -> str:
        """Unity C# 스크립트 생성"""
        tag = model_info['tag_number'].replace('-', '_')
        script_name = f"Cyclone_{tag}"
        
        script_content = f"""using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Plant3D.Equipment
{{
    /// <summary>
    /// 사이클론 {model_info['tag_number']} 컴포넌트
    /// Fisher-Klosterman {model_info.get('model', 'Size 11')}
    /// </summary>
    public class {script_name} : MonoBehaviour
    {{
        [Header("Equipment Information")]
        public string tagNumber = "{model_info['tag_number']}";
        public string service = "{model_info.get('service', 'Cyclone Separator')}";
        public string manufacturer = "Fisher-Klosterman";
        public string model = "{model_info.get('model', 'Size 11')}";
        
        [Header("Design Parameters")]
        public float cylinderDiameter = {model_info.get('dimensions', {}).get('cylinder_diameter', '279').replace(' mm', '')}f; // mm
        public float totalHeight = {model_info.get('dimensions', {}).get('total_height', '1117').replace(' mm', '')}f; // mm
        public float wallThickness = {model_info.get('dimensions', {}).get('wall_thickness', '12.7').replace(' mm', '')}f; // mm
        
        [Header("Operating Conditions")]
        public float designPressure = 24.6f; // kg/cm²
        public float designTemperature = 140f; // °C
        public string material = "CS";
        
        [Header("Performance")]
        public float efficiency = 99.2f; // %
        public float pressureDrop = 0.357f; // kg/cm²
        public float inletVelocity = 20f; // m/s
        
        [Header("Visualization")]
        public Material cycloneMaterial;
        public bool showFlowAnimation = true;
        public bool showPerformanceData = false;
        
        private void Start()
        {{
            InitializeCyclone();
        }}
        
        private void InitializeCyclone()
        {{
            // 콜라이더 추가 (상호작용을 위해)
            if (GetComponent<Collider>() == null)
            {{
                gameObject.AddComponent<MeshCollider>();
            }}
            
            // 태그 설정
            gameObject.tag = "Equipment";
            gameObject.layer = LayerMask.NameToLayer("Equipment");
            
            // 재질 적용
            if (cycloneMaterial != null)
            {{
                ApplyMaterial();
            }}
            
            Debug.Log($"Cyclone {{tagNumber}} initialized - {{manufacturer}} {{model}}");
        }}
        
        private void ApplyMaterial()
        {{
            MeshRenderer[] renderers = GetComponentsInChildren<MeshRenderer>();
            foreach (var renderer in renderers)
            {{
                renderer.material = cycloneMaterial;
            }}
        }}
        
        /// <summary>
        /// 사이클론 정보 반환
        /// </summary>
        public CycloneInfo GetCycloneInfo()
        {{
            return new CycloneInfo
            {{
                TagNumber = tagNumber,
                Service = service,
                Manufacturer = manufacturer,
                Model = model,
                CylinderDiameter = cylinderDiameter,
                TotalHeight = totalHeight,
                DesignPressure = designPressure,
                DesignTemperature = designTemperature,
                Efficiency = efficiency
            }};
        }}
        
        /// <summary>
        /// 유체 흐름 애니메이션 시작
        /// </summary>
        public void StartFlowAnimation()
        {{
            if (showFlowAnimation)
            {{
                // 파티클 시스템으로 유체 흐름 시각화
                // TODO: 파티클 시스템 구현
            }}
        }}
        
        /// <summary>
        /// 성능 데이터 UI 표시
        /// </summary>
        public void ShowPerformanceData()
        {{
            showPerformanceData = true;
            // TODO: UI 패널 표시
        }}
        
        private void OnMouseDown()
        {{
            // 클릭시 정보 표시
            ShowPerformanceData();
        }}
    }}
    
    [System.Serializable]
    public class CycloneInfo
    {{
        public string TagNumber;
        public string Service;
        public string Manufacturer;
        public string Model;
        public float CylinderDiameter;
        public float TotalHeight;
        public float DesignPressure;
        public float DesignTemperature;
        public float Efficiency;
    }}
}}
"""
        
        script_path = self.scripts_folder / f"{script_name}.cs"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        logger.info(f"Unity C# 스크립트 생성: {script_path}")
        return str(script_path)
    
    def _update_unity_scene(self, model_info: Dict) -> str:
        """Unity Scene 업데이트"""
        scene_name = "Plant3DScene"
        scene_path = self.scenes_folder / f"{scene_name}.unity"
        
        # 기본 Scene 파일 생성 (존재하지 않는 경우)
        if not scene_path.exists():
            scene_content = f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!29 &1
OcclusionCullingSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_OcclusionBakeSettings:
    smallestOccluder: 5
    smallestHole: 0.25
    backfaceThreshold: 100
  m_SceneGUID: 00000000000000000000000000000000
  m_OcclusionCullingData: {{fileID: 0}}
--- !u!104 &2
RenderSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 9
  m_Fog: 0
  m_FogColor: {{r: 0.5, g: 0.5, b: 0.5, a: 1}}
  m_FogMode: 3
  m_FogDensity: 0.01
  m_LinearFogStart: 0
  m_LinearFogEnd: 300
  m_AmbientMode: 0
  m_AmbientSkyColor: {{r: 0.212, g: 0.227, b: 0.259, a: 1}}
  m_AmbientEquatorColor: {{r: 0.114, g: 0.125, b: 0.133, a: 1}}
  m_AmbientGroundColor: {{r: 0.047, g: 0.043, b: 0.035, a: 1}}
  m_AmbientIntensity: 1
  m_AmbientMode: 3
  m_SubtractiveShadowColor: {{r: 0.42, g: 0.478, b: 0.627, a: 1}}
  m_SkyboxMaterial: {{fileID: 0}}
  m_HaloStrength: 0.5
  m_FlareStrength: 1
  m_FlareFadeSpeed: 3
  m_HaloTexture: {{fileID: 0}}
  m_SpotCookie: {{fileID: 10001, guid: 0000000000000000e000000000000000, type: 0}}
  m_DefaultReflectionMode: 0
  m_DefaultReflectionResolution: 128
  m_ReflectionBounces: 1
  m_ReflectionIntensity: 1
  m_CustomReflection: {{fileID: 0}}
  m_Sun: {{fileID: 0}}
  m_IndirectSpecularColor: {{r: 0, g: 0, b: 0, a: 1}}
  m_UseRadianceAmbientProbe: 0
--- !u!157 &3
LightmapSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 12
  m_GIWorkflowMode: 1
  m_GISettings:
    serializedVersion: 2
    m_BounceScale: 1
    m_IndirectOutputScale: 1
    m_AlbedoBoost: 1
    m_EnvironmentLightingMode: 0
    m_EnableBakedLightmaps: 1
    m_EnableRealtimeLightmaps: 0
  m_LightmapEditorSettings:
    serializedVersion: 12
    m_Resolution: 2
    m_BakeResolution: 40
    m_AtlasSize: 1024
    m_AO: 0
    m_AOMaxDistance: 1
    m_CompAOExponent: 1
    m_CompAOExponentDirect: 0
    m_ExtractAmbientOcclusion: 0
    m_Padding: 2
    m_LightmapParameters: {{fileID: 0}}
    m_LightmapsBakeMode: 1
    m_TextureCompression: 1
    m_FinalGather: 0
    m_FinalGatherFiltering: 1
    m_FinalGatherRayCount: 256
    m_ReflectionCompression: 2
    m_MixedBakeMode: 2
    m_BakeBackend: 1
    m_PVRSampling: 1
    m_PVRDirectSampleCount: 32
    m_PVRSampleCount: 512
    m_PVRBounces: 2
    m_PVREnvironmentSampleCount: 256
    m_PVREnvironmentReferencePointCount: 2048
    m_PVRFilteringMode: 1
    m_PVRDenoiserTypeDirect: 1
    m_PVRDenoiserTypeIndirect: 1
    m_PVRDenoiserTypeAO: 1
    m_PVRFilterTypeDirect: 0
    m_PVRFilterTypeIndirect: 0
    m_PVRFilterTypeAO: 0
    m_PVREnvironmentMIS: 1
    m_PVRCulling: 1
    m_PVRFilteringGaussRadiusDirect: 1
    m_PVRFilteringGaussRadiusIndirect: 5
    m_PVRFilteringGaussRadiusAO: 2
    m_PVRFilteringAtrousPositionSigmaDirect: 0.5
    m_PVRFilteringAtrousPositionSigmaIndirect: 2
    m_PVRFilteringAtrousPositionSigmaAO: 1
    m_ExportTrainingData: 0
    m_TrainingDataDestination: TrainingData
    m_LightProbeSampleCountMultiplier: 4
  m_LightingDataAsset: {{fileID: 0}}
  m_LightingSettings: {{fileID: 0}}
--- !u!196 &4
NavMeshSettings:
  serializedVersion: 2
  m_ObjectHideFlags: 0
  m_BuildSettings:
    serializedVersion: 2
    agentTypeID: 0
    agentRadius: 0.5
    agentHeight: 2
    agentSlope: 45
    agentClimb: 0.4
    ledgeDropHeight: 0
    maxJumpAcrossDistance: 0
    minRegionArea: 2
    manualCellSize: 0
    cellSize: 0.16666667
    manualTileSize: 0
    tileSize: 256
    accuratePlacement: 0
    maxJobWorkers: 0
    preserveTilesOutsideBounds: 0
    debug:
      m_Flags: 0
  m_NavMeshData: {{fileID: 0}}
--- !u!1 &{self._generate_unity_object_id()}
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: {self._generate_unity_object_id()}}}
  - component: {{fileID: {self._generate_unity_object_id()}}}
  - component: {{fileID: {self._generate_unity_object_id()}}}
  m_Layer: 0
  m_Name: Main Camera
  m_TagString: MainCamera
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
"""
            
            with open(scene_path, 'w', encoding='utf-8') as f:
                f.write(scene_content)
        
        logger.info(f"Unity Scene 업데이트: {scene_path}")
        return str(scene_path)
    
    def _generate_unity_guid(self) -> str:
        """Unity GUID 생성"""
        import uuid
        return str(uuid.uuid4()).replace('-', '')[:32]
    
    def _generate_unity_object_id(self) -> str:
        """Unity Object ID 생성"""
        import random
        return str(random.randint(100000000, 999999999))
    
    def _refresh_unity_project(self):
        """Unity 프로젝트 새로고침"""
        try:
            # Unity가 실행 중이면 Asset Database 새로고침
            unity_log_path = self.unity_project_path / "Logs" / "AssetImportWorker0.log"
            
            if unity_log_path.exists():
                logger.info("Unity 프로젝트가 실행 중입니다. Asset Database가 자동으로 새로고침됩니다.")
            else:
                logger.info("Unity 프로젝트를 실행하여 Asset을 확인하세요.")
                
        except Exception as e:
            logger.warning(f"Unity 새로고침 실패: {e}")
    
    def create_integration_summary(self, model_info: Dict, unity_model_path: str) -> Dict:
        """Unity 통합 요약 정보 생성"""
        return {
            'unity_integration': {
                'model_path': unity_model_path,
                'unity_project': str(self.unity_project_path),
                'assets_folder': str(self.unity_assets_path),
                'scripts_created': True,
                'scene_updated': True,
                'status': 'completed'
            },
            'equipment_info': model_info,
            'next_steps': [
                "Unity Editor에서 프로젝트 열기",
                "Models/Cyclones 폴더에서 STEP 파일 확인",
                "Scripts 폴더에서 생성된 C# 스크립트 확인", 
                "Plant3DScene에서 사이클론 배치 확인",
                "재질 및 조명 설정"
            ]
        }


def integrate_with_unity(freecad_model_path: str, model_info: Dict) -> Dict:
    """FreeCAD 모델을 Unity에 통합하는 헬퍼 함수"""
    try:
        logger.info("Unity 통합 시작...")
        
        # Unity 통합 객체 생성
        unity_integration = UnityIntegration()
        
        # 모델 import
        unity_model_path = unity_integration.import_cyclone_model(freecad_model_path, model_info)
        
        # 통합 요약 생성
        summary = unity_integration.create_integration_summary(model_info, unity_model_path)
        
        logger.info("Unity 통합 완료!")
        return summary
        
    except Exception as e:
        logger.error(f"Unity 통합 실패: {e}")
        raise


if __name__ == "__main__":
    # 테스트
    import sys
    
    if len(sys.argv) > 2:
        freecad_path = sys.argv[1]
        model_info_json = sys.argv[2]
        
        try:
            with open(model_info_json, 'r', encoding='utf-8') as f:
                model_info = json.load(f)
            
            summary = integrate_with_unity(freecad_path, model_info)
            
            print("\n" + "="*60)
            print("🎮 Unity 통합 완료!")
            print("="*60)
            print(f"📁 Unity 모델 경로: {summary['unity_integration']['model_path']}")
            print(f"🎯 Unity 프로젝트: {summary['unity_integration']['unity_project']}")
            print(f"\n📋 다음 단계:")
            for step in summary['next_steps']:
                print(f"  • {step}")
                
        except Exception as e:
            print(f"❌ 오류: {e}")
            sys.exit(1)
    else:
        print("사용법: python unity_integration.py <FreeCAD모델경로> <모델정보JSON>")
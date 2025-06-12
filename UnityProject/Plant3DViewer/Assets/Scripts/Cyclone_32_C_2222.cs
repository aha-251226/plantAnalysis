using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Plant3D.Equipment
{
    /// <summary>
    /// 사이클론 32-C-2222 컴포넌트
    /// Fisher-Klosterman 11
    /// </summary>
    public class Cyclone_32_C_2222 : MonoBehaviour
    {
        [Header("Equipment Information")]
        public string tagNumber = "32-C-2222";
        public string service = "Flash Gas Cyclone";
        public string manufacturer = "Fisher-Klosterman";
        public string model = "11";
        
        [Header("Design Parameters")]
        public float cylinderDiameter = 279f; // mm
        public float totalHeight = 1117f; // mm
        public float wallThickness = 12.7f; // mm
        
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
        {
            InitializeCyclone();
        }
        
        private void InitializeCyclone()
        {
            // 콜라이더 추가 (상호작용을 위해)
            if (GetComponent<Collider>() == null)
            {
                gameObject.AddComponent<MeshCollider>();
            }
            
            // 태그 설정
            gameObject.tag = "Equipment";
            gameObject.layer = LayerMask.NameToLayer("Equipment");
            
            // 재질 적용
            if (cycloneMaterial != null)
            {
                ApplyMaterial();
            }
            
            Debug.Log($"Cyclone {tagNumber} initialized - {manufacturer} {model}");
        }
        
        private void ApplyMaterial()
        {
            MeshRenderer[] renderers = GetComponentsInChildren<MeshRenderer>();
            foreach (var renderer in renderers)
            {
                renderer.material = cycloneMaterial;
            }
        }
        
        /// <summary>
        /// 사이클론 정보 반환
        /// </summary>
        public CycloneInfo GetCycloneInfo()
        {
            return new CycloneInfo
            {
                TagNumber = tagNumber,
                Service = service,
                Manufacturer = manufacturer,
                Model = model,
                CylinderDiameter = cylinderDiameter,
                TotalHeight = totalHeight,
                DesignPressure = designPressure,
                DesignTemperature = designTemperature,
                Efficiency = efficiency
            };
        }
        
        /// <summary>
        /// 유체 흐름 애니메이션 시작
        /// </summary>
        public void StartFlowAnimation()
        {
            if (showFlowAnimation)
            {
                // 파티클 시스템으로 유체 흐름 시각화
                // TODO: 파티클 시스템 구현
            }
        }
        
        /// <summary>
        /// 성능 데이터 UI 표시
        /// </summary>
        public void ShowPerformanceData()
        {
            showPerformanceData = true;
            // TODO: UI 패널 표시
        }
        
        private void OnMouseDown()
        {
            // 클릭시 정보 표시
            ShowPerformanceData();
        }
    }
    
    [System.Serializable]
    public class CycloneInfo
    {
        public string TagNumber;
        public string Service;
        public string Manufacturer;
        public string Model;
        public float CylinderDiameter;
        public float TotalHeight;
        public float DesignPressure;
        public float DesignTemperature;
        public float Efficiency;
    }
}

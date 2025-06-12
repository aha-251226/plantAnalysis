import streamlit as st
import plotly.graph_objects as go
import numpy as np
import json
from pathlib import Path
import pandas as pd
import base64
import time
from plotly.subplots import make_subplots

# 페이지 설정
st.set_page_config(
    page_title=("Cyclone Engineering Review System"),
    page_icon=None,
    layout="wide"
)

# CSS 스타일 - 글자 크기 축소
st.markdown("""
<style>
    .metric-value { font-size: 0.4rem !important; }
    .metric-label { font-size: 0.6rem !important; }
    div[data-testid="metric-container"] { padding: 0.2rem !important; }
    h1 { font-size: 2.5rem !important; }
    h2 { font-size: 1.1rem !important; }
    h3 { font-size: 0.95rem !important; }
    h4 { font-size: 0.85rem !important; }
    .stTabs [data-baseweb="tab-list"] { font-size: 0.8rem !important; }
</style>
""", unsafe_allow_html=True)

# 타이틀
st.title("Engineering Review")

# 세션 상태
if 'pdf_uploaded' not in st.session_state:
    st.session_state.pdf_uploaded = False

# 파일 경로
json_file = Path("src/extractor/data/extracted/MF PE Cyclone_20250609_extracted.json")

# JSON 데이터 로드
@st.cache_data
def load_json_data():
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

# Cut size 계산
def calculate_cut_size(flow_ratio, base_d50=5.0):
    """유량 변화에 따른 cut size 계산"""
    return base_d50 / np.sqrt(flow_ratio)

# 효율 곡선 계산
def calculate_efficiency(particle_size, d50):
    """Barth 모델 기반 효율 계산"""
    n = 2.5  # slope parameter
    return 100 / (1 + (d50/particle_size)**n)

# 사이드바
with st.sidebar:
    st.markdown("### 📄 PDF Upload")
    uploaded_pdf = st.file_uploader("Dats sheet", type=['pdf'])
    
    if uploaded_pdf:
        st.success("✅ Complete!")
        st.session_state.pdf_uploaded = True
        
        pdf_bytes = uploaded_pdf.read()
        
        # PDF 미리보기
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="300"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

# 메인 화면
data = load_json_data()

if st.session_state.pdf_uploaded and data:
    # 상단 정보
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Tag", data.get('tag_number', 'N/A'))
    with col2:
        st.metric("Service", data.get('service', 'N/A')[:15])
    with col3:
        st.metric("Design P", f"{data.get('design_pressure', 0)} kg/cm²")
    with col4:
        st.metric("Design T", f"{data.get('design_temperature', 0)}°C")
    with col5:
        st.metric("효율", f"{data.get('efficiency', 0)}%")
    with col6:
        st.metric("ΔP", f"{data.get('pressure_drop', 0)} kg/cm²")
    
    st.markdown("---")
    
    # 메인 탭
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 기본 데이터",
        "🔍 설계 마진",
        "📈 성능 검토",
        "🔄 병렬/직렬",
        "🎯 입자 분리",
        "⚠️ 이상 상황"
    ])
    
    # Tab 1: 기본 데이터
    with tab1:
        col1, col2, col3 = st.columns([3, 3, 3])
        
        with col1:
            st.markdown("#### 운전 조건")
            st.write(f"온도: {data.get('temperature', 0)}°C")
            st.write(f"압력: {data.get('pressure', 0)} kg/cm²")
            st.write(f"유량: {data.get('flow_rate', 0)} kg/hr")
            st.write(f"밀도: {data.get('density', 0)} kg/m³")
        
        with col2:
            st.markdown("#### 성능")
            st.write(f"효율: {data.get('efficiency', 0)}%")
            st.write(f"압력손실: {data.get('pressure_drop', 0)} kg/cm²")
            st.write(f"입구속도: {data.get('inlet_velocity', 0)} m/s")
            if data.get('dimensions'):
                st.write(f"입구크기: {data['dimensions'].get('inlet_height_mm', 0)}x{data['dimensions'].get('inlet_width_mm', 0)}mm")
        
        with col3:
            st.markdown("#### 노즐")
            if data.get('nozzles'):
                for nozzle in data['nozzles']:
                    st.write(f"• {nozzle.get('service', '')}: {nozzle.get('size', '')}")
    
    # Tab 2: 설계 마진
    with tab2:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 압력 마진
            design_p = data.get('design_pressure', 24.6)
            oper_p = data.get('pressure', 10.2)
            margin_p = ((design_p - oper_p) / oper_p) * 100
            
            st.metric("압력 마진", f"{margin_p:.0f}%")
            if margin_p > 100:
                st.success("충분")
            elif margin_p > 50:
                st.info("적정")
            else:
                st.warning("부족")
        
        with col2:
            # 온도 마진
            design_t = data.get('design_temperature', 140)
            oper_t = data.get('temperature', 82.2)
            margin_t = ((design_t - oper_t) / oper_t) * 100
            
            st.metric("온도 마진", f"{margin_t:.0f}%")
            if margin_t > 50:
                st.success("충분")
            elif margin_t > 30:
                st.info("적정")
            else:
                st.warning("부족")
        
        with col3:
            # 재질
            material = data.get('material', 'CS')
            st.metric("재질", material)
            if material == 'CS' and oper_t <= 400:
                st.success("적합")
            else:
                st.warning("검토")
    
    # Tab 3: 성능 검토
    with tab3:
        # 조건 변경
        col1, col2, col3 = st.columns(3)
        with col1:
            new_flow = st.slider("유량 (kg/hr)", 
                               int(data.get('flow_rate', 671) * 0.5), 
                               int(data.get('flow_rate', 671) * 1.5), 
                               int(data.get('flow_rate', 671)))
        with col2:
            new_temp = st.slider("온도 (°C)", 50, 150, int(data.get('temperature', 82)))
        with col3:
            new_pressure = st.slider("압력 (kg/cm²)", 5, 15, int(data.get('pressure', 10)))
        
        # 계산
        base_flow = data.get('flow_rate', 671)
        base_dp = data.get('pressure_drop', 0.357)
        base_velocity = data.get('inlet_velocity', 20)
        
        flow_ratio = new_flow / base_flow
        new_velocity = base_velocity * flow_ratio
        new_dp = base_dp * flow_ratio ** 2
        
        # 결과
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("입구속도", f"{new_velocity:.1f} m/s", 
                     f"{new_velocity - base_velocity:+.1f}")
            if new_velocity > 25:
                st.error("침식 위험")
        
        with col2:
            st.metric("압력손실", f"{new_dp:.3f} kg/cm²", 
                     f"{new_dp - base_dp:+.3f}")
            if new_dp > 1.0:
                st.warning("과도함")
        
        with col3:
            eff_change = -2 * abs(flow_ratio - 1)
            new_eff = max(85, data.get('efficiency', 99.2) + eff_change)
            st.metric("예상 효율", f"{new_eff:.1f}%", 
                     f"{new_eff - data.get('efficiency', 99.2):+.1f}")
        
        # 그래프
        st.markdown("---")
        
        # 압력손실 곡선
        flow_range = np.linspace(base_flow * 0.3, base_flow * 1.7, 50)
        dp_curve = base_dp * (flow_range / base_flow) ** 2
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=flow_range, y=dp_curve, mode='lines', name='압력손실'))
        fig.add_trace(go.Scatter(x=[new_flow], y=[new_dp], mode='markers', 
                                marker=dict(size=10, color='red'), name='운전점'))
        fig.add_hline(y=1.0, line_dash="dash", annotation_text="한계")
        fig.update_xaxes(title="유량 (kg/hr)")
        fig.update_yaxes(title="압력손실 (kg/cm²)")
        fig.update_layout(height=300)
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Tab 4: 병렬/직렬 운전
    with tab4:
        st.markdown("#### 병렬/직렬 구성 시뮬레이션")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 병렬 운전")
            n_parallel = st.selectbox("병렬 대수", [1, 2, 3, 4])
            
            if n_parallel > 1:
                # 각 사이클론 유량
                flow_per_unit = base_flow / n_parallel
                velocity_per_unit = base_velocity / n_parallel
                dp_per_unit = base_dp * (1/n_parallel) ** 2
                
                st.write(f"• 대당 유량: {flow_per_unit:.0f} kg/hr")
                st.write(f"• 대당 속도: {velocity_per_unit:.1f} m/s")
                st.write(f"• 압력손실: {dp_per_unit:.3f} kg/cm² (동일)")
                
                # 효율 변화
                d50_parallel = calculate_cut_size(1/n_parallel)
                eff_10um = calculate_efficiency(10, d50_parallel)
                
                st.write(f"• Cut size: {d50_parallel:.1f} μm")
                st.write(f"• 10μm 효율: {eff_10um:.1f}%")
                
                if velocity_per_unit < 15:
                    st.warning("속도가 너무 낮음")
                else:
                    st.success("적정 속도 범위")
        
        with col2:
            st.markdown("##### 직렬 운전")
            n_series = st.selectbox("직렬 단수", [1, 2, 3])
            
            if n_series > 1:
                # 전체 압력손실
                total_dp = base_dp * n_series
                
                # 단별 효율
                stage_eff = data.get('efficiency', 99.2) / 100
                total_eff = 1 - (1 - stage_eff) ** n_series
                
                st.write(f"• 총 압력손실: {total_dp:.3f} kg/cm²")
                st.write(f"• 총 효율: {total_eff*100:.2f}%")
                
                # 입자별 효율
                particle_sizes = [1, 5, 10, 20]
                for size in particle_sizes:
                    eff_single = calculate_efficiency(size, 5.0) / 100
                    eff_total = 1 - (1 - eff_single) ** n_series
                    st.write(f"• {size}μm: {eff_total*100:.1f}%")
                
                if total_dp > 1.5:
                    st.error("압력손실 과도")
                else:
                    st.success("압력손실 허용범위")
    
    # Tab 5: 입자 분리 특성
    with tab5:
        st.markdown("#### 입자 크기별 분리 효율")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Cut size 조정
            d50_factor = st.slider("Cut size 조정 계수", 0.5, 2.0, 1.0)
            d50_adjusted = 5.0 * d50_factor
            
            # 효율 곡선
            particle_range = np.logspace(-0.5, 2.5, 100)  # 0.3 - 300 μm
            efficiency_base = calculate_efficiency(particle_range, 5.0)
            efficiency_adjusted = calculate_efficiency(particle_range, d50_adjusted)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=particle_range, y=efficiency_base,
                                   mode='lines', name='기준', line=dict(dash='dash')))
            fig.add_trace(go.Scatter(x=particle_range, y=efficiency_adjusted,
                                   mode='lines', name='조정', line=dict(width=3)))
            
            # 주요 입자 크기 표시
            key_sizes = [1, 5, 10, 50, 100]
            for size in key_sizes:
                fig.add_vline(x=size, line_dash="dot", opacity=0.3)
            
            fig.update_xaxes(type="log", title="입자 크기 (μm)")
            fig.update_yaxes(title="효율 (%)", range=[0, 100])
            fig.update_layout(height=400)
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("##### 주요 입자 효율")
            
            for size in [1, 5, 10, 20, 50]:
                eff = calculate_efficiency(size, d50_adjusted)
                st.metric(f"{size} μm", f"{eff:.1f}%")
            
            st.markdown("---")
            st.write(f"**d50**: {d50_adjusted:.1f} μm")
            st.write(f"**d90**: {d50_adjusted * 3:.1f} μm")
    
    # Tab 6: 이상 상황 시뮬레이션
    with tab6:
        st.markdown("#### 이상 상황 분석")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 막힘 시나리오")
            
            blockage = st.slider("입구 막힘 (%)", 0, 50, 0)
            
            if blockage > 0:
                # 유효 면적 감소
                area_factor = 1 - blockage/100
                
                # 속도 증가
                blocked_velocity = base_velocity / area_factor
                blocked_dp = base_dp / (area_factor ** 2)
                
                st.write(f"• 실제 속도: {blocked_velocity:.1f} m/s")
                st.write(f"• 압력손실: {blocked_dp:.3f} kg/cm²")
                
                if blocked_velocity > 25:
                    st.error("⚠️ 심각한 침식 위험")
                elif blocked_velocity > 22:
                    st.warning("⚠️ 침식 주의")
                
                if blocked_dp > 1.0:
                    st.error("⚠️ 과도한 압력손실")
        
        with col2:
            st.markdown("##### 마모 예측")
            
            operating_hours = st.number_input("운전 시간 (hr)", 0, 50000, 8760)
            
            if operating_hours > 0:
                # 침식률 계산 (간단한 모델)
                erosion_rate = (base_velocity / 20) ** 3  # mm/year
                thickness_loss = erosion_rate * (operating_hours / 8760)
                
                # 효율 저하
                eff_degradation = min(10, thickness_loss * 0.5)
                predicted_eff = max(80, data.get('efficiency', 99.2) - eff_degradation)
                
                st.write(f"• 예상 마모: {thickness_loss:.1f} mm")
                st.write(f"• 예상 효율: {predicted_eff:.1f}%")
                
                # 점검 주기
                if thickness_loss > 5:
                    st.error("즉시 점검 필요")
                elif thickness_loss > 3:
                    st.warning("점검 계획 수립")
                else:
                    st.success("정상 범위")
                
                # 권장 점검 주기
                if base_velocity > 22:
                    inspection_interval = 3  # months
                elif base_velocity > 20:
                    inspection_interval = 6
                else:
                    inspection_interval = 12
                
                st.info(f"권장 점검 주기: {inspection_interval}개월")
        
        # 종합 위험도 평가
        st.markdown("---")
        st.markdown("#### 종합 위험도 매트릭스")
        
        # 위험 요소 점수
        risk_scores = {
            "압력 마진": 100 if margin_p > 100 else (50 if margin_p > 50 else 20),
            "온도 마진": 100 if margin_t > 50 else (50 if margin_t > 30 else 20),
            "입구 속도": 100 if base_velocity < 20 else (50 if base_velocity < 22 else 20),
            "압력손실": 100 if base_dp < 0.5 else (50 if base_dp < 0.7 else 20),
            "효율": 100 if data.get('efficiency', 99.2) > 95 else 50
        }
        
        avg_risk = np.mean(list(risk_scores.values()))
        
        # 시각화
        fig = go.Figure(data=[
            go.Bar(x=list(risk_scores.keys()), y=list(risk_scores.values()),
                   marker_color=['green' if v > 70 else 'orange' if v > 40 else 'red' 
                                for v in risk_scores.values()])
        ])
        fig.add_hline(y=70, line_dash="dash", annotation_text="안전")
        fig.add_hline(y=40, line_dash="dash", annotation_text="주의")
        fig.update_yaxes(range=[0, 100], title="점수")
        fig.update_layout(height=300)
        
        st.plotly_chart(fig, use_container_width=True)
        
        if avg_risk > 70:
            st.success(f"종합 점수: {avg_risk:.0f}/100 - 안전한 운전 상태")
        elif avg_risk > 40:
            st.warning(f"종합 점수: {avg_risk:.0f}/100 - 주의 필요")
        else:
            st.error(f"종합 점수: {avg_risk:.0f}/100 - 위험 상태")

else:
    st.info("Upload your PDF file")

# 푸터
st.markdown("---")
st.caption("Yonsei University | aha0810@yonsei.ac.kr, 2025. All rights reserved.")
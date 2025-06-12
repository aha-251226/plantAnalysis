using UnityEngine;
using UnityEngine.UI;
using System.Collections;
using System.Collections.Generic;

public class CFD : MonoBehaviour
{
    // �ڵ� ������ ������Ʈ��
    private GameObject cyclone;
    private ParticleSystem gasParticles;
    private ParticleSystem dustParticles;
    private LineRenderer flowLines;

    // UI ��ҵ�
    private Slider velocitySlider;
    private Slider pressureSlider;
    private Text efficiencyText;

    // �ùķ��̼� �Ķ����
    private float inletVelocity = 15f;
    private float pressure = 101325f;
    private float efficiency = 0f;

    void Start()
    {
        // 1. ����Ŭ�� �� �ڵ� ���� (OBJ ��� ����)
        CreateCycloneModel();

        // 2. ��ƼŬ �ý��� ����
        CreateParticleSystems();

        // 3. UI ����
        CreateUI();

        // 4. ī�޶� ����
        SetupCamera();

        // 5. �ùķ��̼� ����
        StartCoroutine(RunSimulation());
    }

    void CreateCycloneModel()
    {
        // ���� ����Ŭ�� �����̳�
        cyclone = new GameObject("Cyclone");

        // ������ ��� (�Ǹ���)
        GameObject cylinder = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        cylinder.name = "Upper_Body";
        cylinder.transform.parent = cyclone.transform;
        cylinder.transform.localScale = new Vector3(2f, 3f, 2f);
        cylinder.transform.position = Vector3.zero;

        // ������ �Ϻ�
        GameObject cone = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        cone.name = "Lower_Cone";
        cone.transform.parent = cyclone.transform;
        cone.transform.localScale = new Vector3(2f, 2f, 2f);
        cone.transform.position = new Vector3(0, -2.5f, 0);

        // ���� �ⱸ (���)
        GameObject gasOutlet = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        gasOutlet.name = "Gas_Outlet";
        gasOutlet.transform.parent = cyclone.transform;
        gasOutlet.transform.localScale = new Vector3(0.8f, 1f, 0.8f);
        gasOutlet.transform.position = new Vector3(0, 2f, 0);

        // �Ա� ��Ʈ (���� ����)
        GameObject inlet = GameObject.CreatePrimitive(PrimitiveType.Cube);
        inlet.name = "Inlet";
        inlet.transform.parent = cyclone.transform;
        inlet.transform.localScale = new Vector3(0.5f, 0.5f, 2f);
        inlet.transform.position = new Vector3(1.5f, 1f, 0);
        inlet.transform.rotation = Quaternion.Euler(0, 45, 0);

        // ���� ���� ����
        MakeSemiTransparent(cylinder);
        MakeSemiTransparent(cone);
        MakeSemiTransparent(gasOutlet);
    }

    void MakeSemiTransparent(GameObject obj)
    {
        Renderer renderer = obj.GetComponent<Renderer>();
        Material mat = new Material(Shader.Find("Standard"));
        mat.SetFloat("_Mode", 3); // Transparent mode
        mat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        mat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        mat.SetInt("_ZWrite", 0);
        mat.DisableKeyword("_ALPHATEST_ON");
        mat.EnableKeyword("_ALPHABLEND_ON");
        mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");
        mat.renderQueue = 3000;

        Color color = Color.cyan;
        color.a = 0.3f;
        mat.color = color;
        renderer.material = mat;
    }

    void CreateParticleSystems()
    {
        // ���� ��ƼŬ (û��)
        GameObject gasObj = new GameObject("Gas_Particles");
        gasObj.transform.parent = cyclone.transform;
        gasObj.transform.position = new Vector3(1.5f, 1f, 0);
        gasParticles = gasObj.AddComponent<ParticleSystem>();

        var gasMain = gasParticles.main;
        gasMain.startLifetime = 5f;
        gasMain.startSpeed = inletVelocity;
        gasMain.maxParticles = 1000;
        gasMain.startColor = Color.cyan;

        var gasShape = gasParticles.shape;
        gasShape.shapeType = ParticleSystemShapeType.Box;
        gasShape.scale = new Vector3(0.5f, 0.5f, 0.1f);

        var gasVelocity = gasParticles.velocityOverLifetime;
        gasVelocity.enabled = true;
        gasVelocity.space = ParticleSystemSimulationSpace.World;

        // ������ �������� ���� �ӵ� ����
        AnimationCurve curveX = new AnimationCurve();
        curveX.AddKey(0f, 0f);
        curveX.AddKey(1f, -10f);
        gasVelocity.x = new ParticleSystem.MinMaxCurve(1f, curveX);

        AnimationCurve curveY = new AnimationCurve();
        curveY.AddKey(0f, 0f);
        curveY.AddKey(1f, 5f);
        gasVelocity.y = new ParticleSystem.MinMaxCurve(1f, curveY);

        // ���� ��ƼŬ (����)
        GameObject dustObj = new GameObject("Dust_Particles");
        dustObj.transform.parent = cyclone.transform;
        dustObj.transform.position = new Vector3(1.5f, 1f, 0);
        dustParticles = dustObj.AddComponent<ParticleSystem>();

        var dustMain = dustParticles.main;
        dustMain.startLifetime = 8f;
        dustMain.startSpeed = inletVelocity * 0.8f;
        dustMain.maxParticles = 500;
        dustMain.startColor = Color.red;
        dustMain.gravityModifier = 0.5f;

        var dustShape = dustParticles.shape;
        dustShape.shapeType = ParticleSystemShapeType.Box;
        dustShape.scale = new Vector3(0.5f, 0.5f, 0.1f);
    }

    void CreateUI()
    {
        // Canvas ����
        GameObject canvasObj = new GameObject("UI_Canvas");
        Canvas canvas = canvasObj.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvasObj.AddComponent<CanvasScaler>();
        canvasObj.AddComponent<GraphicRaycaster>();

        // �г� ����
        GameObject panel = new GameObject("Control_Panel");
        panel.transform.SetParent(canvasObj.transform, false);
        RectTransform panelRect = panel.AddComponent<RectTransform>();
        panelRect.anchorMin = new Vector2(0, 0);
        panelRect.anchorMax = new Vector2(0, 1);
        panelRect.offsetMin = new Vector2(10, 10);
        panelRect.offsetMax = new Vector2(310, -10);

        Image panelImg = panel.AddComponent<Image>();
        panelImg.color = new Color(0, 0, 0, 0.8f);

        // ����
        CreateText("CFD Simulation", panel.transform, new Vector2(150, -30));

        // �ӵ� �����̴�
        CreateText("Inlet Velocity: " + inletVelocity + " m/s", panel.transform, new Vector2(150, -70));
        velocitySlider = CreateSlider(panel.transform, new Vector2(150, -100), 5f, 30f, inletVelocity);
        velocitySlider.onValueChanged.AddListener(OnVelocityChanged);

        // �з� �����̴�
        CreateText("Pressure Drop: " + (101325 - pressure) + " Pa", panel.transform, new Vector2(150, -150));
        pressureSlider = CreateSlider(panel.transform, new Vector2(150, -180), 0f, 5000f, 0f);
        pressureSlider.onValueChanged.AddListener(OnPressureChanged);

        // ȿ�� ǥ��
        efficiencyText = CreateText("Separation Efficiency: 0%", panel.transform, new Vector2(150, -230));

        // ���� ��ư
        CreateButton("Reset Simulation", panel.transform, new Vector2(150, -280), ResetSimulation);
    }

    Text CreateText(string content, Transform parent, Vector2 position)
    {
        GameObject textObj = new GameObject("Text");
        textObj.transform.SetParent(parent, false);

        RectTransform rect = textObj.AddComponent<RectTransform>();
        rect.anchoredPosition = position;
        rect.sizeDelta = new Vector2(280, 30);

        Text text = textObj.AddComponent<Text>();
        text.text = content;
        text.font = Resources.GetBuiltinResource<Font>("Arial.ttf");
        text.fontSize = 16;
        text.color = Color.white;
        text.alignment = TextAnchor.MiddleCenter;

        return text;
    }

    Slider CreateSlider(Transform parent, Vector2 position, float min, float max, float value)
    {
        GameObject sliderObj = new GameObject("Slider");
        sliderObj.transform.SetParent(parent, false);

        RectTransform rect = sliderObj.AddComponent<RectTransform>();
        rect.anchoredPosition = position;
        rect.sizeDelta = new Vector2(250, 20);

        Slider slider = sliderObj.AddComponent<Slider>();
        slider.minValue = min;
        slider.maxValue = max;
        slider.value = value;

        // ���
        GameObject background = new GameObject("Background");
        background.transform.SetParent(sliderObj.transform, false);
        RectTransform bgRect = background.AddComponent<RectTransform>();
        bgRect.sizeDelta = new Vector2(250, 10);
        bgRect.anchoredPosition = Vector2.zero;
        Image bgImg = background.AddComponent<Image>();
        bgImg.color = Color.gray;

        // �ڵ�
        GameObject handle = new GameObject("Handle");
        handle.transform.SetParent(sliderObj.transform, false);
        RectTransform handleRect = handle.AddComponent<RectTransform>();
        handleRect.sizeDelta = new Vector2(20, 20);
        Image handleImg = handle.AddComponent<Image>();
        handleImg.color = Color.white;

        slider.targetGraphic = handleImg;
        slider.handleRect = handleRect;

        return slider;
    }

    void CreateButton(string text, Transform parent, Vector2 position, UnityEngine.Events.UnityAction action)
    {
        GameObject buttonObj = new GameObject("Button");
        buttonObj.transform.SetParent(parent, false);

        RectTransform rect = buttonObj.AddComponent<RectTransform>();
        rect.anchoredPosition = position;
        rect.sizeDelta = new Vector2(200, 40);

        Button button = buttonObj.AddComponent<Button>();
        Image buttonImg = buttonObj.AddComponent<Image>();
        buttonImg.color = new Color(0.2f, 0.6f, 1f);
        button.targetGraphic = buttonImg;

        GameObject textObj = new GameObject("Text");
        textObj.transform.SetParent(buttonObj.transform, false);
        Text buttonText = textObj.AddComponent<Text>();
        buttonText.text = text;
        buttonText.font = Resources.GetBuiltinResource<Font>("Arial.ttf");
        buttonText.fontSize = 16;
        buttonText.color = Color.white;
        buttonText.alignment = TextAnchor.MiddleCenter;
        RectTransform textRect = textObj.GetComponent<RectTransform>();
        textRect.sizeDelta = new Vector2(200, 40);

        button.onClick.AddListener(action);
    }

    void SetupCamera()
    {
        Camera.main.transform.position = new Vector3(5, 3, -5);
        Camera.main.transform.LookAt(cyclone.transform);
        Camera.main.backgroundColor = new Color(0.1f, 0.1f, 0.2f);
    }

    void OnVelocityChanged(float value)
    {
        inletVelocity = value;
        var gasMain = gasParticles.main;
        gasMain.startSpeed = value;
        var dustMain = dustParticles.main;
        dustMain.startSpeed = value * 0.8f;

        // UI �ؽ�Ʈ ������Ʈ
        Transform panel = GameObject.Find("Control_Panel").transform;
        panel.GetChild(1).GetComponent<Text>().text = "Inlet Velocity: " + value.ToString("F1") + " m/s";
    }

    void OnPressureChanged(float value)
    {
        pressure = 101325f - value;

        // UI �ؽ�Ʈ ������Ʈ
        Transform panel = GameObject.Find("Control_Panel").transform;
        panel.GetChild(3).GetComponent<Text>().text = "Pressure Drop: " + value.ToString("F0") + " Pa";
    }

    void ResetSimulation()
    {
        gasParticles.Clear();
        dustParticles.Clear();
        efficiency = 0f;
        velocitySlider.value = 15f;
        pressureSlider.value = 0f;
    }

    IEnumerator RunSimulation()
    {
        while (true)
        {
            // ȿ�� ��� (������ ��)
            efficiency = Mathf.Min(95f, (inletVelocity / 15f) * 85f + (pressureSlider.value / 5000f) * 10f);
            efficiencyText.text = "Separation Efficiency: " + efficiency.ToString("F1") + "%";

            // ī�޶� ȸ��
            Camera.main.transform.RotateAround(cyclone.transform.position, Vector3.up, 20f * Time.deltaTime);

            yield return null;
        }
    }
}
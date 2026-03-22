import numpy as np
import pandas as pd
import joblib


FEATURE_COLUMNS = ["age", "onset_days", "fac_adm", "fma_le_adm", "tis_adm"]
FEATURE_LABELS = {
    "age": "年齢",
    "onset_days": "発症から入院まで日数",
    "fac_adm": "入院時FAC",
    "fma_le_adm": "入院時FMA-LE",
    "tis_adm": "入院時TIS",
}


def explain_logistic_case(model, case_df):
    imputer = model.named_steps["imputer"]
    scaler = model.named_steps["scaler"]
    classifier = model.named_steps["model"]

    imputed_values = imputer.transform(case_df[FEATURE_COLUMNS])
    scaled_values = scaler.transform(imputed_values)
    coefficients = classifier.coef_[0]
    contributions = scaled_values[0] * coefficients
    intercept = float(classifier.intercept_[0])
    total_logit = intercept + float(contributions.sum())
    total_probability = 1 / (1 + np.exp(-total_logit))

    explanation_df = pd.DataFrame(
        {
            "項目": [FEATURE_LABELS[column] for column in FEATURE_COLUMNS],
            "入力値": case_df.iloc[0][FEATURE_COLUMNS].values,
            "標準化後": scaled_values[0],
            "寄与(log-odds)": contributions,
        }
    ).sort_values("寄与(log-odds)", key=lambda s: s.abs(), ascending=False)

    print("\n[logistic explanation]")
    print("正の寄与は自立方向、負の寄与は非自立方向を示します。")
    print(f"切片寄与: {intercept:.3f}")
    print(f"合計log-odds: {total_logit:.3f}")
    print(f"説明上の自立確率: {total_probability:.3f}")
    print(
        explanation_df.to_string(
            index=False,
            formatters={
                "入力値": lambda value: f"{float(value):.1f}",
                "標準化後": lambda value: f"{value:.3f}",
                "寄与(log-odds)": lambda value: f"{value:+.3f}",
            },
        )
    )


# 保存したモデルを読み込む
logistic_model = joblib.load("logistic_model.joblib")
tree_model = joblib.load("tree_model.joblib")

# 新しい患者データを1件入力
new_patient = pd.DataFrame(
    [
        {
            "age": 72,
            "onset_days": 20,
            "fac_adm": 2,
            "fma_le_adm": 21,
            "tis_adm": 14,
        }
    ]
)

models = {
    "logistic": logistic_model,
    "tree": tree_model,
}

print("=== 新規症例の予測 ===")
print(new_patient)

for name, model in models.items():
    prob = model.predict_proba(new_patient)[0, 1]
    pred = model.predict(new_patient)[0]
    print(f"\n[{name}]")
    print(f"歩行自立確率: {prob:.3f}")
    print(f"予測ラベル: {pred} (1=自立, 0=非自立)")

    if name == "logistic":
        explain_logistic_case(model, new_patient)

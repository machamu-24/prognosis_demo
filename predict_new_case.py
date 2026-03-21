import pandas as pd
import joblib

# 保存したモデルを読み込む
logistic_model = joblib.load("logistic_model.joblib")
tree_model = joblib.load("tree_model.joblib")

# 新しい患者データを1件入力
new_patient = pd.DataFrame(
    [
        {
            "age": 72,
            "onset_days": 20,
            "gait_adm": 2,
            "leg_func": 3,
            "trunk": 2,
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
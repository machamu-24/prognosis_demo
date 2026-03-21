import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.metrics import (
    roc_auc_score,
    confusion_matrix,
    classification_report,
    ConfusionMatrixDisplay,
    brier_score_loss,
    RocCurveDisplay,
)
from sklearn.calibration import CalibrationDisplay


# =========================
# 1. ダミーデータ生成
# =========================
def clip_round(values, min_value, max_value):
    values = np.round(values).astype(int)
    return np.clip(values, min_value, max_value)


def generate_dummy_data(n=300, random_state=42):
    rng = np.random.default_rng(random_state)

    # -------------------------
    # A. 基本属性の生成
    # -------------------------
    # 年齢: 50-95歳, 平均75歳前後
    age = rng.normal(loc=75, scale=8, size=n)
    age = np.clip(age, 50, 95).round(0)

    # 発症から入院までの日数: 7-60日, やや右裾
    onset_days = rng.gamma(shape=4.0, scale=6.0, size=n) + 5
    onset_days = np.clip(onset_days, 7, 60).round(0)

    # 潜在重症度（見えない要因の一部）
    # 値が大きいほど重い
    latent_severity = rng.normal(loc=0.0, scale=1.0, size=n)

    # -------------------------
    # B. 順序尺度変数の生成
    # 緩い相関を持たせる
    # -------------------------
    # 下肢機能 1-5
    leg_func_score = (
        3.2
        - 0.03 * (age - 75)
        - 0.02 * (onset_days - 25)
        - 0.8 * latent_severity
        + rng.normal(0, 0.8, size=n)
    )
    leg_func = clip_round(leg_func_score, 1, 5)

    # 体幹・基本動作 1-3
    trunk_score = (
        2.1
        - 0.02 * (age - 75)
        - 0.02 * (onset_days - 25)
        - 0.6 * latent_severity
        + 0.25 * (leg_func - 3)
        + rng.normal(0, 0.6, size=n)
    )
    trunk = clip_round(trunk_score, 1, 3)

    # 入院時歩行レベル 0-3
    gait_score = (
        1.4
        - 0.03 * (age - 75)
        - 0.02 * (onset_days - 25)
        - 0.8 * latent_severity
        + 0.55 * (leg_func - 3)
        + 0.45 * (trunk - 2)
        + rng.normal(0, 0.7, size=n)
    )
    gait_adm = clip_round(gait_score, 0, 3)

    # -------------------------
    # C. アウトカム生成
    # 退院時歩行自立（0/1）
    # -------------------------
    # 主効果 + 潜在ノイズ
    logit = (
        -1.0
        - 0.045 * (age - 75)
        - 0.025 * (onset_days - 25)
        + 1.15 * gait_adm
        + 0.60 * leg_func
        + 0.85 * trunk
        - 0.50 * latent_severity
        + rng.normal(0, 0.8, size=n)
    )

    p = 1 / (1 + np.exp(-logit))
    outcome = rng.binomial(1, p, size=n)

    # -------------------------
    # D. 観測ノイズ
    # -------------------------
    # 1) 測定誤差: 7%の症例で順序尺度を±1ずらす
    def add_measurement_noise(arr, min_value, max_value, noise_rate=0.07):
        arr = arr.copy()
        mask = rng.random(n) < noise_rate
        shift = rng.choice([-1, 1], size=n)
        arr[mask] = np.clip(arr[mask] + shift[mask], min_value, max_value)
        return arr

    gait_adm = add_measurement_noise(gait_adm, 0, 3, noise_rate=0.07)
    leg_func = add_measurement_noise(leg_func, 1, 5, noise_rate=0.07)
    trunk = add_measurement_noise(trunk, 1, 3, noise_rate=0.07)

    # 2) ラベル反転: 4%
    flip_mask = rng.random(n) < 0.04
    outcome[flip_mask] = 1 - outcome[flip_mask]

    # 3) 欠損: onset_days, leg_func, trunk に各4%
    def add_missing(arr, missing_rate=0.04):
        arr = arr.astype(float).copy()
        mask = rng.random(n) < missing_rate
        arr[mask] = np.nan
        return arr

    onset_days = add_missing(onset_days, missing_rate=0.04)
    leg_func = add_missing(leg_func, missing_rate=0.04)
    trunk = add_missing(trunk, missing_rate=0.04)

    # DataFrame化
    df = pd.DataFrame(
        {
            "age": age,
            "onset_days": onset_days,
            "gait_adm": gait_adm,
            "leg_func": leg_func,
            "trunk": trunk,
            "independent_walking_discharge": outcome,
        }
    )

    return df


# =========================
# 2. データ確認
# =========================
def summarize_data(df):
    print("\n=== 先頭5行 ===")
    print(df.head())

    print("\n=== 欠損数 ===")
    print(df.isna().sum())

    print("\n=== 記述統計 ===")
    print(df.describe(include="all"))

    outcome_rate = df["independent_walking_discharge"].mean()
    print(f"\n退院時歩行自立率: {outcome_rate:.3f}")


# =========================
# 3. 学習・評価
# =========================
def train_and_evaluate(df):
    feature_cols = ["age", "onset_days", "gait_adm", "leg_func", "trunk"]
    target_col = "independent_walking_discharge"

    X = df[feature_cols]
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y,
    )

    # ロジスティック回帰
    logistic_model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )

    logistic_model.fit(X_train, y_train)
    y_prob_lr = logistic_model.predict_proba(X_test)[:, 1]
    y_pred_lr = (y_prob_lr >= 0.5).astype(int)

    auc_lr = roc_auc_score(y_test, y_prob_lr)
    brier_lr = brier_score_loss(y_test, y_prob_lr)
    cm_lr = confusion_matrix(y_test, y_pred_lr)

    print("\n==============================")
    print("ロジスティック回帰")
    print("==============================")
    print(f"AUROC      : {auc_lr:.3f}")
    print(f"Brier score: {brier_lr:.3f}")
    print("Confusion Matrix:")
    print(cm_lr)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred_lr, digits=3))

    # 決定木
    tree_model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("model", DecisionTreeClassifier(max_depth=4, min_samples_leaf=10, random_state=42)),
        ]
    )

    tree_model.fit(X_train, y_train)
    y_prob_tree = tree_model.predict_proba(X_test)[:, 1]
    y_pred_tree = (y_prob_tree >= 0.5).astype(int)

    auc_tree = roc_auc_score(y_test, y_prob_tree)
    brier_tree = brier_score_loss(y_test, y_prob_tree)
    cm_tree = confusion_matrix(y_test, y_pred_tree)

    print("\n==============================")
    print("決定木")
    print("==============================")
    print(f"AUROC      : {auc_tree:.3f}")
    print(f"Brier score: {brier_tree:.3f}")
    print("Confusion Matrix:")
    print(cm_tree)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred_tree, digits=3))

    # 係数確認
    lr_coef = logistic_model.named_steps["model"].coef_[0]
    coef_df = pd.DataFrame(
        {
            "feature": feature_cols,
            "coefficient": lr_coef,
        }
    ).sort_values("coefficient", ascending=False)

    print("\n=== ロジスティック回帰 係数（標準化後） ===")
    print(coef_df)

    # -------------------------
    # 可視化
    # -------------------------
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))

    # 1. ROC
    RocCurveDisplay.from_predictions(y_test, y_prob_lr, ax=axes[0, 0], name="Logistic")
    axes[0, 0].set_title("ROC Curve - Logistic")

    RocCurveDisplay.from_predictions(y_test, y_prob_tree, ax=axes[0, 1], name="Decision Tree")
    axes[0, 1].set_title("ROC Curve - Tree")

    # 2. Confusion Matrix
    ConfusionMatrixDisplay.from_predictions(y_test, y_pred_lr, ax=axes[0, 2])
    axes[0, 2].set_title("Confusion Matrix - Logistic")

    # 3. Calibration
    CalibrationDisplay.from_predictions(y_test, y_prob_lr, n_bins=6, ax=axes[1, 0], name="Logistic")
    axes[1, 0].set_title("Calibration - Logistic")

    CalibrationDisplay.from_predictions(y_test, y_prob_tree, n_bins=6, ax=axes[1, 1], name="Decision Tree")
    axes[1, 1].set_title("Calibration - Tree")

    # 4. Feature importance (決定木)
    tree_clf = tree_model.named_steps["model"]
    importances = tree_clf.feature_importances_
    imp_df = pd.DataFrame(
        {"feature": feature_cols, "importance": importances}
    ).sort_values("importance", ascending=True)

    axes[1, 2].barh(imp_df["feature"], imp_df["importance"])
    axes[1, 2].set_title("Feature Importance - Tree")
    axes[1, 2].set_xlabel("Importance")

    plt.tight_layout()
    plt.savefig("model_evaluation.png", dpi=150)
    plt.show()

    # 決定木の図
    plt.figure(figsize=(14, 8))
    plot_tree(
        tree_clf,
        feature_names=feature_cols,
        class_names=["non-independent", "independent"],
        filled=True,
        rounded=True,
        fontsize=9,
    )
    plt.title("Decision Tree")
    plt.tight_layout()
    plt.savefig("decision_tree.png", dpi=150)
    plt.show()

    return logistic_model, tree_model


# =========================
# 4. 単一症例の予測
# =========================
def predict_single_case(model):
    # サンプル症例
    sample = pd.DataFrame(
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

    prob = model.predict_proba(sample)[0, 1]
    pred = int(prob >= 0.5)

    print("\n=== 単一症例予測 ===")
    print(sample)
    print(f"歩行自立確率: {prob:.3f}")
    print(f"予測ラベル  : {pred} (1=自立, 0=非自立)")


# =========================
# 5. main
# =========================
def main():
    df = pd.read_csv("dummy_prognosis_data.csv")

    # CSV保存
    #df.to_csv("dummy_prognosis_data.csv", index=False)
    #print("dummy_prognosis_data.csv を保存しました。")

    summarize_data(df)

    logistic_model, tree_model = train_and_evaluate(df)

    joblib.dump(logistic_model, "logistic_model.joblib")
    joblib.dump(tree_model, "tree_model.joblib")
    print("学習済みモデルを保存しました。")

    predict_single_case(logistic_model)


if __name__ == "__main__":
    main()
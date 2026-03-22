import pandas as pd
import matplotlib.pyplot as plt
import joblib
import json
from pathlib import Path

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


FEATURE_COLUMNS = ["age", "onset_days", "fac_adm", "fma_le_adm", "tis_adm"]
TARGET_COLUMN = "independent_walking_discharge"
MAX_FAC_ADMISSION = 3
DATASET_PATH = Path("dummy_prognosis_data.csv")
LOGISTIC_MODEL_PATH = Path("logistic_model.joblib")
TREE_MODEL_PATH = Path("tree_model.joblib")
METRICS_PATH = Path("model_metrics.json")


# =========================
# 1. データ確認
# =========================
def summarize_data(df):
    print(f"\n=== デモ対象 ===\n入院時FAC 0-{MAX_FAC_ADMISSION}")
    print(f"対象症例数: {len(df)}")

    print("\n=== 先頭5行 ===")
    print(df.head())

    print("\n=== 欠損数 ===")
    print(df.isna().sum())

    print("\n=== 記述統計 ===")
    print(df.describe(include="all"))

    outcome_rate = df[TARGET_COLUMN].mean()
    print(f"\n退院時歩行自立率: {outcome_rate:.3f}")

    print("\n=== FAC入院時別 自立率 ===")
    print(df.groupby("fac_adm")[TARGET_COLUMN].agg(["count", "mean"]))


# =========================
# 2. 学習・評価
# =========================
def train_and_evaluate(df):
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

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
            "feature": FEATURE_COLUMNS,
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
        {"feature": FEATURE_COLUMNS, "importance": importances}
    ).sort_values("importance", ascending=True)

    axes[1, 2].barh(imp_df["feature"], imp_df["importance"])
    axes[1, 2].set_title("Feature Importance - Tree")
    axes[1, 2].set_xlabel("Importance")

    plt.tight_layout()
    plt.savefig("model_evaluation.png", dpi=150)
    plt.close(fig)

    # 決定木の図
    fig_tree, ax_tree = plt.subplots(figsize=(14, 8))
    plot_tree(
        tree_clf,
        feature_names=FEATURE_COLUMNS,
        class_names=["non-independent", "independent"],
        filled=True,
        rounded=True,
        fontsize=9,
        ax=ax_tree,
    )
    ax_tree.set_title("Decision Tree")
    fig_tree.tight_layout()
    fig_tree.savefig("decision_tree.png", dpi=150)
    plt.close(fig_tree)

    metrics = {
        "cohort": f"入院時FAC 0-{MAX_FAC_ADMISSION}",
        "dataset_size": int(len(df)),
        "outcome_rate": float(y.mean()),
        "fac_distribution": {
            str(int(index)): {
                "count": int(row["count"]),
                "mean": float(row["mean"]),
            }
            for index, row in df.groupby("fac_adm")[TARGET_COLUMN].agg(["count", "mean"]).iterrows()
        },
        "models": {
            "logistic": {
                "auroc": float(auc_lr),
                "brier": float(brier_lr),
                "accuracy": float((y_pred_lr == y_test).mean()),
                "confusion_matrix": cm_lr.tolist(),
            },
            "tree": {
                "auroc": float(auc_tree),
                "brier": float(brier_tree),
                "accuracy": float((y_pred_tree == y_test).mean()),
                "confusion_matrix": cm_tree.tolist(),
            },
        },
        "feature_coefficients": {
            row["feature"]: float(row["coefficient"])
            for _, row in coef_df.iterrows()
        },
    }

    return logistic_model, tree_model, metrics


# =========================
# 3. main
# =========================
def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            "dummy_prognosis_data.csv が見つかりません。"
            " 先に `python generate_dummy_data.py` を実行してください。"
        )

    df = pd.read_csv(DATASET_PATH)
    df = df[df["fac_adm"] <= MAX_FAC_ADMISSION].copy()

    if df.empty:
        raise ValueError("FAC 0-3 の症例がありません。ダミーデータ生成条件を確認してください。")

    summarize_data(df)

    logistic_model, tree_model, metrics = train_and_evaluate(df)

    joblib.dump(logistic_model, LOGISTIC_MODEL_PATH)
    joblib.dump(tree_model, TREE_MODEL_PATH)
    METRICS_PATH.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("\n学習済みモデルを保存しました。")
    print(f"- {LOGISTIC_MODEL_PATH}")
    print(f"- {TREE_MODEL_PATH}")
    print(f"- {METRICS_PATH}")
    print("評価図を保存しました。")
    print("- model_evaluation.png")
    print("- decision_tree.png")


if __name__ == "__main__":
    main()

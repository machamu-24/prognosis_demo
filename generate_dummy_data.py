import argparse

import numpy as np
import pandas as pd


FEATURE_COLUMNS = ["age", "onset_days", "fac_adm", "fma_le_adm", "tis_adm"]
TARGET_COLUMN = "independent_walking_discharge"
MAX_FAC_ADMISSION = 3


def clip_round(values, min_value, max_value):
    values = np.rint(values).astype(int)
    return np.clip(values, min_value, max_value)


def continuous_to_fac(values, max_level=5):
    bins = [0.5, 1.5, 2.5, 3.5, 4.5]
    fac_values = np.digitize(values, bins=bins)
    return np.clip(fac_values, 0, max_level)


def add_measurement_noise(rng, values, min_value, max_value, noise_rate):
    noisy_values = values.copy()
    shift_mask = rng.random(values.size) < noise_rate
    shift = rng.choice([-1, 1], size=values.size)
    noisy_values[shift_mask] = np.clip(
        noisy_values[shift_mask] + shift[shift_mask],
        min_value,
        max_value,
    )
    return noisy_values


def add_groupwise_missing(rng, values, severity_code, base_rate, severe_bonus):
    values_with_missing = values.astype(float).copy()
    missing_rate = base_rate + severe_bonus * (severity_code / 2.0)
    missing_mask = rng.random(values.size) < missing_rate
    values_with_missing[missing_mask] = np.nan
    return values_with_missing


def summarize_generated_data(df):
    print("\n=== 先頭5行 ===")
    print(df.head())

    print("\n=== 欠損数 ===")
    print(df.isna().sum())

    print("\n=== 記述統計 ===")
    print(df.describe(include="all"))

    outcome_rate = df[TARGET_COLUMN].mean()
    print(f"\n退院時歩行自立率: {outcome_rate:.3f}")
    print(f"対象コホート: 入院時FAC 0-{MAX_FAC_ADMISSION}")

    print("\n=== FAC入院時別 自立率 ===")
    print(df.groupby("fac_adm")[TARGET_COLUMN].agg(["count", "mean"]))


def generate_dummy_data(n=300, random_state=42):
    rng = np.random.default_rng(random_state)

    clinical_profile = rng.choice(
        ["mild", "moderate", "severe"],
        size=n,
        p=[0.25, 0.50, 0.25],
    )
    severity_code = np.select(
        [clinical_profile == "mild", clinical_profile == "moderate", clinical_profile == "severe"],
        [0.0, 1.0, 2.0],
    )

    rehab_potential = rng.normal(0.0, 0.9, size=n)
    medical_complexity = rng.normal(0.0, 1.0, size=n)
    discharge_complication = rng.binomial(
        1,
        np.clip(0.10 + 0.08 * (severity_code / 2.0), 0.0, 0.35),
        size=n,
    )
    social_support = rng.normal(0.0, 0.8, size=n)

    age_mean = np.select(
        [clinical_profile == "mild", clinical_profile == "moderate", clinical_profile == "severe"],
        [66.0, 75.0, 84.0],
    )
    age = rng.normal(age_mean + 1.0 * medical_complexity, 6.0, size=n)
    age = np.clip(age, 50, 95).round(0)

    onset_mean = np.select(
        [clinical_profile == "mild", clinical_profile == "moderate", clinical_profile == "severe"],
        [13.0, 25.0, 40.0],
    )
    onset_days = rng.normal(onset_mean + 2.0 * medical_complexity, 7.5, size=n)
    onset_days = np.clip(onset_days, 7, 75).round(0)

    fma_le_score = (
        28.0
        - 9.0 * severity_code
        - 0.22 * (age - 75)
        - 0.16 * (onset_days - 25)
        + 3.2 * rehab_potential
        - 1.8 * medical_complexity
        + rng.normal(0, 4.2, size=n)
    )
    fma_le_adm = clip_round(fma_le_score, 0, 34)

    tis_score = (
        17.0
        - 4.8 * severity_code
        - 0.12 * (age - 75)
        - 0.10 * (onset_days - 25)
        + 0.15 * (fma_le_adm - 17)
        + 1.9 * rehab_potential
        - 0.9 * medical_complexity
        + rng.normal(0, 2.8, size=n)
    )
    tis_adm = clip_round(tis_score, 0, 23)

    fac_adm_score = (
        -0.95
        - 0.50 * severity_code
        - 0.025 * (age - 75)
        - 0.025 * (onset_days - 25)
        + 0.075 * fma_le_adm
        + 0.060 * tis_adm
        + 0.40 * rehab_potential
        - 0.15 * medical_complexity
        + rng.normal(0, 0.95, size=n)
    )
    fac_adm = continuous_to_fac(fac_adm_score, max_level=MAX_FAC_ADMISSION)

    required_gain = 4 - fac_adm
    recovery_logit = (
        1.35
        - 1.02 * required_gain
        - 0.085 * (age - 75)
        - 0.045 * (onset_days - 25)
        + 0.070 * (fma_le_adm - 17)
        + 0.095 * (tis_adm - 11)
        + 0.24 * rehab_potential
        - 0.22 * medical_complexity
        - 0.15 * severity_code
        - 0.75 * discharge_complication
        + 0.10 * social_support
        + 0.02 * np.maximum(fma_le_adm - 20, 0) * (3 - fac_adm) / 3.0
        + 0.03 * np.maximum(tis_adm - 12, 0) * (3 - fac_adm) / 3.0
        + rng.normal(0, 0.40, size=n)
    )
    recovery_probability = 1 / (1 + np.exp(-recovery_logit))
    outcome = rng.binomial(1, recovery_probability, size=n)

    fac_adm = add_measurement_noise(
        rng,
        fac_adm,
        0,
        MAX_FAC_ADMISSION,
        noise_rate=0.05,
    )
    fma_le_adm = add_measurement_noise(rng, fma_le_adm, 0, 34, noise_rate=0.05)
    tis_adm = add_measurement_noise(rng, tis_adm, 0, 23, noise_rate=0.05)

    flip_mask = rng.random(n) < 0.02
    outcome[flip_mask] = 1 - outcome[flip_mask]

    onset_days = add_groupwise_missing(
        rng,
        onset_days,
        severity_code,
        base_rate=0.02,
        severe_bonus=0.03,
    )
    fma_le_adm = add_groupwise_missing(
        rng,
        fma_le_adm,
        severity_code,
        base_rate=0.02,
        severe_bonus=0.04,
    )
    tis_adm = add_groupwise_missing(
        rng,
        tis_adm,
        severity_code,
        base_rate=0.02,
        severe_bonus=0.04,
    )

    return pd.DataFrame(
        {
            "age": age,
            "onset_days": onset_days,
            "fac_adm": fac_adm,
            "fma_le_adm": fma_le_adm,
            "tis_adm": tis_adm,
            TARGET_COLUMN: outcome,
        }
    )


def parse_args():
    parser = argparse.ArgumentParser(description="予後予測用のダミーデータを生成します。")
    parser.add_argument("--n", type=int, default=300, help="生成する症例数")
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="乱数シード",
    )
    parser.add_argument(
        "--output",
        default="dummy_prognosis_data.csv",
        help="出力先CSVファイル名",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    df = generate_dummy_data(n=args.n, random_state=args.random_state)
    df.to_csv(args.output, index=False)
    print(f"{args.output} を保存しました。")
    summarize_generated_data(df)


if __name__ == "__main__":
    main()

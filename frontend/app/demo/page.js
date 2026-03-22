"use client";

import { useEffect, useState } from "react";

import { ComparisonPanel } from "../../components/comparison-panel";
import { PatientForm } from "../../components/patient-form";
import { PredictionPanel } from "../../components/prediction-panel";
import { fetchMetadata, predictCase } from "../../lib/api";


const FALLBACK_PRIMARY = {
  age: 72,
  onset_days: 20,
  fac_adm: 2,
  fma_le_adm: 21,
  tis_adm: 14
};
const FALLBACK_COMPARE = {
  age: 64,
  onset_days: 14,
  fac_adm: 3,
  fma_le_adm: 29,
  tis_adm: 20
};

const COMPARISON_PRESETS = [
  {
    id: "baseline-vs-promising",
    label: "境界症例 vs 改善余地あり",
    description: "改善余地のある症例との差分をそのまま説明できます。",
    leftSample: "borderline",
    rightSample: "promising"
  },
  {
    id: "frail-vs-borderline",
    label: "高齢・重症寄り vs 境界症例",
    description: "年齢と機能低下が予測をどう下げるかを見せる組み合わせです。",
    leftSample: "frail",
    rightSample: "borderline"
  }
];


export default function DemoPage() {
  const [mode, setMode] = useState("single");
  const [metadata, setMetadata] = useState(null);
  const [primaryCase, setPrimaryCase] = useState(FALLBACK_PRIMARY);
  const [secondaryCase, setSecondaryCase] = useState(FALLBACK_COMPARE);
  const [primaryPrediction, setPrimaryPrediction] = useState(null);
  const [secondaryPrediction, setSecondaryPrediction] = useState(null);
  const [loadingState, setLoadingState] = useState("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    fetchMetadata()
      .then((data) => {
        if (cancelled) {
          return;
        }
        setMetadata(data);

        const boundarySample = data.samples.find((sample) => sample.id === "borderline");
        const promisingSample = data.samples.find((sample) => sample.id === "promising");

        if (boundarySample) {
          setPrimaryCase(boundarySample.values);
        }
        if (promisingSample) {
          setSecondaryCase(promisingSample.values);
        }
      })
      .catch((loadError) => {
        if (!cancelled) {
          setError(loadError.message);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  async function runSinglePrediction() {
    setError("");
    setLoadingState("single");

    try {
      const prediction = await predictCase(primaryCase);
      setPrimaryPrediction(prediction);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoadingState("idle");
    }
  }

  async function runComparisonPrediction() {
    setError("");
    setLoadingState("compare");

    try {
      const [left, right] = await Promise.all([
        predictCase(primaryCase),
        predictCase(secondaryCase)
      ]);
      setPrimaryPrediction(left);
      setSecondaryPrediction(right);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoadingState("idle");
    }
  }

  function updateCase(setter, key, value) {
    setter((current) => ({
      ...current,
      [key]: Number(value)
    }));
  }

  const samples = metadata?.samples || [];

  function loadComparisonPreset(leftId, rightId) {
    if (!metadata?.samples) {
      return;
    }

    const left = metadata.samples.find((sample) => sample.id === leftId);
    const right = metadata.samples.find((sample) => sample.id === rightId);

    if (left) {
      setPrimaryCase(left.values);
    }
    if (right) {
      setSecondaryCase(right.values);
    }
  }

  return (
    <main className="shell shell--page">
      <section className="page-head page-head--demo">
        <p className="eyebrow">Live Demo</p>
        <h1>提案デモとして伝わる流れに整える</h1>
        <p className="muted">
          まず主モデルの予測と根拠を示し、その後に症例比較で介入の意味を見せます。
          補助モデルは折りたたんで補足に回します。
        </p>
      </section>

      <section className="demo-story">
        <article className="story-card">
          <span>1</span>
          <strong>症例を入力する</strong>
          <p>臨床で使う FAC / FMA-LE / TIS をそのまま使います。</p>
        </article>
        <article className="story-card">
          <span>2</span>
          <strong>主モデルで判断する</strong>
          <p>ロジスティック回帰を主表示に固定し、判断根拠も同時に提示します。</p>
        </article>
        <article className="story-card">
          <span>3</span>
          <strong>比較で介入余地を示す</strong>
          <p>症例比較モードで、改善前後や別ケースの差を見せられます。</p>
        </article>
      </section>

      <section className="mode-switch">
        <button
          className={`mode-switch__button ${mode === "single" ? "is-active" : ""}`}
          type="button"
          onClick={() => setMode("single")}
        >
          単一症例デモ
        </button>
        <button
          className={`mode-switch__button ${mode === "compare" ? "is-active" : ""}`}
          type="button"
          onClick={() => setMode("compare")}
        >
          症例比較モード
        </button>
      </section>

      {error ? <p className="status status--error">{error}</p> : null}

      {mode === "single" ? (
        <section className="demo-grid">
          <PatientForm
            actionLabel="主モデルで予測する"
            disabled={loadingState === "single"}
            metadata={metadata}
            mode="single"
            onChange={(key, value) => updateCase(setPrimaryCase, key, value)}
            onLoadSample={(values) => setPrimaryCase(values)}
            onSubmit={runSinglePrediction}
            samples={samples}
            subtitle="ロジスティック回帰を主表示にした提案デモです。"
            title="Primary Case"
            values={primaryCase}
          />
          <PredictionPanel prediction={primaryPrediction} />
        </section>
      ) : (
        <section className="compare-layout">
          <div className="compare-layout__forms">
            <section className="panel panel--soft">
              <div className="section-head">
                <div>
                  <p className="eyebrow">Preset Pair</p>
                  <h3>プレゼンしやすい組み合わせを選ぶ</h3>
                </div>
              </div>
              <div className="preset-grid">
                {COMPARISON_PRESETS.map((preset) => (
                  <button
                    className="preset-card"
                    key={preset.id}
                    type="button"
                    onClick={() => loadComparisonPreset(preset.leftSample, preset.rightSample)}
                  >
                    <strong>{preset.label}</strong>
                    <span>{preset.description}</span>
                  </button>
                ))}
              </div>
            </section>

            <PatientForm
              actionLabel="Case A を更新"
              disabled={loadingState === "compare"}
              metadata={metadata}
              mode="compare"
              onChange={(key, value) => updateCase(setPrimaryCase, key, value)}
              onLoadSample={(values) => setPrimaryCase(values)}
              onSubmit={runComparisonPrediction}
              samples={samples}
              showSubmitButton={false}
              subtitle="ベース症例"
              title="Case A"
              values={primaryCase}
            />
            <PatientForm
              actionLabel="Case B を更新"
              disabled={loadingState === "compare"}
              metadata={metadata}
              mode="compare"
              onChange={(key, value) => updateCase(setSecondaryCase, key, value)}
              onLoadSample={(values) => setSecondaryCase(values)}
              onSubmit={runComparisonPrediction}
              samples={samples}
              showSubmitButton={false}
              subtitle="比較対象症例"
              title="Case B"
              values={secondaryCase}
            />
            <div className="button-row compare-layout__cta">
              <button
                className="button button--primary"
                disabled={loadingState === "compare"}
                type="button"
                onClick={runComparisonPrediction}
              >
                {loadingState === "compare" ? "比較中..." : "2症例を比較する"}
              </button>
              <p className="muted compare-layout__note">
                ロジスティック回帰の差分を主メッセージにし、必要なときだけ補助モデルへ触れます。
              </p>
            </div>
          </div>
          <ComparisonPanel
            leftLabel="Case A"
            leftPrediction={primaryPrediction}
            rightLabel="Case B"
            rightPrediction={secondaryPrediction}
          />
        </section>
      )}
    </main>
  );
}

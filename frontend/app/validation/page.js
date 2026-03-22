"use client";

import { useEffect, useState } from "react";

import { fetchMetrics, getApiBase } from "../../lib/api";


function MetricCard({ label, value, tone = "default" }) {
  return (
    <article className={`metric-card metric-card--${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function DatasetStat({ label, value }) {
  return (
    <article className="dataset-stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}


export default function ValidationPage() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    fetchMetrics()
      .then((data) => {
        if (!cancelled) {
          setMetrics(data);
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

  const apiBase = getApiBase();

  return (
    <main className="shell shell--page">
      <section className="page-head">
        <p className="eyebrow">モデル検証</p>
        <h1>PoC としての妥当性を、誠実に見せる</h1>
        <p className="muted">
          主モデルはロジスティック回帰です。ここでは対象コホート、メトリクス、synthetic data
          の限界を明示し、提案としての信頼性を担保します。
        </p>
      </section>

      <section className="validation-banner">
        <div>
          <p className="eyebrow" style={{ color: "var(--warning)" }}>注意事項</p>
          <h3>本デモは synthetic data に基づく PoC です。</h3>
        </div>
        <p>
          実データによる外部妥当性検証は未実施です。提案デモとしては、説明可能性と運用イメージの提示を主目的としています。
        </p>
      </section>

      {error ? <p className="status status--error">{error}</p> : null}

      {metrics ? (
        <>
          <section className="metric-grid">
            <MetricCard label="対象コホート" value={metrics.cohort} />
            <MetricCard label="症例数" value={String(metrics.dataset_size)} />
            <MetricCard label="全体自立率" value={metrics.outcome_rate.toFixed(3)} />
            <MetricCard
              label="主モデル AUROC"
              tone="highlight"
              value={metrics.models.logistic.auroc.toFixed(3)}
            />
          </section>

          {metrics.dataset_overview ? (
            <section className="dataset-layout">
              <article className="panel panel--soft">
                <div className="section-head">
                  <div>
                    <p className="eyebrow">データセット概要</p>
                    <h3>今回学習に使ったダミーデータ</h3>
                  </div>
                </div>
                <p className="muted">
                  実患者データではなく、入院時 FAC 0-3 の患者を想定した synthetic data です。
                  プレゼンでは「何を模していて、どこに揺らぎを入れたか」をここで説明できます。
                </p>
                <div className="dataset-stat-grid">
                  <DatasetStat
                    label="年齢"
                    value={`${metrics.dataset_overview.age_mean.toFixed(1)} ± ${metrics.dataset_overview.age_sd.toFixed(1)} 歳`}
                  />
                  <DatasetStat
                    label="発症から入院まで"
                    value={`${metrics.dataset_overview.onset_days_mean.toFixed(1)} ± ${metrics.dataset_overview.onset_days_sd.toFixed(1)} 日`}
                  />
                  <DatasetStat
                    label="FMA-LE 平均"
                    value={metrics.dataset_overview.fma_le_mean.toFixed(1)}
                  />
                  <DatasetStat
                    label="TIS 平均"
                    value={metrics.dataset_overview.tis_mean.toFixed(1)}
                  />
                </div>
              </article>

              <article className="panel panel--soft">
                <div className="section-head">
                  <div>
                    <p className="eyebrow">生成ロジック</p>
                    <h3>どう作ったデータか</h3>
                  </div>
                </div>
                <ul className="dataset-note-list">
                  {metrics.dataset_overview.notes.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
                <div className="missing-grid">
                  {Object.entries(metrics.dataset_overview.missing).map(([key, value]) => (
                    <article className="missing-card" key={key}>
                      <span>{key}</span>
                      <strong>{value} 件</strong>
                    </article>
                  ))}
                </div>
              </article>
            </section>
          ) : null}

          <section className="validation-layout">
            <article className="panel panel--soft">
              <div className="section-head">
                <div>
                  <p className="eyebrow">主モデル</p>
                  <h3>ロジスティック回帰を中心に説明する</h3>
                </div>
              </div>
              <div className="compare-table">
                <div className="compare-row compare-row--triple compare-row--head">
                  <span>指標</span>
                  <span>値</span>
                  <span>解釈</span>
                </div>
                <div className="compare-row compare-row--triple">
                  <span>AUROC</span>
                  <span>{metrics.models.logistic.auroc.toFixed(3)}</span>
                  <span>識別性能の基礎指標</span>
                </div>
                <div className="compare-row compare-row--triple">
                  <span>Brier</span>
                  <span>{metrics.models.logistic.brier.toFixed(3)}</span>
                  <span>確率予測の妥当性</span>
                </div>
                <div className="compare-row compare-row--triple">
                  <span>Accuracy</span>
                  <span>{metrics.models.logistic.accuracy.toFixed(3)}</span>
                  <span>二値予測の正答率</span>
                </div>
              </div>
            </article>

            <article className="panel panel--soft">
              <div className="section-head">
                <div>
                  <p className="eyebrow">コホート分布</p>
                  <h3>FAC別の自立率</h3>
                </div>
              </div>
              <div className="fac-ladder">
                {Object.entries(metrics.fac_distribution).map(([fac, value]) => (
                  <div className="fac-ladder__row" key={fac}>
                    <div className="fac-ladder__copy">
                      <strong>FAC {fac}</strong>
                      <span>{value.count} 例</span>
                    </div>
                    <div className="fac-ladder__track">
                      <div
                        className="fac-ladder__bar"
                        style={{ width: `${value.mean * 100}%` }}
                      />
                    </div>
                    <div className="fac-ladder__value">{(value.mean * 100).toFixed(1)}%</div>
                  </div>
                ))}
              </div>
            </article>
          </section>

          <section className="panel panel--soft" style={{ marginBottom: "24px" }}>
            <div className="section-head">
              <div>
                <p className="eyebrow">モデル比較</p>
                <h3>補助モデルは比較にとどめる</h3>
              </div>
            </div>
            <div className="compare-table">
              <div className="compare-row compare-row--quad compare-row--head">
                <span>モデル</span>
                <span>AUROC</span>
                <span>Brier</span>
                <span>Accuracy</span>
              </div>
              {Object.entries(metrics.models).map(([name, model]) => (
                <div className="compare-row compare-row--quad" key={name}>
                  <span>{name === "logistic" ? "ロジスティック回帰" : "決定木"}</span>
                  <span>{model.auroc.toFixed(3)}</span>
                  <span>{model.brier.toFixed(3)}</span>
                  <span>{model.accuracy.toFixed(3)}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="visual-grid">
            <article className="panel panel--visual">
              <p className="eyebrow">可視化</p>
              <h3>評価サマリー</h3>
              <img alt="model evaluation" src={`${apiBase}/artifacts/model_evaluation.png`} />
            </article>
            <article className="panel panel--visual">
              <p className="eyebrow">可視化</p>
              <h3>決定木</h3>
              <img alt="decision tree" src={`${apiBase}/artifacts/decision_tree.png`} />
            </article>
          </section>
        </>
      ) : (
        <section className="panel panel--placeholder">
          <p className="muted">メトリクスを読み込み中です。</p>
        </section>
      )}
    </main>
  );
}

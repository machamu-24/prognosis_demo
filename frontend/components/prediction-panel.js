import { ExplanationBars } from "./explanation-bars";


function narrative(probability) {
  if (probability < 0.3) {
    return "現時点では非自立寄りです。集中的な介入や阻害因子の整理が必要なレンジです。";
  }
  if (probability < 0.7) {
    return "境界症例です。機能改善や介入条件の変化で転ぶ可能性があるレンジです。";
  }
  return "自立方向に傾いています。退院時の歩行自立が比較的見込みやすいレンジです。";
}


function ProbabilityBar({ probability }) {
  const pct = (probability * 100).toFixed(1);
  const hue = probability < 0.3 ? 0 : probability < 0.7 ? 38 : 152;
  const color = `hsl(${hue}, 72%, 42%)`;

  return (
    <div style={{ marginTop: "12px" }}>
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "baseline",
        marginBottom: "6px"
      }}>
        <span style={{ fontSize: "0.75rem", color: "rgba(255,255,255,0.65)" }}>歩行自立確率</span>
        <span style={{ fontSize: "0.75rem", color: "rgba(255,255,255,0.65)" }}>100%</span>
      </div>
      <div style={{
        height: "10px",
        borderRadius: "999px",
        background: "rgba(255,255,255,0.15)",
        overflow: "hidden"
      }}>
        <div style={{
          height: "100%",
          width: `${pct}%`,
          borderRadius: "999px",
          background: color,
          transition: "width 600ms cubic-bezier(0.4, 0, 0.2, 1)"
        }} />
      </div>
    </div>
  );
}


function ProbabilitySummary({ result }) {
  return (
    <article className="result-hero">
      <p className="eyebrow" style={{ color: "rgba(255,255,255,0.6)" }}>主モデル（ロジスティック回帰）</p>
      <div className="result-hero__value">{(result.probability * 100).toFixed(1)}%</div>
      <div className="result-hero__meta">
        <span className={`pill pill--${result.band.tone}`}>{result.band.label}</span>
        <span style={{ fontSize: "0.875rem" }}>{result.prediction === 1 ? "退院時歩行自立を予測" : "退院時非自立を予測"}</span>
      </div>
      <ProbabilityBar probability={result.probability} />
      <p className="result-hero__narrative">{narrative(result.probability)}</p>
    </article>
  );
}

function DriverSummary({ explanation }) {
  if (!explanation?.items?.length) {
    return null;
  }

  const strongestPositive = explanation.items.find((item) => item.contribution > 0);
  const strongestNegative = explanation.items.find((item) => item.contribution < 0);

  return (
    <section className="panel panel--soft">
      <div className="section-head">
        <div>
          <p className="eyebrow">判断の要点</p>
          <h3>この症例で何を説明するか</h3>
        </div>
      </div>
      <div className="driver-summary">
        <article className="driver-summary__card driver-summary__card--positive">
          <span>自立方向の主因</span>
          <strong>{strongestPositive ? strongestPositive.label : "該当なし"}</strong>
          <p>
            {strongestPositive
              ? `寄与は +${strongestPositive.contribution.toFixed(3)}。現状ではこの項目が最も予測を押し上げています。`
              : "自立方向へ強く押し上げる項目は目立っていません。"}
          </p>
        </article>
        <article className="driver-summary__card driver-summary__card--negative">
          <span>非自立方向の主因</span>
          <strong>{strongestNegative ? strongestNegative.label : "該当なし"}</strong>
          <p>
            {strongestNegative
              ? `寄与は ${strongestNegative.contribution.toFixed(3)}。ここが主な制約因子として説明できます。`
              : "大きなマイナス寄与は現時点では目立っていません。"}
          </p>
        </article>
      </div>
    </section>
  );
}


export function PredictionPanel({ prediction }) {
  if (!prediction) {
    return (
      <section className="panel panel--placeholder">
        <div>
          <p className="eyebrow">予測結果</p>
          <h3 style={{ marginTop: "8px" }}>主モデルの予測結果</h3>
          <p className="muted" style={{ marginTop: "8px", maxWidth: "28rem" }}>
            左の入力フォームに症例データを入力し、「予測する」ボタンを押してください。
            ロジスティック回帰による確率・判定・判断根拠が表示されます。
          </p>
        </div>
      </section>
    );
  }

  return (
    <div className="stack">
      <section className="panel panel--result">
        <div className="section-head">
          <div>
            <p className="eyebrow">予測結果</p>
            <h3>ロジスティック回帰による予測</h3>
          </div>
        </div>

        <ProbabilitySummary result={prediction.logistic} />

        <div className="result-callouts">
          <div className="callout">
            <span>対象コホート</span>
            <strong>FAC 0-3</strong>
          </div>
          <div className="callout">
            <span>説明可能性</span>
            <strong>寄与を可視化</strong>
          </div>
          <div className="callout">
            <span>補助モデル</span>
            <strong>決定木で比較</strong>
          </div>
        </div>
      </section>

      <DriverSummary explanation={prediction.logistic.explanation} />

      <ExplanationBars explanation={prediction.logistic.explanation} />

      <details className="panel panel--soft comparison-disclosure">
        <summary>
          <div>
            <p className="eyebrow">補助モデル</p>
            <h3>決定木の補助比較を見る</h3>
          </div>
          <span className="comparison-disclosure__value">
            {(prediction.tree.probability * 100).toFixed(1)}%
          </span>
        </summary>
        <div className="comparison-disclosure__body">
          <p className="muted">
            決定木は比較用です。主メッセージはロジスティック回帰の結果と判断根拠で伝えます。
          </p>
          <div className="compare-table">
            <div className="compare-row compare-row--quad compare-row--head">
              <span>モデル</span>
              <span>確率</span>
              <span>判定</span>
              <span>予測</span>
            </div>
            <div className="compare-row compare-row--quad">
              <span>決定木</span>
              <span>{(prediction.tree.probability * 100).toFixed(1)}%</span>
              <span>{prediction.tree.band.label}</span>
              <span>{prediction.tree.prediction === 1 ? "自立" : "非自立"}</span>
            </div>
          </div>
        </div>
      </details>
    </div>
  );
}

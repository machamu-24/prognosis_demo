function ComparisonProbability({ label, probability }) {
  return (
    <article className="comparison-probability">
      <span>{label}</span>
      <strong>{(probability * 100).toFixed(1)}%</strong>
    </article>
  );
}


function buildContributionRows(leftExplanation, rightExplanation) {
  const rightMap = new Map(
    rightExplanation.items.map((item) => [item.feature, item])
  );

  return leftExplanation.items.map((item) => {
    const pair = rightMap.get(item.feature);
    const delta = pair.contribution - item.contribution;
    return {
      feature: item.feature,
      label: item.label,
      left: item.contribution,
      right: pair.contribution,
      delta
    };
  }).sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
}


export function ComparisonPanel({
  leftLabel = "Case A",
  leftPrediction,
  rightLabel = "Case B",
  rightPrediction
}) {
  if (!leftPrediction || !rightPrediction) {
    return (
      <section className="panel panel--placeholder">
        <div>
          <p className="eyebrow">症例比較</p>
          <h3 style={{ marginTop: "8px" }}>症例比較モード</h3>
          <p className="muted" style={{ marginTop: "8px", maxWidth: "28rem" }}>
            2つの症例を入力し「比較する」ボタンを押すと、ロジスティック回帰の確率差と主要因子の差分を比較できます。
          </p>
        </div>
      </section>
    );
  }

  const left = leftPrediction.logistic;
  const right = rightPrediction.logistic;
  const delta = right.probability - left.probability;
  const rows = buildContributionRows(left.explanation, right.explanation);
  const highlights = rows.slice(0, 3);

  return (
    <div className="stack">
      <section className="panel panel--result">
        <div className="section-head">
          <div>
            <p className="eyebrow">比較結果</p>
            <h3>ロジスティック回帰による症例比較</h3>
          </div>
        </div>

        <div className="comparison-hero">
          <ComparisonProbability label={leftLabel} probability={left.probability} />
          <article className="comparison-delta">
            <span>差分</span>
            <strong>{delta >= 0 ? "+" : ""}{(delta * 100).toFixed(1)} pt</strong>
            <p>{delta >= 0 ? `${rightLabel} の方が自立方向です。` : `${leftLabel} の方が自立方向です。`}</p>
          </article>
          <ComparisonProbability label={rightLabel} probability={right.probability} />
        </div>
      </section>

      <section className="panel panel--soft">
        <div className="section-head">
          <div>
            <p className="eyebrow">説明のポイント</p>
            <h3>差分をどう話すか</h3>
          </div>
        </div>
        <div className="comparison-highlights">
          {highlights.map((row) => (
            <article className="comparison-highlight" key={`highlight-${row.feature}`}>
              <span>{row.label}</span>
              <strong className={row.delta >= 0 ? "positive-copy" : "negative-copy"}>
                {row.delta > 0 ? "+" : ""}
                {row.delta.toFixed(3)}
              </strong>
              <p>
                {row.delta >= 0
                  ? `${rightLabel} の方がこの因子で自立方向に傾いています。`
                  : `${leftLabel} の方がこの因子で自立方向に傾いています。`}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel panel--soft">
        <div className="section-head">
          <div>
            <p className="eyebrow">因子の変化</p>
            <h3>主要因子の差分</h3>
          </div>
        </div>
        <div className="compare-table">
          <div className="compare-row compare-row--quad compare-row--head">
            <span>特徴量</span>
            <span>{leftLabel}</span>
            <span>{rightLabel}</span>
            <span>差分</span>
          </div>
          {rows.map((row) => (
            <div className="compare-row compare-row--quad" key={row.feature}>
              <span>{row.label}</span>
              <span>{row.left > 0 ? "+" : ""}{row.left.toFixed(3)}</span>
              <span>{row.right > 0 ? "+" : ""}{row.right.toFixed(3)}</span>
              <span className={row.delta >= 0 ? "positive-copy" : "negative-copy"}>
                {row.delta > 0 ? "+" : ""}
                {row.delta.toFixed(3)}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

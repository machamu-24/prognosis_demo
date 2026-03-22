export function ExplanationBars({ explanation }) {
  if (!explanation) {
    return null;
  }

  const maxMagnitude = Math.max(
    ...explanation.items.map((item) => Math.abs(item.contribution)),
    0.001
  );

  return (
    <section className="panel panel--soft">
      <div className="section-head">
        <div>
          <p className="eyebrow">判断根拠</p>
          <h3>各特徴量の寄与度</h3>
        </div>
        <div className="compact-stat">
          <span>合計 log-odds</span>
          <strong>{explanation.log_odds.toFixed(3)}</strong>
        </div>
      </div>
      <p className="muted" style={{ marginBottom: "4px" }}>
        正の寄与は自立方向、負の寄与は非自立方向を示します。切片は{" "}
        {explanation.intercept.toFixed(3)} です。
      </p>
      <div className="explanation-list">
        {explanation.items.map((item) => {
          const width = `${(Math.abs(item.contribution) / maxMagnitude) * 100}%`;
          return (
            <div className="explanation-row" key={item.feature}>
              <div className="explanation-copy">
                <strong style={{ fontSize: "0.875rem" }}>{item.label}</strong>
                <span>入力値: {item.raw_value.toFixed(1)}</span>
              </div>
              <div className="explanation-track">
                <div
                  className={`explanation-bar explanation-bar--${item.direction}`}
                  style={{ width }}
                />
              </div>
              <div className={`explanation-value explanation-value--${item.direction}`}>
                {item.contribution > 0 ? "+" : ""}
                {item.contribution.toFixed(3)}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

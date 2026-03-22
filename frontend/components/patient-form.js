"use client";

export function PatientForm({
  actionLabel,
  disabled,
  metadata,
  mode = "single",
  onChange,
  onLoadSample,
  onSubmit,
  samples = [],
  showSubmitButton = true,
  subtitle,
  title,
  values
}) {
  function handleSubmit(event) {
    event.preventDefault();
    onSubmit();
  }

  return (
    <section className={`panel patient-panel patient-panel--${mode}`}>
      <div className="section-head">
        <div>
          <p className="eyebrow">症例入力</p>
          <h3>{title}</h3>
          {subtitle ? <p className="muted patient-panel__subtitle">{subtitle}</p> : null}
        </div>
      </div>

      {samples.length > 0 ? (
        <div className="sample-row">
          {samples.map((sample) => (
            <button
              className="ghost-chip"
              key={`${title}-${sample.id}`}
              type="button"
              onClick={() => onLoadSample(sample.values)}
            >
              {sample.label}
            </button>
          ))}
        </div>
      ) : null}

      <form className="patient-form" onSubmit={handleSubmit}>
        {metadata
          ? Object.entries(metadata.features).map(([key, config]) => (
              <label className="field" key={`${title}-${key}`}>
                <div className="field__head">
                  <span>{config.label}</span>
                  <small className="field__hint">
                    {config.min} — {config.max}
                  </small>
                </div>
                <div className="field__input-row">
                  <input
                    max={config.max}
                    min={config.min}
                    step={config.step}
                    type="range"
                    value={values[key]}
                    onChange={(event) => onChange(key, event.target.value)}
                  />
                  <input
                    max={config.max}
                    min={config.min}
                    step={config.step}
                    type="number"
                    value={values[key]}
                    onChange={(event) => onChange(key, event.target.value)}
                  />
                </div>
              </label>
            ))
          : null}

        {showSubmitButton ? (
          <div className="button-row" style={{ marginTop: "8px" }}>
            <button className="button button--primary" disabled={disabled} type="submit">
              {disabled ? "予測中..." : actionLabel}
            </button>
          </div>
        ) : null}
      </form>
    </section>
  );
}

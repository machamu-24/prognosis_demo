import Link from "next/link";


export default function HomePage() {
  return (
    <main>
      <section className="hero hero--pitch">
        <div className="shell hero__grid">
          <div className="hero__copy">
            <p className="eyebrow">Proposal Demo</p>
            <h1>歩行予後予測を、説明可能なAIの体験に変える。</h1>
            <p className="hero__lead">
              FAC 0-3 の患者を対象に、退院時歩行自立を予測。数値だけでなく、
              なぜその判断に至ったかまで含めてデモできる提案用UIです。
            </p>
            <div className="button-row">
              <Link className="button button--primary" href="/demo">
                デモを始める
              </Link>
              <Link className="button button--secondary" href="/validation">
                検証結果を見る
              </Link>
            </div>
          </div>

          <div className="hero__panel panel panel--hero">
            <div className="hero-callout">
              <span>Primary Narrative</span>
              <strong>Logistic Regression First</strong>
              <p>主表示はロジスティック回帰。補助モデルは必要なときだけ比較表示します。</p>
            </div>
            <div className="hero-callout">
              <span>Clinical Inputs</span>
              <strong>FAC / FMA-LE / TIS</strong>
              <p>現場で馴染みのある尺度を、そのままデモ入力に使います。</p>
            </div>
            <div className="hero-callout">
              <span>Audience Flow</span>
              <strong>課題 → デモ → 検証</strong>
              <p>提案資料として通る導線を、1つのアプリ内にまとめています。</p>
            </div>
          </div>
        </div>
      </section>

      <section className="shell presentation-track">
        <div className="track-intro">
          <p className="eyebrow">Presentation Flow</p>
          <h2>提案デモとしての流れを最初から設計する</h2>
        </div>
        <div className="presentation-track__grid">
          <article className="track-card">
            <span>01</span>
            <h3>現場の課題を明示</h3>
            <p>経験差のある予後判断を、再現可能な支援ツールへ変える文脈で始めます。</p>
          </article>
          <article className="track-card">
            <span>02</span>
            <h3>主モデルで体験させる</h3>
            <p>症例入力から確率、判定、判断根拠までを一気に見せます。</p>
          </article>
          <article className="track-card">
            <span>03</span>
            <h3>比較で意思決定を見せる</h3>
            <p>2症例比較で、介入前後や条件差の意味を伝えられる構成にします。</p>
          </article>
          <article className="track-card">
            <span>04</span>
            <h3>検証で誠実さを担保</h3>
            <p>PoC としての検証結果と、synthetic data の限界を明示して締めます。</p>
          </article>
        </div>
      </section>

      <section className="shell feature-strip feature-strip--elevated">
        <article className="feature-card">
          <p className="eyebrow">01</p>
          <h3>予測の標準化</h3>
          <p>FAC・FMA-LE・TIS といった臨床評価を、ばらつきの少ない予測へ変換します。</p>
        </article>
        <article className="feature-card">
          <p className="eyebrow">02</p>
          <h3>介入判断の支援</h3>
          <p>境界症例で何が改善余地で、何が制約かを直感的に説明できます。</p>
        </article>
        <article className="feature-card">
          <p className="eyebrow">03</p>
          <h3>説明可能な推論</h3>
          <p>予測確率だけでなく、項目ごとの寄与までその場で確認できます。</p>
        </article>
      </section>
    </main>
  );
}

const signals = [
  {
    title: "Intelligence platform initializing",
    description:
      "The system foundation is ready. Source collection and intelligence processing will be added in later phases.",
    status: "SYSTEM",
  },
  {
    title: "Current scope",
    description:
      "Pig and cattle/calf intelligence across Europe, China, the United States and relevant global sources.",
    status: "SCOPE",
  },
  {
    title: "Next phase",
    description:
      "Backend and database foundation, followed by source registry and collection.",
    status: "ROADMAP",
  },
];

export default function Home() {
  return (
    <main className="page">
      <header className="header">
        <div className="brand">
          <div className="brandMark">LI</div>
          <div>
            <h1>Livestock Intelligence</h1>
            <p>Early-Warning System</p>
          </div>
        </div>

        <div className="status">
          <span className="statusDot" />
          Demo Environment
        </div>
      </header>

      <section className="hero">
        <span className="eyebrow">ANIMAL HEALTH & LIVESTOCK INTELLIGENCE</span>
        <h2>Detect what matters before it becomes obvious.</h2>
        <p>
          A domain-specific intelligence platform for pig and cattle/calf
          production, combining scientific, government, regulatory, market,
          technology and funding signals.
        </p>
      </section>

      <section className="grid">
        {signals.map((signal) => (
          <article className="card" key={signal.status}>
            <span className="cardLabel">{signal.status}</span>
            <h3>{signal.title}</h3>
            <p>{signal.description}</p>
          </article>
        ))}
      </section>

      <footer>
        <span>All system timestamps will use UTC/GMT.</span>
        <span>Phase 0 · Project Foundation</span>
      </footer>
    </main>
  );
}

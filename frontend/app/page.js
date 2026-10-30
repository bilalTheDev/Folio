export default function HomePage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "0.75rem",
        background: "#F7F7FA",
        color: "#111118",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <h1 style={{ fontSize: "2rem", fontWeight: 600, letterSpacing: "-0.02em" }}>
        Folio
      </h1>
      <p style={{ fontSize: "1rem", color: "#5F5F70", margin: 0 }}>
        Ask the page.
      </p>
    </main>
  );
}

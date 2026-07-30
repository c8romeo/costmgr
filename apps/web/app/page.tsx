// apps/web/app/page.tsx — minimal landing page (Story 0.1 stub)

export default function Home() {
  return (
    <main style={{ padding: '2rem', maxWidth: 720, margin: '0 auto' }}>
      <h1>bizup/costmgr</h1>
      <p>원가 관리 SaaS — 모놀리스 + 헥사고날 코어 골격 (Story 0.1)</p>
      <ul>
        <li>아키텍처: AD-1 modular monolith + hexagonal core</li>
        <li>엔진 순수성: AD-5 (no I/O, no DB, no clock, no random)</li>
        <li>의존성 방향: AD-11 (ui → api → services → ports → engine)</li>
      </ul>
    </main>
  );
}

import Link from 'next/link';

export default function Home() {
  return (
    <main style={{ padding: '2rem', fontFamily: 'Arial, sans-serif' }}>
      <h1>dreamaware.cc</h1>
      <p>AI-First, Security-Driven Research Portal</p>
      <ul>
        <li><Link href="/wiki/overview">Overview</Link></li>
        <li><Link href="/wiki/ai-futures">AI Futures (2030)</Link></li>
        <li><Link href="/wiki/xikizpedia">Xikizpedia</Link></li>
        <li><Link href="/wiki/forum">Forum & Threads</Link></li>
        <li><Link href="/wiki/security">Security & Policy</Link></li>
      </ul>
    </main>
  );
}
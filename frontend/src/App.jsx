import { useState } from 'react'
import ChatInterface from './components/ChatInterface'
import './App.css'

const highlights = [
  {
    title: 'Contract Analysis & Review',
    description:
      'LexEdge AI analyzes contracts, NDAs, and agreements with comprehensive risk assessment, clause-by-clause review, and redlining suggestions.',
  },
  {
    title: 'Legal Research & Case Law',
    description:
      'Advanced legal research capabilities for case law, statutes, regulations, and precedents with proper citation verification.',
  },
  {
    title: 'Compliance & Regulatory',
    description:
      'Multi-framework compliance auditing for GDPR, SOX, HIPAA, and industry-specific regulations with risk assessment.',
  },
]

const useCases = [
  {
    name: 'Document Analysis',
    details:
      'Analyze legal documents, contracts, and filings to extract key provisions, identify risks, and provide structured summaries.',
  },
  {
    name: 'Case Management',
    details:
      'Track deadlines, manage case timelines, monitor filings, and coordinate case workflow across multiple matters.',
  },
  {
    name: 'Legal Correspondence',
    details:
      'Draft professional client letters, legal notices, demand letters, and settlement proposals with proper legal formatting.',
  },
]

const agentSpecialties = [
  'Contract Law',
  'Corporate Law',
  'Litigation',
  'Compliance',
  'Legal Research',
  'Case Management',
]

function App() {
  const [showChat, setShowChat] = useState(false)

  if (showChat) {
    return (
      <div className="app app-chat">
        <header className="nav nav--chat">
          <div className="brand">
            <span className="brand__mark">LE</span>
            <div>
              <p className="brand__title">LexEdge – Open Legal Agents</p>
              <p className="brand__meta">Legal Intelligence Console</p>
            </div>
          </div>
          <div className="nav__actions">
            <span className="nav__tag">Secure session</span>
            <button className="button button--ghost" onClick={() => setShowChat(false)}>
              Back to landing
            </button>
          </div>
        </header>
        <div className="chat-shell">
          <div className="chat-shell__top">
            <div>
              <p className="eyebrow">Legal workspace</p>
            </div>
            <div className="chat-shell__meta">
              <span>Gemini 1.5 Pro</span>
              <span>Multi-Agent Legal AI</span>
            </div>
          </div>
          <ChatInterface />
        </div>
        <footer className="footer footer--chat footer--tiny">
          <span>
            MIT Licensed &middot; Developed by{' '}
            <a href="https://www.lexedge.ai/" target="_blank" rel="noopener noreferrer" style={{ color: 'inherit', textDecoration: 'underline' }}>LexEdge Lab</a>
          </span>
        </footer>
      </div>
    )
  }

  return (
    <div className="app">
      <div className="background-orb orb-one" />
      <div className="background-orb orb-two" />
      <header className="nav">
        <div className="brand">
          <span className="brand__mark">LE</span>
          <div>
            <p className="brand__title">LexEdge – Open Legal Agents</p>
            <p className="brand__meta">Legal Intelligence Platform</p>
          </div>
        </div>
        <div className="nav__actions">
          <a className="nav__link" href="#use-cases">Use cases</a>
          <a className="nav__link" href="#platform">Platform</a>
          <a className="nav__link" href="#agents">Agents</a>
          <button className="button" onClick={() => setShowChat(true)}>
            Open Legal Console
          </button>
        </div>
      </header>

      <main className="hero">
        <div className="hero__content">
          <p className="eyebrow">AI-Powered Legal Intelligence</p>
          <h1>Agentic legal intelligence for modern law practice.</h1>
          <p className="lead">
            LexEdge combines advanced AI models with Google ADK orchestration to deliver a multi-agent legal
            experience tailored to practice areas and common legal workflows.
          </p>
          <div className="hero__actions">
            <button className="button button--primary" onClick={() => setShowChat(true)}>
              Legal Assistant
            </button>
            <button className="button button--ghost" onClick={() => setShowChat(true)}>
              Contract Review
            </button>
          </div>
          <div className="hero__metrics">
            <div>
              <p className="metric">8 Agents</p>
              <p className="metric__label">Specialized legal AI</p>
            </div>
            <div>
              <p className="metric">Multi-Jurisdiction</p>
              <p className="metric__label">Configurable settings</p>
            </div>
            <div>
              <p className="metric">Compliance</p>
              <p className="metric__label">GDPR, SOX, HIPAA</p>
            </div>
          </div>
        </div>
        <div className="hero__panel">
          <div className="panel">
            <div className="panel__header">
              <p>Legal workflow summary</p>
              <span>Now</span>
            </div>
            <div className="panel__body">
              <p className="panel__title">Multi-agent legal routing</p>
              <p>
                Assign contract analysis, legal research, and compliance agents to the same case while LexEdge
                handles document review + legal reasoning.
              </p>
              <div className="panel__tags">
                <span>Contract Review</span>
                <span>Case Law Research</span>
                <span>Compliance Audit</span>
              </div>
            </div>
            <div className="panel__footer">
              <button className="button button--ghost" onClick={() => setShowChat(true)}>
                Open Legal Console
              </button>
              <p className="panel__note">AI-assisted analysis. Review with licensed counsel.</p>
            </div>
          </div>
        </div>
      </main>

      <section className="section" id="use-cases">
        <div className="section__title">
          <h2>Core LexEdge Open Legal Agents capabilities</h2>
          <p>Streamline legal workflows with AI-powered document analysis and research.</p>
        </div>
        <div className="grid">
          {useCases.map((useCase) => (
            <article key={useCase.name} className="card">
              <h3>{useCase.name}</h3>
              <p>{useCase.details}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section section--alt" id="platform">
        <div className="section__title">
          <h2>Why LexEdge – Open Legal Agents</h2>
          <p>Built for legal teams seeking efficient, accurate AI-assisted legal workflows.</p>
        </div>
        <div className="grid grid--highlight">
          {highlights.map((item) => (
            <article key={item.title} className="card card--accent">
              <h3>{item.title}</h3>
              <p>{item.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section" id="agents">
        <div className="section__title">
          <h2>Legal agents available now</h2>
          <p>LexEdge – Open Legal Agents provides specialized legal agents coordinated by Google ADK for comprehensive legal support.</p>
        </div>
        <div className="agent-grid">
          {agentSpecialties.map((agent) => (
            <div key={agent} className="agent-chip">
              <span>{agent}</span>
            </div>
          ))}
        </div>
        <div className="section__footer">
          <button className="button button--primary" onClick={() => setShowChat(true)}>
            Consult an agent
          </button>
          <p className="subtext">Add new practice areas by extending the agent registry in `lexedge/sub_agents`.</p>
        </div>
      </section>

      <footer className="footer">
        <div>
          <p className="brand__title">LexEdge – Open Legal Agents</p>
          <p className="footer__text">Agentic legal workflows powered by advanced AI and Google ADK.</p>
        </div>
        <div className="footer__meta">
          <p style={{ fontSize: '0.82rem', opacity: 0.75, margin: '0 0 10px 0' }}>
            MIT Licensed &middot; Developed by{' '}
            <a href="https://www.lexedge.ai/" target="_blank" rel="noopener noreferrer"
              style={{ color: 'inherit', textDecoration: 'underline', fontWeight: 600 }}>
              LexEdge Lab
            </a>
          </p>
          <button className="button button--ghost" onClick={() => setShowChat(true)}>
            Launch Console
          </button>
        </div>
      </footer>
    </div>
  )
}

export default App

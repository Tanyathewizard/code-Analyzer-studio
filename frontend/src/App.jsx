import { useState } from 'react'
import CodeInput from './components/CodeInput'
import ResultsDisplay from './components/ResultsDisplay'
import QuickActions from './components/QuickActions'
import { analyzeCode } from './services/api'
import UMLDiagramGenerator from './components/UMLDiagramGenerator'

function App() {
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState('python')
  const [analysisType, setAnalysisType] = useState('all')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState({ type: '', message: '' })
  const [view, setView] = useState('input') // input, results, uml, diagrams

  const handleAnalyze = async () => {
    if (!code.trim()) {
      setStatus({
        type: 'error',
        message: 'Add some code or drop a file to start the analysis.',
      })
      return
    }

    setLoading(true)
    setStatus({ type: '', message: '' })
    setView('input')

    try {
      const data = await analyzeCode(code, language, analysisType)
      setResults(data)
      setView('results')

      if (data._usingMockData) {
        setStatus({
          type: 'info',
          message:
            'Backend API was unreachable, so you are seeing interactive mock data. Start the backend to get real results.',
        })
      }
    } catch (err) {
      setResults(null)
      setStatus({
        type: 'error',
        message: err.message || 'The analyzer failed. Please try again.',
      })
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleCopyCode = () => {
    navigator.clipboard.writeText(code)
    setStatus({ type: 'info', message: 'Code copied to clipboard!' })
    setTimeout(() => setStatus({ type: '', message: '' }), 2000)
  }

  const handleExportJSON = () => {
    if (!results) {
      setStatus({ type: 'error', message: 'No results to export. Run analysis first.' })
      return
    }
    try {
      const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = 'analysis-results.json'
      anchor.click()
      URL.revokeObjectURL(url)
      setStatus({ type: 'info', message: 'JSON exported successfully!' })
      setTimeout(() => setStatus({ type: '', message: '' }), 2000)
    } catch (error) {
      setStatus({ type: 'error', message: 'Failed to export JSON.' })
    }
  }

  const handleGenerateReport = () => {
    if (!results) {
      setStatus({ type: 'error', message: 'No results to generate report. Run analysis first.' })
      return
    }
    // Generate a text report from results
    let report = 'Code Analysis Report\n'
    report += '='.repeat(50) + '\n\n'
    report += `Analysis Type: ${analysisType}\n`
    report += `Language: ${language}\n`
    report += `Date: ${new Date().toLocaleString()}\n\n`
    
    if (results.data) {
      Object.entries(results.data).forEach(([key, value]) => {
        report += `\n${key.toUpperCase()}:\n`
        report += '-'.repeat(30) + '\n'
        if (typeof value === 'object') {
          report += JSON.stringify(value, null, 2) + '\n'
        } else {
          report += String(value) + '\n'
        }
      })
    }
    
    const blob = new Blob([report], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'analysis-report.txt'
    anchor.click()
    URL.revokeObjectURL(url)
    setStatus({ type: 'info', message: 'Report generated successfully!' })
    setTimeout(() => setStatus({ type: '', message: '' }), 2000)
  }

  const handleQuickAction = (action) => {
    switch (action) {
      case 'uml':
        setView('uml')
        break
      case 'diagrams':
        if (results) {
          setView('results')
        } else {
          setStatus({ type: 'error', message: 'Run analysis first to view diagrams.' })
        }
        break
      case 'export':
        handleExportJSON()
        break
      case 'report':
        handleGenerateReport()
        break
      default:
        break
    }
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <div className="logo-icon">
            <span>&lt;/&gt;</span>
          </div>
          <div className="header-title">
            <h1>Code Analyzer Studio</h1>
            <p className="subtitle">Advanced semantic analysis & visualization</p>
          </div>
        </div>
        <button className="multi-agent-btn">
          <span className="sparkle-icon">✨</span>
          Multi-agent
        </button>
      </header>

      {/* Main Content */}
      {view === 'results' ? (
        <section className="results-section">
          <div className="results-header-bar">
            <button className="back-btn" onClick={() => setView('input')}>
              ← Back to editor
            </button>
            <div>
              <p className="result-label">Analysis Output</p>
              <h2>Insights & Graphs</h2>
            </div>
            <span className="status-chip">{loading ? 'Refreshing…' : 'Ready'}</span>
          </div>
          <ResultsDisplay loading={loading} results={results} />
        </section>
      ) : view === 'uml' ? (
        <section className="uml-section">
          <div className="section-header">
              <h2>UML Diagram Generator</h2>
            <button className="back-btn" onClick={() => setView('input')}>
                ← Back to editor
              </button>
          </div>
          <UMLDiagramGenerator />
        </section>
      ) : (
        <div className="main-workspace">
          {/* Left Panel - Input Workspace */}
          <div className="input-workspace-panel">
            <div className="panel-header">
              <div className="panel-title">
                <span className="panel-icon">📄</span>
              <h2>Input Workspace</h2>
              </div>
              <div className="panel-actions">
                <button className="copy-btn" onClick={handleCopyCode} title="Copy code">
                  <span>📋</span>
                </button>
              </div>
            </div>

            <div className="language-selector">
              <select
                className="language-dropdown"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="python">Python</option>
                <option value="javascript">JavaScript</option>
                <option value="typescript">TypeScript</option>
                <option value="java">Java</option>
                <option value="cpp">C++</option>
              </select>
            </div>

            <CodeInput
              code={code}
              language={language}
              analysisType={analysisType}
              onCodeChange={setCode}
              onLanguageChange={setLanguage}
              onAnalysisTypeChange={setAnalysisType}
              onAnalyze={handleAnalyze}
              loading={loading}
            />

            {status.message && (
              <div className={`status-banner ${status.type === 'info' ? 'info' : 'error'}`}>
                {status.message}
              </div>
            )}

            <div className="workspace-actions">
              <button
                className="run-analysis-btn"
                onClick={handleAnalyze}
                disabled={loading}
              >
                <span className="play-icon">▶</span>
                {loading ? 'Analyzing…' : 'Run Analysis'}
              </button>
              <label className="upload-file-btn">
                <input
                  type="file"
                  accept=".py,.js,.ts,.java,.cpp,.txt"
                  onChange={(e) => {
                    const file = e.target.files?.[0]
                    if (file) {
                      const reader = new FileReader()
                      reader.onload = (event) => setCode(event.target.result?.toString() ?? '')
                      reader.readAsText(file)
                    }
                  }}
                />
                Upload File
              </label>
            </div>
          </div>

          {/* Right Panel - Quick Actions */}
          <QuickActions
            onAction={handleQuickAction}
            hasResults={!!results}
          />
        </div>
      )}
    </div>
  )
}

export default App

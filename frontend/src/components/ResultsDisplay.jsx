import { useEffect, useMemo, useState } from 'react'
import GraphPreview from './GraphPreview'
import UMLDiagramViewer from './UMLDiagramViewer'


const formatKey = (key) =>
  key
    .replace(/_/g, ' ')
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, (char) => char.toUpperCase())

const stringifyValue = (value, depth = 0) => {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return 'No data available.'
    return value
      .map((entry) => {
        if (typeof entry === 'string') return `• ${entry}`
        if (typeof entry === 'object' && entry !== null) {
          const line = Object.entries(entry)
            .map(([k, v]) => `${formatKey(k)}: ${stringifyValue(v, depth + 1)}`)
            .join(' · ')
          return `• ${line}`
        }
        return `• ${String(entry)}`
      })
      .join('\n')
  }

  if (typeof value === 'object') {
    if (depth > 3) {
      return JSON.stringify(value, null, 2)
    }
    return Object.entries(value)
      .map(([k, v]) => `${formatKey(k)}: ${stringifyValue(v, depth + 1)}`)
      .join('\n')
  }

  return '—'
}

const downloadJson = (label, payload) => {
  try {
    const safeLabel = label.toLowerCase().replace(/[^a-z0-9]+/g, '-')
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${safeLabel || 'analysis'}-results.json`
    anchor.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to trigger download', error)
  }
}

const deepFindKey = (node, targetKey) => {
  if (!node || typeof node !== 'object') return null
  if (node[targetKey]) {
    return node[targetKey]
  }
  for (const value of Object.values(node)) {
    if (typeof value === 'object') {
      const result = deepFindKey(value, targetKey)
      if (result) return result
    }
  }
  return null
}

const buildCfgGraph = (cfg) => {
  if (!cfg?.nodes?.length) return null
  return {
    nodes: cfg.nodes.map((node) => ({
      id: node.id,
      label: `${node.kind.toUpperCase()} • ${node.name}`,
      line: node.lineno,
      kind: node.kind,
    })),
    edges: (cfg.edges || []).map((edge, index) => ({
      id: `${edge.from}-${edge.to}-${index}`,
      from: edge.from,
      to: edge.to,
      label: edge.type || '',
    })),
  }
}

const buildDfgGraph = (dfg) => {
  if (!dfg || (!dfg.assignments && !dfg.uses)) return null

  const nodes = []
  const edges = []

  Object.entries(dfg.assignments || {}).forEach(([variable, lines]) => {
    lines.forEach((line) => {
      nodes.push({
        id: `assign_${variable}_${line}`,
        label: `Assign ${variable}`,
        line,
        kind: 'assign',
      })
    })
  })

  Object.entries(dfg.uses || {}).forEach(([variable, lines]) => {
    lines.forEach((line) => {
      const useId = `use_${variable}_${line}`
      nodes.push({
        id: useId,
        label: `Use ${variable}`,
        line,
        kind: 'use',
      })

      const assigns = dfg.assignments?.[variable] || []
      assigns.forEach((assignLine, idx) => {
        edges.push({
          id: `edge_${variable}_${assignLine}_${line}_${idx}`,
          from: `assign_${variable}_${assignLine}`,
          to: useId,
          label: 'data',
        })
      })
    })
  })

  if (!nodes.length) return null
  return { nodes, edges }
}

const HIDDEN_DATA_KEYS = new Set(['cfg_svg', 'dfg_svg', 'graph_path', 'graph_paths'])
const GRAPH_DATA_KEYS = new Set(['cfg', 'dfg'])
const QUALITY_KEYS = new Set(['quality'])

const getPreferredScheme = () => {
  if (typeof window === 'undefined' || !window.matchMedia) return 'dark'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

const deriveHighlightCards = (value) => {
  if (!value || typeof value !== 'object') return []

  const candidates = []
  const collectEntries = (source) => {
    if (!source || typeof source !== 'object') return
    Object.entries(source).forEach(([key, entryValue]) => {
      if (entryValue === null || entryValue === undefined) return
      if (
        typeof entryValue === 'number' ||
        (typeof entryValue === 'string' && entryValue.trim().length <= 60)
      ) {
        candidates.push({ key, value: entryValue })
      }
    })
  }

  collectEntries(value.summary)
  collectEntries(value.metrics)
  if (!candidates.length && !Array.isArray(value)) {
    collectEntries(value)
  }

  const seen = new Set()
  const result = []
  candidates.forEach(({ key, value }) => {
    if (seen.has(key)) return
    seen.add(key)
    result.push({ label: formatKey(key), value })
  })
  return result.slice(0, 6)
}

const formatScore = (score) => {
  const numeric = typeof score === 'number' ? score : Number(score)
  if (Number.isFinite(numeric)) {
    return Math.round(numeric)
  }
  return score
}

const deriveNavHint = (value) => {
  if (!value || typeof value !== 'object') {
    return 'Raw output'
  }

  if (Array.isArray(value)) {
    return value.length ? `${value.length} entries` : 'No entries'
  }

  const summary = value.summary
  if (summary && typeof summary === 'object') {
    if (summary.overall_grade && summary.overall_score !== undefined) {
      return `${summary.overall_grade} · ${formatScore(summary.overall_score)} pts`
    }
    if (summary.overall_grade) {
      return `Grade: ${summary.overall_grade}`
    }
    if (summary.overall_score !== undefined) {
      return `Score: ${formatScore(summary.overall_score)}`
    }
  }

  const metrics = value.metrics
  if (metrics && typeof metrics === 'object') {
    const numericMetric = Object.entries(metrics).find(
      ([, metricValue]) => typeof metricValue === 'number'
    )
    if (numericMetric) {
      return `${formatKey(numericMetric[0])}: ${numericMetric[1]}`
    }
  }

  const keys = Object.keys(value)
  if (keys.length) {
    return `${keys.length} fields`
  }

  return 'Raw output'
}

const formatHighlightValue = (value) => {
  if (typeof value === 'number') {
    if (Number.isInteger(value)) return value.toLocaleString()
    return value.toFixed(value < 1 ? 3 : 2)
  }
  return value
}

const ResultsDisplay = ({ results, loading }) => {
  if (loading) {
    return (
      <div className="result-placeholder">
        Running analyzers, crunching embeddings, drawing graphs…
      </div>
    )
  }

  if (!results) {
    return (
      <div className="result-placeholder">
        Insights will appear here once the analyzer finishes. Expect call stack
        summaries, CFG previews, and agent recommendations.
      </div>
    )
  }

  if (results.success === false && !results._usingMockData) {
    return (
      <div className="result-placeholder">
        Analyzer reported: {results.error || 'Unknown error. Please retry.'}
      </div>
    )
  }

  const [colorScheme, setColorScheme] = useState(getPreferredScheme)

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = (event) => setColorScheme(event.matches ? 'dark' : 'light')
    media.addEventListener('change', handleChange)
    return () => media.removeEventListener('change', handleChange)
  }, [])

  const rawEntries = useMemo(() => {
    return Object.entries(results.data || {}).filter(([key, value]) => {
      const hasValue = value !== undefined && value !== null
      return hasValue && !HIDDEN_DATA_KEYS.has(key)
    })
  }, [results.data])

  const cfgData = deepFindKey(results, 'cfg')
  const dfgData = deepFindKey(results, 'dfg')
  const cfgGraph = buildCfgGraph(cfgData)
  const dfgGraph = buildDfgGraph(dfgData)
  const qualityData = results.data?.quality || null
  const showCfgPage = Boolean(cfgGraph)
  const showDfgPage = Boolean(dfgGraph)
  const hasSemantic = results.data?.semantic && !results.data.semantic.error
  const standardEntries = useMemo(
    () =>
      rawEntries.filter(
        ([key]) => !GRAPH_DATA_KEYS.has(key) && !QUALITY_KEYS.has(key)
      ),
    [rawEntries]
  )

  const [activeIndex, setActiveIndex] = useState(0)

  const navItems = useMemo(() => {
    const items = []

    if (showDfgPage) {
      items.push({
        id: 'dfg-board',
        label: 'DFG Result Page',
        hint: 'Assignments & usages',
        type: 'dfg',
      })
    }

    if (showCfgPage) {
      items.push({
        id: 'cfg-board',
        label: 'CFG Insights',
        hint: 'Control flow focus',
        type: 'cfg',
      })
    }

    if (qualityData) {
      items.push({
        id: 'quality-board',
        label: 'Quality Dashboard',
        hint: deriveNavHint(qualityData),
        type: 'quality',
        data: qualityData,
      })
    }

    standardEntries.forEach(([key, value]) => {
      items.push({
        id: key,
        label: formatKey(key),
        hint: deriveNavHint(value),
        type: 'data',
        dataKey: key,
        data: value,
      })
    })

    if (hasSemantic) {
      items.push({
        id: 'uml-diagram',
        label: 'UML Diagram',
        hint: 'Auto-generated from semantic analysis',
        type: 'uml',
      })
    }

    if (!items.length && rawEntries.length) {
      items.push({
        id: 'raw-output',
        label: 'Raw Output',
        hint: 'Analyzer payload',
        type: 'data',
        dataKey: rawEntries[0][0],
        data: rawEntries[0][1],
      })
    }

    return items
  }, [showDfgPage, showCfgPage, qualityData, standardEntries, hasSemantic, rawEntries])

  useEffect(() => {
    if (!navItems.length) {
      setActiveIndex(0)
      return
    }
    setActiveIndex((prev) => Math.min(prev, navItems.length - 1))
  }, [navItems.length])

  const activeItem = navItems[activeIndex]
  const highlightCards = useMemo(() => deriveHighlightCards(activeItem?.data), [activeItem])
  const showNav = navItems.length > 1

  const dfgStats = useMemo(() => {
    if (!dfgData) {
      return {
        categories: 0,
        assignments: 0,
        uses: 0,
        nodes: 0,
        variables: [],
      }
    }
    const assignments = Object.entries(dfgData.assignments || {})
    const uses = Object.entries(dfgData.uses || {})
    const assignmentCount = assignments.reduce((sum, [, lines]) => sum + lines.length, 0)
    const useCount = uses.reduce((sum, [, lines]) => sum + lines.length, 0)
    const nodes = assignmentCount + useCount
    const variablesMap = new Map()
    assignments.forEach(([variable, lines]) => {
      variablesMap.set(variable, {
        variable,
        lines,
        uses: [],
      })
    })
    uses.forEach(([variable, lines]) => {
      if (!variablesMap.has(variable)) {
        variablesMap.set(variable, { variable, lines: [], uses: [...lines] })
      } else {
        variablesMap.get(variable).uses = [...lines]
      }
    })
    const variables = Array.from(variablesMap.values()).sort((a, b) =>
      a.variable.localeCompare(b.variable)
    )
    return {
      categories: assignments.length,
      assignments: assignmentCount,
      uses: useCount,
      nodes,
      variables,
    }
  }, [dfgData])

  const downloadActiveJson = () => {
    if (!activeItem) return
    if (activeItem.type === 'data' && activeItem.dataKey) {
      downloadJson(activeItem.dataKey, activeItem.data)
    } else if (activeItem.type === 'quality') {
      downloadJson('quality', qualityData)
    } else if (activeItem.type === 'dfg' && dfgData) {
      downloadJson('dfg', dfgData)
    } else if (activeItem.type === 'cfg' && cfgData) {
      downloadJson('cfg', cfgData)
    }
  }

  const renderDfgPage = () => {
    if (!showDfgPage) return null
    return (
      <section className="result-card dfg-page">
        <header className="result-card__header">
          <div>
            <p className="result-label">Result page</p>
            <h3>DFG Result Page</h3>
          </div>
          <button type="button" className="download-btn" onClick={() => downloadJson('dfg', dfgData)}>
            Download JSON
          </button>
        </header>
        <div className="dfg-stats-grid">
          <div className="dfg-stat-card">
            <p>Total Categories</p>
            <strong>{dfgStats.categories || '—'}</strong>
          </div>
          <div className="dfg-stat-card">
            <p>Total Nodes</p>
            <strong>{dfgStats.nodes || '—'}</strong>
          </div>
          <div className="dfg-stat-card">
            <p>Assignments</p>
            <strong>{dfgStats.assignments || '—'}</strong>
          </div>
          <div className="dfg-stat-card">
            <p>Uses</p>
            <strong>{dfgStats.uses || '—'}</strong>
          </div>
        </div>
        <div className="dfg-tree">
          {dfgStats.variables.length ? (
            dfgStats.variables.map((variable) => (
              <div className="dfg-branch" key={variable.variable}>
                <div className="dfg-node assignment">
                  <span className="dfg-node-title">Assignments: {variable.variable}</span>
                  <span className="dfg-node-meta">{variable.lines.length} lines</span>
                </div>
                <div className="dfg-children">
                  {variable.lines.map((line) => (
                    <div className="dfg-child" key={`${variable.variable}-assign-${line}`}>
                      <span className="dfg-pill">line {line}</span>
                      <span className="dfg-pill subtle">Assign</span>
                    </div>
                  ))}
                  {variable.uses.map((line) => (
                    <div className="dfg-child use" key={`${variable.variable}-use-${line}`}>
                      <span className="dfg-pill">line {line}</span>
                      <span className="dfg-pill subtle">Use</span>
                    </div>
                  ))}
                </div>
              </div>
            ))
          ) : (
            <div className="graph-empty glass-outline">No DFG data available.</div>
          )}
        </div>
        {dfgGraph && (
          <div className="insights-graph">
            <GraphPreview
              title="Data Flow Graph (DFG)"
              graph={dfgGraph}
              svg={results.data?.dfg_svg}
              filename="dfg"
            />
          </div>
        )}
      </section>
    )
  }

  const renderCfgPage = () => {
    if (!showCfgPage) return null
    return (
      <section className="result-card insights-board">
        <header className="result-card__header">
          <div>
            <p className="result-label">Diagram suite</p>
            <h3>Control Flow Graph</h3>
          </div>
          <button type="button" className="download-btn" onClick={() => downloadJson('cfg', cfgData)}>
            Download JSON
          </button>
        </header>
        <div className="insights-hero">
          <div>
            <p className="insights-eyebrow">Analysis output</p>
            <h4>Insights &amp; Graphs</h4>
          </div>
          <span className="status-chip">{loading ? 'Refreshing…' : 'Ready'}</span>
        </div>
        <div className="insights-graph">
          <GraphPreview title="Control Flow Graph (CFG)" graph={cfgGraph} svg={results.data?.cfg_svg} filename="cfg" />
        </div>
      </section>
    )
  }

  const renderQualityPage = () => {
    if (!qualityData) return null
    const summary = qualityData.summary || {}
    const grade = summary.overall_grade || qualityData.overall_grade || '—'
    const score = summary.overall_score ?? qualityData.overall_score ?? '—'
    const totalIssues = summary.total_issues ?? qualityData.total_issues ?? 0
    const criticalIssues = summary.critical_issues ?? qualityData.critical_issues ?? 0
    const readability = summary.readability_score ?? qualityData.readability_score ?? '—'
    const avgLine = summary.avg_line_length ?? qualityData.avg_line_length ?? '—'
    const metrics = qualityData.metrics || {}
    const recommendations = qualityData.recommendations || summary.recommendations || []
    return (
      <section className="result-card quality-dashboard">
        <div className="quality-header">
          <div>
            <p className="result-label">Analysis output</p>
            <h3>Insights &amp; Graphs</h3>
          </div>
          <div className="quality-status">
            <div className="indicator" />
            <span>{loading ? 'Processing' : 'Ready'}</span>
          </div>
        </div>
        <div className="quality-metrics-grid">
          <div className="quality-metric-card">
            <p>Overall Grade</p>
            <strong>{grade}</strong>
          </div>
          <div className="quality-metric-card">
            <p>Overall Score</p>
            <strong>{formatScore(score)}</strong>
          </div>
          <div className="quality-metric-card">
            <p>Total Issues</p>
            <strong>{totalIssues}</strong>
          </div>
          <div className="quality-metric-card">
            <p>Critical Issues</p>
            <strong>{criticalIssues}</strong>
          </div>
          <div className="quality-metric-card">
            <p>Readability Score</p>
            <strong>{formatScore(readability)}</strong>
          </div>
          <div className="quality-metric-card">
            <p>Avg Line Length</p>
            <strong>{avgLine}</strong>
          </div>
        </div>
        <div className="quality-section quality-nav">
          <button className="quality-nav-card active">
            <p className="quality-nav-title">Quality</p>
            <span>{grade} · {formatScore(score)} pts</span>
          </button>
          <button className="quality-nav-card">
            <p className="quality-nav-title">Semantic</p>
            <span>{summary.semantic_fields ? `${summary.semantic_fields} fields` : 'Auto generated'}</span>
          </button>
          <button className="quality-nav-card">
            <p className="quality-nav-title">ML Analysis</p>
            <span>Neural predictions</span>
          </button>
        </div>
        <div className="quality-section quality-report">
          <div className="quality-report-header">
            <div>
              <p className="result-label">Result page</p>
              <h4>Quality</h4>
            </div>
            <button type="button" className="download-btn" onClick={() => downloadJson('quality', qualityData)}>
              Download JSON
            </button>
          </div>
          <div className="quality-report-body">
            <p><span>Summary:</span> Overall Grade: {grade}</p>
            <p><span>Overall Score:</span> {formatScore(score)}</p>
            <p><span>Total Issues:</span> {totalIssues}</p>
            <p><span>Critical Issues:</span> {criticalIssues}</p>
            {Object.entries(metrics).map(([key, value]) => (
              <p key={key}>
                <span>{formatKey(key)}:</span> {value}
              </p>
            ))}
            {recommendations.length > 0 && (
              <p>
                <span>Recommendations:</span> {recommendations.join(', ')}
              </p>
            )}
          </div>
        </div>
      </section>
    )
  }

  const renderDataPage = () => {
    if (activeItem?.type !== 'data') return null
    return (
      <>
        {highlightCards.length > 0 && (
          <div className="highlight-grid">
            {highlightCards.map((card) => (
              <div className="highlight-card" key={card.label}>
                <p className="highlight-label">{card.label}</p>
                <p className="highlight-value">{formatHighlightValue(card.value)}</p>
              </div>
            ))}
          </div>
        )}
        <article className="result-card result-page insight-panel">
          <header className="result-card__header">
            <div>
              <p className="result-label">Result page</p>
              <h3>{formatKey(activeItem.label || activeItem.dataKey)}</h3>
            </div>
            <button type="button" className="download-btn" onClick={downloadActiveJson}>
              Download JSON
            </button>
          </header>
          <div className="insight-body">
            <pre>{stringifyValue(activeItem.data)}</pre>
          </div>
        </article>
      </>
    )
  }

  const totalPages = navItems.length
  const isDfgPage = activeItem?.type === 'dfg'
  const isCfgPage = activeItem?.type === 'cfg'
  const isQualityPage = activeItem?.type === 'quality'
  const isUmlPage = activeItem?.type === 'uml'
  const isDataPage = activeItem?.type === 'data'

  return (
    <div className={`results-wrapper results-theme results-theme--${colorScheme}`}>
      <div className="result-meta">
        <span>
          <strong>Status:</strong> {results.success === false ? 'Partial' : 'Complete'}
        </span>
        <span>
          <strong>Analysis:</strong> {formatKey(results.analysis_type || 'all')}
        </span>
        <span>
          <strong>Source:</strong> {results._usingMockData ? 'Mock data' : 'Live backend'}
        </span>
      </div>

      {totalPages ? (
        <div className={`dashboard-layout${showNav ? '' : ' no-nav'}`}>
          {showNav && (
            <aside className="dashboard-nav">
              <p className="result-label">Sections</p>
              <div className="dashboard-nav__list">
                {navItems.map((item, index) => (
                  <button
                    key={item.id}
                    type="button"
                    className={`nav-item${activeIndex === index ? ' active' : ''}`}
                    onClick={() => setActiveIndex(index)}
                  >
                    <div className="nav-title-row">
                      <span className="nav-title">{item.label}</span>
                    </div>
                    <span className="nav-hint">{item.hint}</span>
                  </button>
                ))}
              </div>
            </aside>
          )}

          <div className="dashboard-main">
            {isDfgPage && renderDfgPage()}
            {isCfgPage && !isDfgPage && renderCfgPage()}
            {isQualityPage && !isDfgPage && !isCfgPage && renderQualityPage()}
            {isUmlPage && <UMLDiagramViewer analysisResults={results.data?.semantic} />}
            {isDataPage && renderDataPage()}
          </div>
        </div>
      ) : (
        <div className="result-placeholder">
          Analyzer returned an empty payload. Double-check the backend response.
        </div>
      )}
    </div>
  )
}

export default ResultsDisplay


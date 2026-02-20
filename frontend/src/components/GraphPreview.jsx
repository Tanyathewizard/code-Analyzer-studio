import { useRef } from 'react'

const getNodeColor = (kind) => {
  if (kind === 'if') return '#fff3cd'
  if (kind === 'loop') return '#e2f7e1'
  if (kind === 'call') return '#e8f0ff'
  if (kind === 'assign') return '#d9f99d'
  if (kind === 'use') return '#fecdd3'
  return '#f8fafc'
}

const downloadSvgFromElement = (svgElement, filename) => {
  const serializer = new XMLSerializer()
  let source = serializer.serializeToString(svgElement)
  if (!source.match(/^<svg[^>]+xmlns=/)) {
    source = source.replace(
      /^<svg/,
      '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"'
    )
  }
  const blob = new Blob([source], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${filename}.svg`
  link.click()
  URL.revokeObjectURL(url)
}

const downloadPngFromElement = (svgElement, filename) => {
  const serializer = new XMLSerializer()
  const svgString = serializer.serializeToString(svgElement)
  const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(svgBlob)

  const image = new Image()
  image.onload = () => {
    const width =
      svgElement.viewBox.baseVal.width || svgElement.getBoundingClientRect().width || 800
    const height =
      svgElement.viewBox.baseVal.height || svgElement.getBoundingClientRect().height || 600
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d')
    ctx.drawImage(image, 0, 0, width, height)
    canvas.toBlob(
      (blob) => {
        if (!blob) return
        const pngUrl = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = pngUrl
        link.download = `${filename}.png`
        link.click()
        URL.revokeObjectURL(pngUrl)
      },
      'image/png',
      1
    )
    URL.revokeObjectURL(url)
  }
  image.onerror = () => URL.revokeObjectURL(url)
  image.src = url
}

const GraphPreview = ({ title, graph, filename = 'graph', svg = null }) => {
  const nodes = graph?.nodes || []
  const edges = graph?.edges || []
  const safeFilename = filename.toLowerCase().replace(/[^a-z0-9]+/g, '-')
  const svgRef = useRef(null)
  const backendSvgRef = useRef(null)

  const columns = Math.min(nodes.length, 3) || 1
  const xGap = 140
  const yGap = 110
  const width = columns * xGap + 160
  const rows = Math.ceil(nodes.length / columns) || 1
  const height = rows * yGap + 120

  const positions = {}
  nodes.forEach((node, index) => {
    const columnIndex = index % columns
    const rowIndex = Math.floor(index / columns)
    const x = 100 + columnIndex * xGap
    const y = 80 + rowIndex * yGap

    positions[node.id] = { x, y }
  })

  const handleDownloadBackendSvg = () => {
    if (backendSvgRef.current) {
      const svgElement = backendSvgRef.current.querySelector('svg')
      if (svgElement) {
        downloadSvgFromElement(svgElement, safeFilename)
      }
    }
  }

  const handleDownloadBackendPng = () => {
    if (backendSvgRef.current) {
      const svgElement = backendSvgRef.current.querySelector('svg')
      if (svgElement) {
        downloadPngFromElement(svgElement, safeFilename)
      }
    }
  }

  return (
    <div className="graph-panel">
      <div className="graph-header">
        <div>
          <h3>{title}</h3>
          <p>
            {svg ? 'Graphviz generated' : `${nodes.length} nodes · ${edges.length} edges`}
          </p>
        </div>
        <div className="graph-actions">
          {svg ? (
            <>
              <button type="button" onClick={handleDownloadBackendSvg}>
                SVG
              </button>
              <button type="button" onClick={handleDownloadBackendPng}>
                PNG
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={() => svgRef.current && downloadSvgFromElement(svgRef.current, safeFilename)}
              >
                SVG
              </button>
              <button
                type="button"
                onClick={() => svgRef.current && downloadPngFromElement(svgRef.current, safeFilename)}
              >
                PNG
              </button>
            </>
          )}
        </div>
      </div>

      {svg ? (
        <div ref={backendSvgRef} className="graph-backend-svg" style={{ overflow: 'auto', maxHeight: '600px' }}>
          <div dangerouslySetInnerHTML={{ __html: svg }} />
        </div>
      ) : nodes.length ? (
        <svg
          ref={svgRef}
          className="graph-canvas"
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label={title}
        >
          <defs>
            <marker
              id="arrowhead"
              markerWidth="8"
              markerHeight="8"
              refX="6"
              refY="3"
              orient="auto"
            >
              <path d="M0,0 L0,6 L6,3 z" fill="#94a3b8" />
            </marker>
          </defs>

          {edges.map((edge) => {
            const from = positions[edge.from]
            const to = positions[edge.to]
            if (!from || !to) return null
            const midX = (from.x + to.x) / 2
            const midY = (from.y + to.y) / 2
            return (
              <g key={edge.id}>
                <line
                  x1={from.x}
                  y1={from.y}
                  x2={to.x}
                  y2={to.y}
                  stroke="#94a3b8"
                  strokeWidth="2"
                  markerEnd="url(#arrowhead)"
                />
                {edge.label && (
                  <text x={midX} y={midY - 6} className="graph-edge-label">
                    {edge.label}
                  </text>
                )}
              </g>
            )
          })}

          {nodes.map((node) => {
            const position = positions[node.id]
            return (
              <g key={node.id} transform={`translate(${position.x}, ${position.y})`}>
                <rect
                  x={-70}
                  y={-30}
                  width="140"
                  height="60"
                  rx="14"
                  ry="14"
                  fill={getNodeColor(node.kind)}
                  stroke="#0f172a"
                  strokeWidth="1"
                />
                <text className="graph-node-label" x="0" y="-6">
                  {node.label}
                </text>
                {node.line !== undefined && (
                  <text className="graph-node-subtext" x="0" y="14">
                    line {node.line}
                  </text>
                )}
              </g>
            )
          })}
        </svg>
      ) : (
        <div className="graph-empty">No graph data available.</div>
      )}
    </div>
  )
}

export default GraphPreview


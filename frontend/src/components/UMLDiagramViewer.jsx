import { useState, useEffect } from 'react'
import plantumlEncoder from 'plantuml-encoder'

/**
 * UMLDiagramViewer Component
 * Displays UML diagrams generated from semantic analysis results
 */
export function UMLDiagramViewer({ analysisResults }) {
  const [diagram, setDiagram] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [diagramType, setDiagramType] = useState('class')

  useEffect(() => {
    if (analysisResults?.semantic) {
      generateUMLFromAnalysis()
    }
  }, [analysisResults])

  /**
   * Transform semantic analysis to UML data format
   */
  const transformToUMLData = () => {
    const semantic = analysisResults.semantic

    return {
      name: semantic.name || 'AnalyzedClass',
      attributes: (semantic.variable_roles || []).map((role, idx) => ({
        name: typeof role === 'string' ? role : Object.keys(role)[0],
        type: 'auto'
      })),
      methods: (semantic.functions || []).map((func) => ({
        name: func.split('.').pop(),
        params: (semantic.inputs || []).slice(0, 2)
      })),
      relationships: []
    }
  }

  /**
   * Call backend to generate UML diagram
   */
  const generateUMLFromAnalysis = async () => {
    setLoading(true)
    setError('')

    try {
      const umlData = transformToUMLData()

      const response = await fetch('/api/generate-uml', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data: umlData,
          diagram_type: diagramType
        })
      })

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`)
      }

      const result = await response.json()

      if (result.success) {
        setDiagram(result.diagram)
        renderDiagram(result.diagram)
      } else {
        setError(result.error || 'Failed to generate diagram')
      }
    } catch (err) {
      console.error('UML Generation Error:', err)
      setError(err.message || 'Error generating diagram')
    } finally {
      setLoading(false)
    }
  }

  /**
   * Render PlantUML diagram as image
   */
  const renderDiagram = (plantumlText) => {
    try {
      const encoded = plantumlEncoder.encode(plantumlText)
      const url = `https://www.plantuml.com/plantuml/svg/${encoded}`
      setImageUrl(url)
    } catch (err) {
      console.error('Encoding Error:', err)
      setError('Failed to render diagram')
    }
  }

  if (!analysisResults || (!analysisResults.semantic && !analysisResults.entities && !analysisResults.classes)) {
    return (
      <div className="uml-viewer empty">
        <p>📝 No semantic analysis available.</p>
        <p style={{ fontSize: '0.9em', color: '#888', marginTop: '10px' }}>
          Ensure the backend is running and try analyzing code with analysis type set to "Unified (all insights)".
        </p>
        <p style={{ fontSize: '0.85em', color: '#999', marginTop: '8px' }}>
          Debug: {analysisResults ? JSON.stringify(Object.keys(analysisResults)).substring(0, 50) : 'No data'}
        </p>
      </div>
    )
  }

  return (
    <div className="uml-viewer">
      <div className="uml-header">
        <h3>📊 UML Diagram</h3>
        <div className="uml-controls">
          <select
            value={diagramType}
            onChange={(e) => {
              setDiagramType(e.target.value)
              // Re-generate with new type
              setTimeout(generateUMLFromAnalysis, 100)
            }}
          >
            <option value="class">Class Diagram</option>
            <option value="sequence">Sequence Diagram</option>
            <option value="erd">Entity Relationship Diagram</option>
          </select>
          <button onClick={generateUMLFromAnalysis} disabled={loading}>
            {loading ? 'Generating...' : '🔄 Regenerate'}
          </button>
        </div>
      </div>

      {error && (
        <div className="uml-error">
          <p>⚠️ {error}</p>
        </div>
      )}

      {loading && (
        <div className="uml-loading">
          <div className="spinner" />
          <p>Generating UML diagram...</p>
        </div>
      )}

      {imageUrl && !loading && (
        <div className="uml-display">
          <iframe
            src={imageUrl}
            title="UML Diagram"
            className="uml-iframe"
            frameBorder="0"
          />
        </div>
      )}

      <details className="uml-source">
        <summary>📝 PlantUML Source</summary>
        <pre>{diagram}</pre>
      </details>

      <div className="uml-info">
        <p>
          <strong>Analysis:</strong> {analysisResults.semantic.name || 'Code Analysis'}
        </p>
        <p>
          <strong>Purpose:</strong> {analysisResults.semantic.purpose || 'N/A'}
        </p>
        <p>
          <strong>Complexity:</strong> {analysisResults.semantic.complexity_estimate || 'N/A'}
        </p>
      </div>
    </div>
  )
}

export default UMLDiagramViewer

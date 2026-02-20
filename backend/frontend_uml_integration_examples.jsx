/**
 * Frontend Integration Example - UML Generator
 * Shows how to integrate UML generation into React components
 */

// ============================================================================
// 1. Simple UML Generation Service
// ============================================================================

export const generateUML = async (data, diagramType = 'class') => {
    try {
        const response = await fetch('/api/generate-uml', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                data,
                diagram_type: diagramType
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();
        if (result.success) {
            return result.diagram;
        } else {
            throw new Error(result.error || 'Unknown error');
        }
    } catch (error) {
        console.error('UML generation error:', error);
        throw error;
    }
};

// ============================================================================
// 2. React Hook for UML Generation
// ============================================================================

import { useState, useCallback } from 'react';

export const useUMLGenerator = () => {
    const [diagram, setDiagram] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const generate = useCallback(async (data, diagramType = 'class') => {
        setLoading(true);
        setError(null);
        try {
            const result = await generateUML(data, diagramType);
            setDiagram(result);
            return result;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    return { diagram, loading, error, generate };
};

// ============================================================================
// 3. React Component for UML Display
// ============================================================================

import React, { useState, useEffect } from 'react';

const UMLViewer = ({ diagramText, diagramType = 'class' }) => {
    const [encoded, setEncoded] = useState(null);

    useEffect(() => {
        if (diagramText) {
            // Encode PlantUML diagram for online viewer
            const encoded = btoa(diagramText);
            setEncoded(encoded);
        }
    }, [diagramText]);

    if (!encoded) {
        return <div>No diagram to display</div>;
    }

    return (
        <div className="uml-viewer">
            <h3>Generated {diagramType.toUpperCase()} Diagram</h3>
            
            {/* Display as iframe from PlantUML online */}
            <iframe
                src={`https://www.plantuml.com/plantuml/svg/${encoded}`}
                style={{
                    width: '100%',
                    height: '600px',
                    border: '1px solid #ddd'
                }}
                title={`${diagramType} Diagram`}
            />

            {/* Show PlantUML source code */}
            <details>
                <summary>PlantUML Source</summary>
                <pre style={{
                    backgroundColor: '#f5f5f5',
                    padding: '10px',
                    borderRadius: '4px',
                    overflowX: 'auto'
                }}>
                    {diagramText}
                </pre>
            </details>
        </div>
    );
};

export default UMLViewer;

// ============================================================================
// 4. Complete Example: Code Analysis → UML Generation
// ============================================================================

const CodeAnalysisWithUML = () => {
    const [code, setCode] = useState('');
    const [analysisData, setAnalysisData] = useState(null);
    const [diagramType, setDiagramType] = useState('class');
    const { diagram, loading, error, generate } = useUMLGenerator();

    const handleAnalyze = async () => {
        try {
            // Step 1: Analyze code
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: JSON.stringify({
                    code,
                    file_type: 'python',
                    analysis_type: 'semantic'
                })
            });

            const result = await response.json();
            if (result.success && result.data.semantic) {
                setAnalysisData(result.data.semantic);

                // Step 2: Generate UML from semantic data
                await generate(result.data.semantic, diagramType);
            }
        } catch (err) {
            console.error('Error:', err);
        }
    };

    return (
        <div className="code-analysis-with-uml">
            <h2>Code Analysis with UML Generation</h2>

            {/* Code Input */}
            <div>
                <label>Python Code:</label>
                <textarea
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    rows={10}
                    cols={50}
                    placeholder="Enter Python code here..."
                />
            </div>

            {/* Diagram Type Selection */}
            <div>
                <label>Diagram Type:</label>
                <select value={diagramType} onChange={(e) => setDiagramType(e.target.value)}>
                    <option value="class">Class Diagram</option>
                    <option value="sequence">Sequence Diagram</option>
                    <option value="erd">Entity Relationship Diagram</option>
                </select>
            </div>

            {/* Action Button */}
            <button onClick={handleAnalyze} disabled={loading || !code}>
                {loading ? 'Generating...' : 'Analyze & Generate UML'}
            </button>

            {/* Error Display */}
            {error && <div className="error">Error: {error}</div>}

            {/* Results */}
            {analysisData && (
                <div className="analysis-results">
                    <h3>Analysis Results</h3>
                    <pre>{JSON.stringify(analysisData, null, 2)}</pre>
                </div>
            )}

            {/* UML Viewer */}
            {diagram && (
                <UMLViewer diagramText={diagram} diagramType={diagramType} />
            )}
        </div>
    );
};

export default CodeAnalysisWithUML;

// ============================================================================
// 5. Example: Creating UML from Manual Data
// ============================================================================

const ManualUMLExample = () => {
    const { diagram, generate } = useUMLGenerator();

    const handleGenerateClassDiagram = async () => {
        const classData = {
            name: 'User',
            attributes: [
                { name: 'id', type: 'int' },
                { name: 'username', type: 'str' },
                { name: 'email', type: 'str' },
                { name: 'created_at', type: 'datetime' }
            ],
            methods: [
                { name: 'login', params: ['password: str'] },
                { name: 'logout', params: [] },
                { name: 'update_profile', params: ['data: dict'] }
            ],
            relationships: [
                { from: 'User', type: '--|>', to: 'BaseModel' }
            ]
        };

        await generate(classData, 'class');
    };

    const handleGenerateSequenceDiagram = async () => {
        const sequenceData = {
            calls: [
                { caller: 'Client', callee: 'API', method: 'POST /login' },
                { caller: 'API', callee: 'Database', method: 'query_user' },
                { caller: 'Database', callee: 'API', method: 'return_user' },
                { caller: 'API', callee: 'Client', method: 'return_token' }
            ]
        };

        await generate(sequenceData, 'sequence');
    };

    const handleGenerateERD = async () => {
        const erdData = {
            entities: {
                User: [
                    { name: 'id', type: 'INT PRIMARY KEY' },
                    { name: 'email', type: 'VARCHAR(100)' },
                    { name: 'username', type: 'VARCHAR(50)' }
                ],
                Post: [
                    { name: 'id', type: 'INT PRIMARY KEY' },
                    { name: 'user_id', type: 'INT' },
                    { name: 'title', type: 'VARCHAR(200)' }
                ]
            },
            relations: [
                { from: 'User', type: '||--o{', to: 'Post', label: 'creates' }
            ]
        };

        await generate(erdData, 'erd');
    };

    return (
        <div className="manual-uml">
            <h2>Manual UML Generation Examples</h2>

            <div>
                <button onClick={handleGenerateClassDiagram}>
                    Generate Class Diagram
                </button>
                <button onClick={handleGenerateSequenceDiagram}>
                    Generate Sequence Diagram
                </button>
                <button onClick={handleGenerateERD}>
                    Generate ERD
                </button>
            </div>

            {diagram && <UMLViewer diagramText={diagram} />}
        </div>
    );
};

export default ManualUMLExample;

// ============================================================================
// 6. CSS Styles
// ============================================================================

const umlStyles = `
.uml-viewer {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 20px;
    margin: 20px 0;
    background: #f9f9f9;
}

.uml-viewer h3 {
    margin-top: 0;
    color: #333;
}

.uml-viewer iframe {
    border: 1px solid #e0e0e0;
    border-radius: 4px;
}

.uml-viewer details {
    margin-top: 15px;
}

.uml-viewer summary {
    cursor: pointer;
    font-weight: bold;
    color: #0066cc;
}

.uml-viewer pre {
    font-size: 12px;
    line-height: 1.5;
}

.code-analysis-with-uml textarea {
    width: 100%;
    padding: 10px;
    font-family: monospace;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.code-analysis-with-uml button {
    padding: 10px 20px;
    margin: 10px 5px 10px 0;
    background: #0066cc;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.code-analysis-with-uml button:disabled {
    background: #ccc;
    cursor: not-allowed;
}

.error {
    color: #cc0000;
    padding: 10px;
    background: #ffe0e0;
    border: 1px solid #ff6666;
    border-radius: 4px;
    margin: 10px 0;
}
`;

export default umlStyles;

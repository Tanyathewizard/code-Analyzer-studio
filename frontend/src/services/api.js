const resolveApiUrl = () => {
    // Vite environment variable (always available in Vite)
    if (
        import.meta.env &&
        import.meta.env.VITE_ANALYZER_API) {
        return import.meta.env.VITE_ANALYZER_API;
    }
    // If running in browser, use current host
    if (typeof window !== 'undefined') {
        const { protocol, hostname } = window.location;
        return `${protocol}//${hostname}:8000`;
    }
    // Default fallback
    return 'http://localhost:8000';
};

const API_BASE_URL = resolveApiUrl()

const mockAnalysis = (code) => ({
    success: true,
    data: {
        semantic: {
            purpose: 'Mock data - backend offline',
            summary: 'Mocked summary: backend is offline, showing sample insights.',
        },
        quality: {
            overall_score: 7.5,
            recommendations: ['Add more comments', 'Refactor long functions'],
        },
    },
    analysis_type: 'all',
    _usingMockData: true,
})

export async function analyzeCode(code, language, analysisType = 'all') {
    try {
        const response = await fetch(`${API_BASE_URL}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code,
                file_type: language,
                analysis_type: analysisType,
            }),
        })

        if (!response.ok) {
            throw new Error(`Backend returned ${response.status}`)
        }

        const data = await response.json()

        if (!data.success) {
            throw new Error(data.error || 'Analysis failed')
        }

        return data
    } catch (error) {
        console.warn('Analyze request failed, returning mock data.', error)
        return mockAnalysis(code)
    }
}

export async function semanticAnalysis(code, language) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/semantic-analysis`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code,
                file_type: language,
            }),
        })

        if (!response.ok) {
            throw new Error(`Backend returned ${response.status}`)
        }

        return await response.json()
    } catch (error) {
        console.warn('Semantic analysis request failed', error)
        throw error
    }
}

export async function qualityAnalysis(code, language) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/quality-analysis`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code,
                file_type: language,
            }),
        })

        if (!response.ok) {
            throw new Error(`Backend returned ${response.status}`)
        }

        return await response.json()
    } catch (error) {
        console.warn('Quality analysis request failed', error)
        throw error
    }
}

export async function unifiedAnalysis(code, language) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/unified-analysis`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code,
                file_type: language,
            }),
        })

        if (!response.ok) {
            throw new Error(`Backend returned ${response.status}`)
        }

        return await response.json()
    } catch (error) {
        console.warn('Unified analysis request failed', error)
        throw error
    }
}

export async function getHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`)
        return response.ok
    } catch (error) {
        return false
    }
}
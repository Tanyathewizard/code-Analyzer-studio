const resolveApiUrl = () => {
    // If using Vercel env variable
    if (import.meta.env?.VITE_ANALYZER_API) {
        return import.meta.env.VITE_ANALYZER_API;
    }

    // 🔥 PUT YOUR RENDER BACKEND LINK HERE
    return "https://code-analyzer-studio.onrender.com";
};

const API_BASE_URL = resolveApiUrl();

// Mock fallback (used only if backend fails)
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
});

// 🔹 MAIN ANALYSIS
export async function analyzeCode(code, language, analysisType = 'all') {
    try {
        const response = await fetch(`${API_BASE_URL}/api/analyze`,{
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code,
                file_type: language,
                analysis_type: analysisType,
            }),
        });

        if (!response.ok) {
            throw new Error(`Backend returned ${response.status}`);
        }

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Analysis failed');
        }

        return data;

    } catch (error) {
        console.warn('Analyze request failed, returning mock data.', error);
        return mockAnalysis(code);
    }
}

// 🔹 SEMANTIC ANALYSIS
export async function semanticAnalysis(code, language) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/semantic-analysis`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code,
                file_type: language,
            }),
        });

        if (!response.ok) {
            throw new Error(`Backend returned ${response.status}`);
        }

        return await response.json();

    } catch (error) {
        console.warn('Semantic analysis request failed', error);
        throw error;
    }
}

// 🔹 QUALITY ANALYSIS
export async function qualityAnalysis(code, language) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/quality-analysis`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code,
                file_type: language,
            }),
        });

        if (!response.ok) {
            throw new Error(`Backend returned ${response.status}`);
        }

        return await response.json();

    } catch (error) {
        console.warn('Quality analysis request failed', error);
        throw error;
    }
}

// 🔹 UNIFIED ANALYSIS
export async function unifiedAnalysis(code, language) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/unified-analysis`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code,
                file_type: language,
            }),
        });

        if (!response.ok) {
            throw new Error(`Backend returned ${response.status}`);
        }

        return await response.json();

    } catch (error) {
        console.warn('Unified analysis request failed', error);
        throw error;
    }
}

// 🔹 HEALTH CHECK
export async function getHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        return response.ok;
    } catch (error) {
        return false;
    }
}

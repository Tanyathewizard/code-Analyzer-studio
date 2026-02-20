# AI Code Analysis Studio

A comprehensive AI-powered code analysis platform with machine learning capabilities, semantic analysis, and UML diagram generation.

## 🏗️ Architecture Overview

This is a full-stack application built with:

- **Backend**: FastAPI (Python) - REST API server with ML integration
- **Frontend**: React + Vite (JavaScript) - Modern single-page application
- **Database**: SQLite with custom ORM for analysis history
- **ML Pipeline**: Ensemble of 6 trained models for code quality prediction
- **Analysis Engine**: Multi-agent system with semantic, quality, and unified analysis

## 📁 Project Structure

```
├── backend.py                 # Main FastAPI application
├── frontend/                  # React frontend application
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API service layer
│   │   └── styles/            # CSS stylesheets
│   ├── package.json
│   └── vite.config.js
├── models/                    # ML models and training data
├── env11/                     # Python virtual environment
├── analysis.db                # SQLite database
├── requirements.txt           # Python dependencies
├── wrapper.py                 # AI API wrappers (OpenAI, Gemini, etc.)
├── semantic_extractor.py      # Semantic analysis agent
├── quality_agent.py           # Code quality evaluator
├── unified_agent.py           # Unified analysis agent
├── ml_traditional.py          # Traditional ML models
├── ml_inference.py            # ML inference engine
├── uml_generator.py           # UML diagram generator
├── semantic_to_uml.py         # Semantic to UML converter
└── [various test and config files]
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Git

### Backend Setup

1. **Clone and navigate to the project directory**
   ```bash
   cd /path/to/auto-ai-project
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv env11
   env11\Scripts\activate  # Windows
   # source env11/bin/activate  # Linux/Mac
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   API_KEY=your_openai_api_key_here
   # Or use other API keys:
   # OPENROUTER_API_KEY=your_openrouter_key
   # GEMINI_API_KEY=your_gemini_key
   ```

5. **Start the backend server**
   ```bash
   python backend.py
   ```
   The server will start at `http://127.0.0.1:8000`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:5173`

## 🔧 API Endpoints

### Core Analysis Endpoints

- `POST /api/analyze` - Main code analysis (semantic, quality, unified)
- `POST /api/semantic-analysis` - Semantic analysis only
- `POST /api/quality-analysis` - Quality analysis only
- `POST /api/unified-analysis` - Unified analysis

### ML Analysis Endpoints

- `POST /api/ml/analyze` - Single ML prediction
- `POST /api/ml/ensemble-predict` - Ensemble prediction from all models
- `POST /api/ml/model-comparison` - Compare predictions across models
- `POST /api/ml/detailed-metrics` - Extract detailed code metrics
- `POST /api/ml/batch-analyze` - Analyze multiple code samples

### UML Generation Endpoints

- `POST /api/generate-uml` - Generate UML diagrams from structured data
- `POST /api/semantic-to-uml` - Convert semantic analysis to UML

### Utility Endpoints

- `GET /api/analysis/{id}` - Retrieve analysis by ID
- `GET /api/search?keyword=...` - Search analysis history
- `GET /health` - Health check

## 🤖 Analysis Types

### 1. Semantic Analysis
Extracts code structure, entities, classes, functions, and relationships using AI models with fallback strategy: LLAMA → GEMINI → GROQ → OPENAI.

### 2. Quality Analysis
Evaluates code quality metrics including:
- Cyclomatic complexity
- Code maintainability
- Best practices adherence
- Potential issues detection

### 3. Unified Analysis
Combines semantic analysis with intermediate representation (IR) analysis including:
- Control Flow Graph (CFG)
- Data Flow Graph (DFG)
- Symbol table analysis

### 4. ML Analysis
Uses ensemble of 6 trained models to predict:
- Code quality score (0-100)
- Issue severity (Minor/Moderate/Severe/Critical)
- Confidence scores for predictions

## 🎨 Features

### Frontend Features
- **Code Editor**: Syntax-highlighted input with multiple language support
- **Real-time Analysis**: Live code analysis with instant feedback
- **Results Visualization**: Interactive display of analysis results
- **UML Diagrams**: PlantUML-based diagram generation and viewing
- **ML Insights**: Machine learning predictions and model comparisons
- **Export Options**: JSON export and text report generation

### Backend Features
- **Multi-Agent System**: Specialized agents for different analysis types
- **API Fallback Strategy**: Graceful degradation across multiple AI providers
- **Database Persistence**: Analysis history with search functionality
- **Rate Limiting**: Built-in API rate limiting and request throttling
- **CORS Support**: Cross-origin resource sharing for web clients

## 🧠 Machine Learning Models

### Available Models
1. **Random Forest Classifier** - Issue type prediction (~69.35% accuracy)
2. **SVM Classifier** - Issue type prediction (~69.35% accuracy)
3. **Logistic Regression** - Issue type prediction (~69.35% accuracy)
4. **Random Forest Regressor** - Quality score prediction (R² ~0.138)
5. **SVM Regressor** - Quality score prediction (R² ~0.132)
6. **Ridge Regressor** - Quality score prediction (R² ~0.149)

### Feature Extraction
10 code metrics extracted for ML predictions:
- Token count, line count, average line length
- Nesting depth, cyclomatic complexity
- Function/class/branch/loop counts
- Comment ratio

## 🧪 Testing

### Backend Testing
```bash
# Run specific test files
python test_backend.py
python test_api.py
python test_uml_integration.py

# Run ML tests
python TEST_ML_ANALYSIS.py
python test_quick.py
```

### Frontend Testing
```bash
cd frontend
npm run lint
```

## 📊 Database Schema

The application uses SQLite with the following main tables:
- `analyses` - Stores analysis results with metadata
- Custom serialization handles complex Python objects

## 🔒 Security & Configuration

### Environment Variables
- `API_KEY` - Primary API key (supports multiple providers)
- `HOST` - Server host (default: 127.0.0.1)
- `PORT` - Server port (default: 8000)
- `RELOAD` - Auto-reload on code changes (default: True)

### API Rate Limiting
Built-in rate limiting prevents API abuse with configurable thresholds.

## 🚀 Deployment

### Development
```bash
# Backend
python backend.py

# Frontend (separate terminal)
cd frontend && npm run dev
```

### Production
```bash
# Build frontend
cd frontend && npm run build

# Serve static files and run backend
# Configure production server (nginx, gunicorn, etc.)
```

## 📈 Performance

- **ML Inference**: <1ms per prediction
- **Memory Usage**: ~15MB for ML models
- **API Response**: Typically 2-5 seconds for full analysis
- **Concurrent Users**: SQLite limits concurrent writes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **Backend won't start**: Check Python version (3.8+) and dependencies
2. **ML models not loading**: Ensure `models/` directory exists with trained models
3. **API errors**: Verify API keys in `.env` file
4. **Frontend build fails**: Clear `node_modules` and reinstall

### Logs
Check backend logs in terminal output for detailed error information.

## 📚 Additional Documentation

- `ML_INTEGRATION_README.md` - ML system documentation
- `UML_INTEGRATION_SUMMARY.md` - UML generation guide
- `PROJECT_STRUCTURE.md` - Detailed project structure
- `FINAL_SUMMARY.md` - Project completion summary

---

**Built with ❤️ using FastAPI, React, and Machine Learning**

 

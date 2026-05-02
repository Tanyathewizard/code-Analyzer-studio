from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
import logging
import uvicorn
import os
from dotenv import load_dotenv
import json

# Load environment variables early
load_dotenv()

# Configure logging early so import-time warnings/exceptions are visible
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom JSON Encoder for non-serializable objects
class CustomJSONEncoder(json.JSONEncoder):
    """Custom encoder to handle non-serializable objects"""
    def default(self, obj):
        # Handle objects with __dict__ attribute
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        # Handle objects with dict() method
        if hasattr(obj, 'dict'):
            try:
                return obj.dict()
            except:
                pass
        # Handle dataclass-like objects
        if hasattr(obj, '__dataclass_fields__'):
            return {f.name: getattr(obj, f.name) for f in obj.__dataclass_fields__.values()}
        # Fallback to string representation
        return str(obj)

# Wrapper and Database
try:
    from wrapper import gemini_analyze_code, llama_extract_json, extract_json
    WRAPPER_DB_AVAILABLE = False
except Exception:
    logger.exception("Wrapper import failed")
    WRAPPER_DB_AVAILABLE = False

# Local graph/IR builders
try:
    from cfg_builder import build_cfg
    from dfg_builder import build_dfg
    from graph_generator import generate_graphs, generate_cfg_svg, generate_dfg_svg
    from symbol_table import build_symbol_table
    GRAPH_TOOLS_AVAILABLE = True
except Exception:
    logger.exception("Failed to import graph/IR builder modules")
    GRAPH_TOOLS_AVAILABLE = False

# UML Generator
try:
    from uml_generator import generate_uml
    UML_GENERATOR_AVAILABLE = True
except Exception:
    logger.exception("Could not import UML generator")
    UML_GENERATOR_AVAILABLE = False

# Semantic to UML Converter
try:
    from semantic_to_uml import semantic_to_uml
    SEMANTIC_TO_UML_AVAILABLE = True
except Exception:
    logger.exception("Could not import semantic_to_uml")
    SEMANTIC_TO_UML_AVAILABLE = False

# Import analysis agents
try:
    from semantic_extractor import SemanticExtractor
    from quality_agent import CodeQualityEvaluator
    from analyzer_agent import UnifiedAnalyzer
    AGENTS_AVAILABLE = True
except Exception:
    logger.exception("Could not import analysis agents (semantic_extractor, quality_agent, analyzer_agent)")
    AGENTS_AVAILABLE = False

# ML Models Integration
try:
    from ml_traditional import TraditionalMLModels
    from ml_data import CodeFeatureExtractor
    import numpy as np
    ML_AVAILABLE = True
except Exception:
    logger.exception("ML modules not available")
    ML_AVAILABLE = False

# Initialize FastAPI app
app = FastAPI(
    title="AI Analysis Backend",
    description="Backend API for AI Code Analysis",
    version="1.0.0"
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup"""
    if WRAPPER_DB_AVAILABLE:
        try:
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)

    # Initialize ML models
    if ML_AVAILABLE:
        global ml_models, feature_extractor
        try:
            ml_models = TraditionalMLModels()
            feature_extractor = CodeFeatureExtractor()
            logger.info("✅ ML models initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ ML models initialization warning: {e}", exc_info=True)

    logger.info("Starting AI Analysis Backend")
    logger.info(f"API Key configured: {bool(get_api_key())}")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# DATA MODELS
# ============================================================================

class AnalysisRequest(BaseModel):
    """Model for analysis requests"""
    code: str
    file_type: Optional[str] = "python"
    analysis_type: Optional[str] = "all"
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "def hello():\n    print('Hello')",
                "file_type": "python",
                "analysis_type": "all"
            }
        }
    )


class AnalysisResult(BaseModel):
    """Model for analysis results"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    analysis_type: str


class UMLGenerationRequest(BaseModel):
    """Model for UML generation requests"""
    data: Dict[str, Any]
    diagram_type: Optional[str] = "class"
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": {
                    "name": "MyClass",
                    "attributes": [
                        {"name": "id", "type": "int"},
                        {"name": "name", "type": "str"}
                    ],
                    "methods": [
                        {"name": "get_id", "params": []}
                    ]
                },
                "diagram_type": "class"
            }
        }
    )


class UMLGenerationResult(BaseModel):
    """Model for UML generation results"""
    success: bool
    diagram: Optional[str] = None
    error: Optional[str] = None
    diagram_type: str


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    version: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# Initialize agents (lazy loading)
_semantic_extractor = None
_quality_evaluator = None
_unified_analyzer = None


def get_semantic_extractor():
    """Get or create semantic extractor instance"""
    global _semantic_extractor
    if _semantic_extractor is None and AGENTS_AVAILABLE:
        _semantic_extractor = SemanticExtractor()
    return _semantic_extractor


def get_quality_evaluator():
    """Get or create quality evaluator instance"""
    global _quality_evaluator
    if _quality_evaluator is None and AGENTS_AVAILABLE:
        _quality_evaluator = CodeQualityEvaluator()
    return _quality_evaluator


def get_unified_analyzer():
    """Get or create unified analyzer instance"""
    global _unified_analyzer
    if _unified_analyzer is None and AGENTS_AVAILABLE:
        _unified_analyzer = UnifiedAnalyzer()
    return _unified_analyzer


def get_api_key() -> str:
    """Get API key from environment variables"""
    # Try multiple key names
    api_key = os.getenv("API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        logger.info("✓ API Key found in environment")
    else:
        logger.warning("API_KEY not found in environment variables")
    return api_key


# ============================================================================
# ROUTES - HEALTH CHECK
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {"message": "AI Analysis Backend API", "status": "running"}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )


@app.get("/api/status", tags=["Health"])
async def runtime_status():
    """
    Returns runtime flags so frontend/dev can assert which capabilities loaded.
    """
    try:
        return {
            "success": True,
            "AGENTS_AVAILABLE": AGENTS_AVAILABLE,
            "GRAPH_TOOLS_AVAILABLE": GRAPH_TOOLS_AVAILABLE,
            "UML_GENERATOR_AVAILABLE": UML_GENERATOR_AVAILABLE,
            "SEMANTIC_TO_UML_AVAILABLE": SEMANTIC_TO_UML_AVAILABLE,
            "WRAPPER_DB_AVAILABLE": WRAPPER_DB_AVAILABLE,
            "ML_AVAILABLE": ML_AVAILABLE,
            "api_key_present": bool(get_api_key())
        }
    except Exception:
        logger.exception("Error building runtime status")
        return {"success": False, "error": "status error"}

# ============================================================================
# ROUTES - ML ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/api/ml/analyze", tags=["ML Analysis"])
async def ml_analyze_code(request: AnalysisRequest):
    """
    Analyze code using ML models
    Returns: quality score (0-100), issue type (0-3), confidence
    """
    if not ML_AVAILABLE:
        return {"error": "ML models not available", "success": False}
    
    try:
        code = request.code.strip()
        if not code:
            return {"error": "Code cannot be empty", "success": False}
        
        # Extract features
        features = feature_extractor.extract(code)
        features_array = np.array([
            features.get('token_count', 0),
            features.get('line_count', 0),
            features.get('avg_line_length', 0),
            features.get('nesting_depth', 0),
            features.get('cyclomatic_complexity', 0),
            features.get('num_functions', 0),
            features.get('num_classes', 0),
            features.get('num_branches', 0),
            features.get('num_loops', 0),
            features.get('num_comments', 0)
        ], dtype=np.float32)
        
        # Get predictions
        quality = float(ml_models.predict_rf_reg(features_array))
        issue_type, confidence = ml_models.predict_rf_clf(features_array)
        
        issue_names = ["Minor", "Moderate", "Severe", "Critical"]
        
        return {
            "success": True,
            "quality": quality,
            "issue_type": int(issue_type),
            "issue_name": issue_names[int(issue_type)],
            "confidence": float(confidence),
            "features": features
        }
    except Exception:
        logger.exception("ML analysis error")
        return {"error": "ML analysis failed", "success": False}


@app.post("/api/ml/train", tags=["ML Analysis"])
async def train_ml_models(request: dict):
    """
    Train ML models on provided data
    Expects: {"X_train": [...], "y_train": [...]}
    """
    if not ML_AVAILABLE:
        return {"error": "ML models not available", "success": False}
    
    try:
        X_train = np.array(request.get("X_train", []), dtype=np.float32)
        y_train = np.array(request.get("y_train", []))
        
        if X_train.size == 0 or y_train.size == 0:
            return {"error": "Training data cannot be empty", "success": False}
        
        # Train Random Forest
        result = ml_models.train_random_forest_classifier(X_train, y_train)
        
        return {
            "success": True,
            "message": "Models trained successfully",
            "metrics": result
        }
    except Exception:
        logger.exception("ML training error")
        return {"error": "Training failed", "success": False}


@app.post("/api/ml/batch-analyze", tags=["ML Analysis"])
async def ml_batch_analyze(request: dict):
    """
    Analyze multiple code samples
    Expects: {"codes": [code1, code2, ...]}
    """
    if not ML_AVAILABLE:
        return {"error": "ML models not available", "success": False}
    
    try:
        codes = request.get("codes", [])
        if not codes:
            return {"error": "No codes provided", "success": False}
        
        results = []
        for code in codes:
            features = feature_extractor.extract(code)
            features_array = np.array([
                features.get('token_count', 0),
                features.get('line_count', 0),
                features.get('avg_line_length', 0),
                features.get('nesting_depth', 0),
                features.get('cyclomatic_complexity', 0),
                features.get('num_functions', 0),
                features.get('num_classes', 0),
                features.get('num_branches', 0),
                features.get('num_loops', 0),
                features.get('num_comments', 0)
            ], dtype=np.float32)
            
            quality = float(ml_models.predict_rf_reg(features_array))
            issue_type, confidence = ml_models.predict_rf_clf(features_array)
            
            results.append({
                "quality": quality,
                "issue_type": int(issue_type),
                "confidence": float(confidence)
            })
        
        return {
            "success": True,
            "results": results,
            "total": len(results)
        }
    except Exception:
        logger.exception("Batch analysis error")
        return {"error": "Batch analysis failed", "success": False}


# ============================================================================
# ROUTES - ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/api/analyze", response_model=AnalysisResult, tags=["Analysis"])
async def analyze_code(analysis_request: AnalysisRequest, request: Request):
    """
    Analyze code and return analysis results

    - **code**: The source code to analyze
    - **file_type**: Programming language type (default: python)
    - **analysis_type**: Type of analysis - 'semantic', 'quality', 'unified', or 'all'
    """
    try:
        logger.info(f"Request received: {request.method} {request.url.path}")
        if not analysis_request.code.strip():
            raise HTTPException(status_code=400, detail="Code cannot be empty")

        logger.info(f"Analyzing code with type: {analysis_request.analysis_type}")
        
        if not AGENTS_AVAILABLE:
            logger.warning("Analysis agents not available")
            raise HTTPException(status_code=503, detail="Analysis agents not available")
        
        result_data = {}

        # Always attempt to build CFG/DFG/Symbol Table for supported languages (best-effort)
        try:
            if analysis_request.file_type == "python":
                if GRAPH_TOOLS_AVAILABLE:
                    cfg = build_cfg(analysis_request.code)
                    dfg = build_dfg(analysis_request.code)
                    symbol_table = build_symbol_table(analysis_request.code)
                    result_data["cfg"] = cfg
                    result_data["dfg"] = dfg
                    result_data["symbol_table"] = symbol_table
                    # generate image artifacts (optional) under output/ by default
                    try:
                        paths = generate_graphs(cfg, dfg, output_dir=os.path.join(os.getcwd(), "output"))
                        if paths:
                            result_data["graph_paths"] = paths
                    except Exception:
                        logger.exception("Graph generation failed")

                    # Try to generate inline SVGs (useful for embedding in frontend)
                    try:
                        cfg_svg = generate_cfg_svg(cfg)
                        dfg_svg = generate_dfg_svg(dfg)
                        if cfg_svg:
                            result_data["cfg_svg"] = cfg_svg
                        if dfg_svg:
                            result_data["dfg_svg"] = dfg_svg
                    except Exception:
                        logger.exception("Inline SVG generation failed")
                else:
                    # Tools not available; still include empty placeholders
                    result_data.setdefault("cfg", {"nodes": [], "edges": []})
                    result_data.setdefault("dfg", {"assignments": {}, "uses": {}})
            else:
                # Non-python file types: include empty placeholders for frontend
                result_data.setdefault("cfg", {"nodes": [], "edges": []})
                result_data.setdefault("dfg", {"assignments": {}, "uses": {}})
        except Exception:
            logger.exception("CFG/DFG generation failed")
        
        # Perform requested analyses
        if analysis_request.analysis_type in ["semantic", "all"]:
            try:
                semantic_extractor = get_semantic_extractor()
                if semantic_extractor:
                    semantic_result = semantic_extractor.run(analysis_request.code, analysis_request.file_type)
                    result_data["semantic"] = semantic_result
                    logger.info("Semantic analysis completed: keys: %s", list(semantic_result.keys()) if isinstance(semantic_result, dict) else "non-dict")
                else:
                    logger.warning("Semantic extractor not available")
                    result_data["semantic"] = {"error": "Semantic extractor not available", "entities": []}
            except Exception:
                logger.exception("Semantic analysis error")
                result_data["semantic"] = {"error": "Semantic analysis failed", "entities": []}
                result_data["semantic_error"] = "Semantic analysis failed"

        if analysis_request.analysis_type in ["quality", "all"]:
            try:
                quality_evaluator = get_quality_evaluator()
                if quality_evaluator:
                    quality_result = quality_evaluator.evaluate(analysis_request.code, analysis_request.file_type)
                    result_data["quality"] = quality_result
                    logger.info("Quality analysis completed")
            except Exception:
                logger.exception("Quality analysis error")
                result_data["quality_error"] = "Quality analysis failed"

        if analysis_request.analysis_type in ["unified", "all"]:
            try:
                unified_analyzer = get_unified_analyzer()
                if unified_analyzer:
                    unified_result = unified_analyzer.analyze(analysis_request.code, analysis_request.file_type)
                    result_data["unified"] = unified_result
                    logger.info("Unified analysis completed")
            except Exception:
                logger.exception("Unified analysis error")
                result_data["unified_error"] = "Unified analysis failed"
        
        # Add the original code to the response for ML Analysis
        result_data["code"] = analysis_request.code

        # Try to generate UML diagram if semantic data is available
        if UML_GENERATOR_AVAILABLE and "semantic" in result_data:
            try:
                semantic_data = result_data.get("semantic", {})

                # Check if semantic data is valid and has the right structure
                if isinstance(semantic_data, dict) and not semantic_data.get("error"):
                    # For class/structure analysis, try to extract class info
                    if "classes" in semantic_data or "entities" in semantic_data or "name" in semantic_data:
                        try:
                            # Try class diagram first (most common)
                            uml_data = semantic_to_uml(semantic_data, "class")
                            if uml_data:
                                result_data["uml"] = {"class_diagram": uml_data}
                                logger.info("UML diagram generated")
                        except Exception:
                            logger.exception("Class diagram generation failed")
                            # Try ERD if class diagram fails
                            try:
                                uml_data = semantic_to_uml(semantic_data, "erd")
                                if uml_data:
                                    result_data["uml"] = {"erd": uml_data}
                                    logger.info("UML ERD diagram generated")
                            except Exception:
                                logger.exception("ERD generation failed")
                    else:
                        logger.debug("Semantic data structure not suitable for UML generation")
                else:
                    logger.debug("No valid semantic data for UML generation")
            except Exception:
                logger.exception("UML generation attempt failed")


        # Save analysis to database (if available)
        if WRAPPER_DB_AVAILABLE:
            try:
                analysis_kind = analysis_request.analysis_type if analysis_request.analysis_type != "all" else "comprehensive"
                # Use custom encoder to handle non-serializable objects
                result_json = json.dumps(result_data, cls=CustomJSONEncoder, default=str)
                save_analysis(
                    language=analysis_request.file_type,
                    kind=analysis_kind,
                    code=analysis_request.code,
                    result=result_json,
                    summary=f"Analysis of {analysis_request.file_type} code with {analysis_kind} mode"
                )
                logger.info("Analysis saved to database")
            except Exception:
                logger.exception("Failed to save analysis to database")

        return AnalysisResult(
            success=True,
            data=result_data,
            analysis_type=analysis_request.analysis_type
        )
    
    except Exception:
        logger.exception("Analysis error")
        analysis_type = getattr(analysis_request, "analysis_type", "unknown") if 'analysis_request' in locals() else "unknown"
        return AnalysisResult(
            success=False,
            error="Analysis failed",
            analysis_type=analysis_type
        )


# ============================================================================
# ROUTES - SEMANTIC ANALYSIS
# ============================================================================

@app.post("/api/semantic-analysis", tags=["Semantic Analysis"])
async def semantic_analysis(request: AnalysisRequest):
    """
    Perform semantic analysis on code
    """
    try:
        if not request.code.strip():
            raise HTTPException(status_code=400, detail="Code cannot be empty")
        
        logger.info("Starting semantic analysis")
        
        if not AGENTS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Semantic analysis not available")
        
        semantic_extractor = get_semantic_extractor()
        if not semantic_extractor:
            raise HTTPException(status_code=503, detail="Semantic extractor not initialized")
        
        result = semantic_extractor.run(request.code, request.file_type)
        
        return AnalysisResult(
            success=True,
            data=result,
            analysis_type="semantic"
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Semantic analysis error")
        return AnalysisResult(
            success=False,
            error="Semantic analysis failed",
            analysis_type="semantic"
        )


# ============================================================================
# ROUTES - QUALITY ANALYSIS
# ============================================================================

@app.post("/api/quality-analysis", tags=["Quality Analysis"])
async def quality_analysis(request: AnalysisRequest):
    """
    Perform quality analysis on code
    """
    try:
        if not request.code.strip():
            raise HTTPException(status_code=400, detail="Code cannot be empty")
        
        logger.info("Starting quality analysis")
        
        if not AGENTS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Quality analysis not available")
        
        quality_evaluator = get_quality_evaluator()
        if not quality_evaluator:
            raise HTTPException(status_code=503, detail="Quality evaluator not initialized")
        
        result = quality_evaluator.evaluate(request.code, request.file_type)
        
        return AnalysisResult(
            success=True,
            data=result,
            analysis_type="quality"
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Quality analysis error")
        return AnalysisResult(
            success=False,
            error="Quality analysis failed",
            analysis_type="quality"
        )


# ============================================================================
# ROUTES - UNIFIED ANALYSIS
# ============================================================================

@app.post("/api/unified-analysis", tags=["Analysis"])
async def unified_analysis(request: AnalysisRequest):
    """
    Perform unified analysis combining IR, semantic, and quality analysis
    """
    try:
        if not request.code.strip():
            raise HTTPException(status_code=400, detail="Code cannot be empty")
        
        logger.info("Starting unified analysis")
        
        if not AGENTS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Unified analysis not available")
        
        unified_analyzer = get_unified_analyzer()
        if not unified_analyzer:
            raise HTTPException(status_code=503, detail="Unified analyzer not initialized")
        
        result = unified_analyzer.analyze(request.code, request.file_type)
        
        return AnalysisResult(
            success=True,
            data=result,
            analysis_type="unified"
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unified analysis error")
        return AnalysisResult(
            success=False,
            error="Unified analysis failed",
            analysis_type="unified"
        )


# ============================================================================
# ROUTES - SEMANTIC TO UML CONVERSION
# ============================================================================

@app.post("/api/semantic-to-uml", tags=["Semantic to UML"])
async def semantic_to_uml_conversion(request: dict):
    """
    Convert semantic analysis results to UML diagrams

    Expects: {"semantic_data": {...}, "diagram_type": "class|sequence"}
    Returns: UML diagram string
    """
    try:
        semantic_data = request.get("semantic_data", {})
        diagram_type = request.get("diagram_type", "class")

        if not semantic_data:
            raise HTTPException(status_code=400, detail="Semantic data cannot be empty")

        if diagram_type not in ["class", "sequence"]:
            raise HTTPException(status_code=400, detail="diagram_type must be 'class' or 'sequence'")

        if not SEMANTIC_TO_UML_AVAILABLE:
            raise HTTPException(status_code=503, detail="Semantic to UML converter not available")

        logger.info(f"Converting semantic data to {diagram_type} diagram")

        # Extract the appropriate data structure for the diagram type
        if diagram_type == "class":
            data = semantic_data.get("classes", [])
        elif diagram_type == "sequence":
            calls = semantic_data.get("calls", [])
            # Transform calls to participant format expected by semantic_to_uml
            participants = {}
            for call in calls:
                caller = call.get("caller")
                callee = call.get("callee")
                method = call.get("method", "call")
                if caller not in participants:
                    participants[caller] = {"name": caller, "calls": []}
                participants[caller]["calls"].append(f"{callee}: {method}")
                # Ensure callee is also a participant
                if callee not in participants:
                    participants[callee] = {"name": callee, "calls": []}
            data = list(participants.values())
        else:
            data = semantic_data

        # Convert semantic data to UML
        uml_diagram = semantic_to_uml(data, diagram_type)

        if not uml_diagram:
            return {
                "success": False,
                "error": "Failed to generate UML diagram from semantic data"
            }

        return {
            "success": True,
            "diagram": uml_diagram,
            "diagram_type": diagram_type
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Semantic to UML conversion error")
        return {
            "success": False,
            "error": "Semantic to UML conversion failed"
        }


# ============================================================================
# ROUTES - UML GENERATION
# ============================================================================

@app.post("/api/generate-uml", response_model=UMLGenerationResult, tags=["UML"])
async def generate_uml_diagram(request: UMLGenerationRequest):
    """
    Generate UML diagram from structured data
    """
    try:
        if not request.data:
            raise HTTPException(status_code=400, detail="Data cannot be empty")

        if request.diagram_type not in ["class", "sequence", "erd"]:
            raise HTTPException(status_code=400, detail="Invalid diagram_type. Use 'class', 'sequence', or 'erd'")

        if not UML_GENERATOR_AVAILABLE:
            raise HTTPException(status_code=503, detail="UML generator not available")

        logger.info(f"Generating {request.diagram_type} diagram with data: {type(request.data)}")

        try:
            # Generate UML diagram
            diagram = generate_uml(request.data, request.diagram_type)

            if not diagram:
                logger.warning(f"UML generator returned empty diagram for type: {request.diagram_type}")
                return UMLGenerationResult(
                    success=False,
                    error="UML generator returned empty result",
                    diagram_type=request.diagram_type
                )

            logger.info(f"✓ {request.diagram_type.upper()} diagram generated successfully ({len(diagram)} chars)")

            return UMLGenerationResult(
                success=True,
                diagram=diagram,
                diagram_type=request.diagram_type
            )
        except TypeError:
            logger.exception("Type error in UML generation")
            return UMLGenerationResult(
                success=False,
                error=f"Invalid data structure for {request.diagram_type}",
                diagram_type=request.diagram_type
            )
        except ValueError:
            logger.exception("Value error in UML generation")
            return UMLGenerationResult(
                success=False,
                error=f"Invalid value in data for {request.diagram_type}",
                diagram_type=request.diagram_type
            )

    except HTTPException:
        raise
    except Exception:
        logger.exception("UML generation error")
        return UMLGenerationResult(
            success=False,
            error="UML generation failed",
            diagram_type=request.diagram_type
        )


# ============================================================================
# ROUTES - FILE UPLOAD
# ============================================================================

@app.post("/api/upload", tags=["File Operations"])
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and analyze a code file
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        contents = await file.read()
        code_content = contents.decode("utf-8")
        
        logger.info(f"File uploaded: {file.filename}")
        
        # TODO: Process the uploaded file
        # result = analyze_code(code_content, file.filename)
        
        return {
            "success": True,
            "filename": file.filename,
            "size": len(contents),
            "message": "File processed successfully"
        }
    except Exception:
        logger.exception("File upload error")
        raise HTTPException(status_code=400, detail="File upload failed")


# ============================================================================
# ROUTES - BATCH OPERATIONS
# ============================================================================

@app.post("/api/batch-analyze", tags=["Batch Operations"])
async def batch_analyze(requests: List[AnalysisRequest]):
    """
    Analyze multiple code snippets in batch
    """
    try:
        results = []
        for idx, request in enumerate(requests):
            # TODO: Implement batch processing
            result = {
                "index": idx,
                "success": True,
                "data": {"code_length": len(request.code)}
            }
            results.append(result)
        
        return {
            "success": True,
            "total": len(requests),
            "results": results
        }
    except Exception:
        logger.exception("Batch analysis error")
        raise HTTPException(status_code=400, detail="Batch analysis failed")


# ============================================================================
# ROUTES - CONFIGURATION
# ============================================================================

@app.get("/api/config", tags=["Configuration"])
async def get_config():
    """
    Get current configuration (non-sensitive)
    """
    return {
        "version": "1.0.0",
        "analysis_types": ["semantic", "quality", "unified"],
        "supported_file_types": ["python", "java", "javascript", "cpp"],
        "max_file_size_mb": 10
    }


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return {
        "success": False,
        "error": exc.detail,
        "status_code": exc.status_code
    }


# ============================================================================
# ROUTES - HISTORY (DB-backed)
# ============================================================================

@app.get("/api/analysis/{analysis_id}", tags=["History"])
async def get_analysis(analysis_id: int):
    """
    Retrieve a previous analysis result by ID from the database
    """
    if not WRAPPER_DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database functionality not available")
    
    try:
        result = get_analysis_by_id(analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")
        
        # Parse the result JSON
        result["result"] = json.loads(result["result"])
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error retrieving analysis")
        raise HTTPException(status_code=500, detail="Error retrieving analysis")


@app.get("/api/search", tags=["History"])
async def search_analyses(keyword: str):
    """
    Search analysis history by keyword in code, results, or summary
    """
    if not WRAPPER_DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database functionality not available")
    
    try:
        results = search_by_keyword(keyword)
        # Parse result JSON for each record
        for r in results:
            try:
                r["result"] = json.loads(r["result"])
            except:
                pass  # Keep as string if parsing fails
        return {"status": "success", "count": len(results), "data": results}
    except Exception:
        logger.exception("Error searching analyses")
        raise HTTPException(status_code=500, detail="Error searching analyses")


# ============================================================================
# ENHANCED ML ENDPOINTS - COMPREHENSIVE ML INTEGRATION
# ============================================================================

@app.post("/api/ml/ensemble-predict", tags=["ML Analysis - Enhanced"])
async def ensemble_predict(request: AnalysisRequest):
    """
    Ensemble prediction using all models for robust decisions
    Returns: predictions from each model + weighted ensemble result
    """
    if not ML_AVAILABLE:
        return {"error": "ML models not available", "success": False}
    
    try:
        code = request.code.strip()
        if not code:
            return {"error": "Code cannot be empty", "success": False}
        
        # Extract features
        features = feature_extractor.extract(code)
        features_array = np.array([
            features.get('token_count', 0),
            features.get('line_count', 0),
            features.get('avg_line_length', 0),
            features.get('nesting_depth', 0),
            features.get('cyclomatic_complexity', 0),
            features.get('num_functions', 0),
            features.get('num_classes', 0),
            features.get('num_branches', 0),
            features.get('num_loops', 0),
            features.get('num_comments', 0)
        ], dtype=np.float32)
        
        # Get predictions from all models
        predictions = {}
        
        # Regression models (quality prediction)
        predictions['random_forest_reg'] = float(ml_models.predict_rf_reg(features_array))
        predictions['svm_reg'] = float(ml_models.predict_svm_reg(features_array))
        predictions['ridge_reg'] = float(ml_models.predict_ridge_reg(features_array))
        
        # Classification models (issue type prediction)
        rf_issue, rf_conf = ml_models.predict_rf_clf(features_array)
        svm_issue, svm_conf = ml_models.predict_svm_clf(features_array)
        lr_issue, lr_conf = ml_models.predict_lr_clf(features_array)
        
        # Ensemble quality (average of regressors)
        ensemble_quality = np.mean([
            predictions['random_forest_reg'],
            predictions['svm_reg'],
            predictions['ridge_reg']
        ])
        
        # Ensemble issue type (majority vote)
        issue_votes = np.array([rf_issue, svm_issue, lr_issue], dtype=int)
        ensemble_issue = int(np.bincount(issue_votes).argmax())
        
        # Ensemble confidence (average of classifiers)
        ensemble_confidence = float(np.mean([rf_conf, svm_conf, lr_conf]))
        
        issue_names = ["Minor", "Moderate", "Severe", "Critical"]
        
        return {
            "success": True,
            "ensemble": {
                "quality": round(float(ensemble_quality), 2),
                "issue_type": int(ensemble_issue),
                "issue_name": issue_names[int(ensemble_issue)],
                "confidence": round(float(ensemble_confidence), 4)
            },
            "individual_models": {
                "regression": predictions,
                "classification": {
                    "random_forest": {"issue": int(rf_issue), "confidence": round(float(rf_conf), 4)},
                    "svm": {"issue": int(svm_issue), "confidence": round(float(svm_conf), 4)},
                    "logistic_regression": {"issue": int(lr_issue), "confidence": round(float(lr_conf), 4)}
                }
            },
            "features": features,
            "timestamp": str(np.datetime64('now'))
        }
    except Exception:
        logger.exception("Ensemble prediction error")
        return {"error": "Ensemble prediction failed", "success": False}


@app.post("/api/ml/model-comparison", tags=["ML Analysis - Enhanced"])
async def model_comparison(request: AnalysisRequest):
    """
    Compare predictions from all 6 trained models
    Useful for understanding model disagreements and reliability
    """
    if not ML_AVAILABLE:
        return {"error": "ML models not available", "success": False}
    
    try:
        code = request.code.strip()
        if not code:
            return {"error": "Code cannot be empty", "success": False}
        
        features = feature_extractor.extract(code)
        features_array = np.array([
            features.get('token_count', 0),
            features.get('line_count', 0),
            features.get('avg_line_length', 0),
            features.get('nesting_depth', 0),
            features.get('cyclomatic_complexity', 0),
            features.get('num_functions', 0),
            features.get('num_classes', 0),
            features.get('num_branches', 0),
            features.get('num_loops', 0),
            features.get('num_comments', 0)
        ], dtype=np.float32)
        
        # Quality predictions (regression)
        quality_predictions = {
            "random_forest": round(float(ml_models.predict_rf_reg(features_array)), 2),
            "svm": round(float(ml_models.predict_svm_reg(features_array)), 2),
            "ridge": round(float(ml_models.predict_ridge_reg(features_array)), 2)
        }
        
        # Issue type predictions (classification)
        rf_issue, rf_conf = ml_models.predict_rf_clf(features_array)
        svm_issue, svm_conf = ml_models.predict_svm_clf(features_array)
        lr_issue, lr_conf = ml_models.predict_lr_clf(features_array)
        
        issue_names = ["Minor", "Moderate", "Severe", "Critical"]
        
        issue_predictions = {
            "random_forest": {
                "issue_type": int(rf_issue),
                "issue_name": issue_names[int(rf_issue)],
                "confidence": round(float(rf_conf), 4)
            },
            "svm": {
                "issue_type": int(svm_issue),
                "issue_name": issue_names[int(svm_issue)],
                "confidence": round(float(svm_conf), 4)
            },
            "logistic_regression": {
                "issue_type": int(lr_issue),
                "issue_name": issue_names[int(lr_issue)],
                "confidence": round(float(lr_conf), 4)
            }
        }
        
        # Calculate agreement metrics
        quality_std = float(np.std(list(quality_predictions.values())))
        issue_agreement = len(set([int(rf_issue), int(svm_issue), int(lr_issue)])) == 1
        
        return {
            "success": True,
            "quality_predictions": quality_predictions,
            "issue_predictions": issue_predictions,
            "agreement_metrics": {
                "quality_std_dev": round(quality_std, 2),
                "quality_range": [
                    round(min(quality_predictions.values()), 2),
                    round(max(quality_predictions.values()), 2)
                ],
                "issue_agreement": issue_agreement,
                "confidence_average": round(float(np.mean([rf_conf, svm_conf, lr_conf])), 4)
            },
            "code_snippet": code[:100] + "..." if len(code) > 100 else code
        }
    except Exception:
        logger.exception("Model comparison error")
        return {"error": "Model comparison failed", "success": False}


@app.post("/api/ml/detailed-metrics", tags=["ML Analysis - Enhanced"])
async def detailed_metrics(request: AnalysisRequest):
    """
    Get detailed code metrics used by ML models
    Shows extracted features for transparency
    """
    if not ML_AVAILABLE:
        return {"error": "ML models not available", "success": False}
    
    try:
        code = request.code.strip()
        if not code:
            return {"error": "Code cannot be empty", "success": False}
        
        features = feature_extractor.extract(code)
        
        # Normalize feature names and values
        feature_details = {
            "token_count": {
                "value": features.get('token_count', 0),
                "description": "Total number of tokens in code",
                "range": "0-10000"
            },
            "line_count": {
                "value": features.get('line_count', 0),
                "description": "Total lines of code",
                "range": "1-5000"
            },
            "avg_line_length": {
                "value": round(features.get('avg_line_length', 0), 2),
                "description": "Average characters per line",
                "range": "1-200"
            },
            "nesting_depth": {
                "value": features.get('nesting_depth', 0),
                "description": "Maximum nesting level (higher = more complex)",
                "range": "0-20"
            },
            "cyclomatic_complexity": {
                "value": features.get('cyclomatic_complexity', 0),
                "description": "Code complexity (branches/decisions)",
                "range": "1-50"
            },
            "num_functions": {
                "value": features.get('num_functions', 0),
                "description": "Number of function definitions",
                "range": "0-1000"
            },
            "num_classes": {
                "value": features.get('num_classes', 0),
                "description": "Number of class definitions",
                "range": "0-500"
            },
            "num_branches": {
                "value": features.get('num_branches', 0),
                "description": "Number of if/elif/else statements",
                "range": "0-500"
            },
            "num_loops": {
                "value": features.get('num_loops', 0),
                "description": "Number of for/while loops",
                "range": "0-500"
            },
            "num_comments": {
                "value": features.get('num_comments', 0),
                "description": "Number of comment lines",
                "range": "0-5000"
            }
        }
        
        # Categorize features
        complexity_metrics = {
            "cyclomatic_complexity": feature_details["cyclomatic_complexity"]["value"],
            "nesting_depth": feature_details["nesting_depth"]["value"],
            "num_branches": feature_details["num_branches"]["value"],
            "num_loops": feature_details["num_loops"]["value"]
        }
        
        size_metrics = {
            "line_count": feature_details["line_count"]["value"],
            "token_count": feature_details["token_count"]["value"],
            "avg_line_length": feature_details["avg_line_length"]["value"]
        }
        
        structure_metrics = {
            "num_functions": feature_details["num_functions"]["value"],
            "num_classes": feature_details["num_classes"]["value"]
        }
        
        documentation_metrics = {
            "num_comments": feature_details["num_comments"]["value"],
            "comment_ratio": round(feature_details["num_comments"]["value"] / 
                                  max(1, feature_details["line_count"]["value"]), 2)
        }
        
        return {
            "success": True,
            "all_metrics": feature_details,
            "complexity": complexity_metrics,
            "size": size_metrics,
            "structure": structure_metrics,
            "documentation": documentation_metrics,
            "code_quality_indicators": {
                "has_comments": feature_details["num_comments"]["value"] > 0,
                "is_complex": feature_details["cyclomatic_complexity"]["value"] > 10,
                "is_deeply_nested": feature_details["nesting_depth"]["value"] > 5,
                "is_well_structured": feature_details["num_functions"]["value"] > 0
            }
        }
    except Exception:
        logger.exception("Detailed metrics error")
        return {"error": "Detailed metrics failed", "success": False}


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
   reload = False
    
    logger.info(f"Starting server at {host}:{port}")
    
    uvicorn.run(
        "backend:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

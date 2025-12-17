"""
FastAPI Backend for Agentic Multi-Modal Processing System
Handles file uploads, intent detection, and task execution
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import os
import logging
from dotenv import load_dotenv
import tempfile
import shutil

from services.intent_detector import IntentDetector
from services.file_processor import FileProcessor
from services.task_executor import TaskExecutor
from services.youtube_service import YouTubeService
from utils.validators import validate_file_size, validate_file_type
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Agentic Multi-Modal System",
    description="Autonomous AI agent for processing text, images, PDFs, and audio",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
intent_detector = IntentDetector()
file_processor = FileProcessor()
task_executor = TaskExecutor(api_key=os.getenv("ANTHROPIC_API_KEY"))
youtube_service = YouTubeService()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Agentic Multi-Modal Processing System",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "intent_detector": "active",
            "file_processor": "active",
            "task_executor": "active"
        }
    }

@app.post("/api/process")
async def process_request(
    text: str = Form(""),
    file: Optional[UploadFile] = File(None)
):
    """
    Main endpoint for processing user requests
    
    Args:
        text: User's text input or query
        file: Optional file upload (image, PDF, or audio)
    
    Returns:
        JSON response with intent, extracted content, and task result
    """
    temp_file_path = None
    
    try:
        logger.info(f"Processing request - Text length: {len(text)}, File: {file.filename if file else None}")
        
        # Validate inputs
        if not text.strip() and not file:
            raise HTTPException(
                status_code=400,
                detail="Either text or file must be provided"
            )
        
        content = text
        file_info = {}
        
        # Process file if uploaded
        if file:
            # Validate file
            validate_file_size(file)
            validate_file_type(file)
            
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                shutil.copyfileobj(file.file, tmp)
                temp_file_path = tmp.name
            
            logger.info(f"Processing file: {file.filename} ({file.content_type})")
            
            # Route to appropriate processor
            if file.content_type.startswith('image/'):
                file_info = await file_processor.process_image(temp_file_path)
            elif file.content_type == 'application/pdf':
                file_info = await file_processor.process_pdf(temp_file_path)
            elif file.content_type.startswith('audio/'):
                file_info = await file_processor.process_audio(temp_file_path)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {file.content_type}"
                )
            
            # Handle processing errors
            if 'error' in file_info:
                raise HTTPException(
                    status_code=500,
                    detail=f"File processing error: {file_info['error']}"
                )
            
            # Append extracted content to text
            if 'text' in file_info and file_info['text']:
                content = f"{text}\n\n[Extracted Content]:\n{file_info['text']}"
            
            logger.info(f"File processed successfully. Extracted {len(file_info.get('text', ''))} characters")
        
        # Check for YouTube URL
        youtube_url = youtube_service.extract_url(text)
        if youtube_url:
            logger.info(f"YouTube URL detected: {youtube_url}")
            transcript = await youtube_service.get_transcript(youtube_url)
            if transcript:
                content = f"{text}\n\n[YouTube Transcript]:\n{transcript}"
                file_info['youtube'] = True
        
        # Detect intent
        intent = intent_detector.detect(text, file is not None or youtube_url is not None)
        logger.info(f"Detected intent: {intent}")
        
        # Execute task based on intent
        result = await task_executor.execute(intent, content, text)
        
        # Prepare response
        response = {
            'success': True,
            'intent': intent,
            'extracted_content': file_info.get('text', '')[:500] if file_info.get('text') else '',
            'result': result['result'],
            'metadata': {
                'file_type': file_info.get('type', 'text_only'),
                'confidence': file_info.get('confidence'),
                'pages': file_info.get('pages'),
                'duration': file_info.get('duration'),
                'language': file_info.get('language'),
                'youtube': file_info.get('youtube', False)
            }
        }
        
        logger.info("Request processed successfully")
        return response
        
    except HTTPException as e:
        logger.error(f"HTTP error: {e.detail}")
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    
    finally:
        # Cleanup temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.debug(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {e}")

@app.post("/api/estimate-cost")
async def estimate_cost(
    text: str = Form(""),
    file_size: int = Form(0)
):
    """
    Estimate API costs before execution (Bonus feature)
    
    Args:
        text: Input text
        file_size: File size in bytes
    
    Returns:
        Cost estimation
    """
    try:
        # Rough estimation: ~4 chars per token
        text_tokens = len(text) // 4
        file_tokens = file_size // 4 if file_size > 0 else 0
        
        # Add overhead for processing
        total_tokens = (text_tokens + file_tokens) * 1.5
        
        # Claude Sonnet pricing (approximate)
        input_cost = total_tokens * 0.000003  # $3 per million input tokens
        output_cost = 500 * 0.000015  # Assume 500 output tokens at $15 per million
        
        total_cost = input_cost + output_cost
        
        return {
            'estimated_input_tokens': int(total_tokens),
            'estimated_output_tokens': 500,
            'estimated_cost_usd': round(total_cost, 4),
            'note': 'This is an approximation. Actual costs may vary.'
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
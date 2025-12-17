"""
File Processing Service
Handles OCR, PDF parsing, and audio transcription
"""

import logging
from typing import Dict, Optional
from PIL import Image
import PyPDF2
import io

logger = logging.getLogger(__name__)


class FileProcessor:
    """
    Processes different file types:
    - Images: OCR extraction
    - PDFs: Text extraction with OCR fallback
    - Audio: Transcription (placeholder for Whisper integration)
    """
    
    def __init__(self):
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required libraries are available"""
        try:
            import pytesseract
            self.ocr_available = True
            logger.info("Tesseract OCR is available")
        except ImportError:
            self.ocr_available = False
            logger.warning("Tesseract OCR not available. Install with: pip install pytesseract")
        
        try:
            import whisper
            self.whisper_available = True
            logger.info("Whisper is available")
        except ImportError:
            self.whisper_available = False
            logger.warning("Whisper not available. Install with: pip install openai-whisper")
    
    async def process_image(self, file_path: str) -> Dict:
        """
        Extract text from image using OCR
        
        Args:
            file_path: Path to image file
        
        Returns:
            Dict with extracted text and metadata
        """
        try:
            logger.info(f"Processing image: {file_path}")
            
            if not self.ocr_available:
                return {
                    'error': 'OCR not available. Please install pytesseract and tesseract-ocr'
                }
            
            import pytesseract
            
            # Open and process image
            img = Image.open(file_path)
            
            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # Perform OCR
            text = pytesseract.image_to_string(img)
            
            # Get OCR data for confidence calculation
            try:
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if conf != '-1']
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            except:
                avg_confidence = 0
            
            logger.info(f"OCR completed. Extracted {len(text)} characters with {avg_confidence:.1f}% confidence")
            
            return {
                'text': text.strip(),
                'confidence': round(avg_confidence, 2),
                'type': 'image_ocr',
                'dimensions': img.size
            }
        
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}", exc_info=True)
            return {'error': f"Image processing failed: {str(e)}"}
    
    async def process_pdf(self, file_path: str) -> Dict:
        """
        Extract text from PDF with OCR fallback for scanned PDFs
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            Dict with extracted text and metadata
        """
        try:
            logger.info(f"Processing PDF: {file_path}")
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                text = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text += page_text + "\n"
                
                # Check if meaningful text was extracted
                if len(text.strip()) < 50:
                    logger.warning("PDF appears to be scanned. Attempting OCR...")
                    
                    if self.ocr_available:
                        # Convert PDF pages to images and OCR
                        text = await self._ocr_pdf(file_path)
                        return {
                            'text': text.strip(),
                            'pages': num_pages,
                            'type': 'pdf_ocr',
                            'method': 'ocr_fallback'
                        }
                    else:
                        return {
                            'text': text.strip(),
                            'pages': num_pages,
                            'type': 'pdf_text',
                            'warning': 'Limited text extracted. OCR not available.'
                        }
                
                logger.info(f"PDF processed. Extracted {len(text)} characters from {num_pages} pages")
                
                return {
                    'text': text.strip(),
                    'pages': num_pages,
                    'type': 'pdf_text',
                    'method': 'text_extraction'
                }
        
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
            return {'error': f"PDF processing failed: {str(e)}"}
    
    async def _ocr_pdf(self, file_path: str) -> str:
        """
        Fallback OCR for scanned PDFs
        Requires pdf2image library
        """
        try:
            from pdf2image import convert_from_path
            import pytesseract
            
            logger.info("Converting PDF to images for OCR...")
            images = convert_from_path(file_path, dpi=300)
            
            text = ""
            for i, img in enumerate(images):
                logger.info(f"OCR on page {i+1}/{len(images)}")
                page_text = pytesseract.image_to_string(img)
                text += page_text + "\n\n"
            
            return text
        
        except ImportError:
            logger.error("pdf2image not available for OCR fallback")
            return "[OCR not available for scanned PDFs. Install: pip install pdf2image]"
        except Exception as e:
            logger.error(f"OCR fallback failed: {str(e)}")
            return f"[OCR failed: {str(e)}]"
    
    async def process_audio(self, file_path: str) -> Dict:
        """
        Transcribe audio file using Whisper
        
        Args:
            file_path: Path to audio file
        
        Returns:
            Dict with transcription and metadata
        """
        try:
            logger.info(f"Processing audio: {file_path}")
            
            if not self.whisper_available:
                return {
                    'text': '[Audio transcription requires Whisper. Install: pip install openai-whisper]',
                    'type': 'audio_transcription',
                    'error': 'Whisper not available'
                }
            
            import whisper
            
            # Load Whisper model (base model for balance of speed/accuracy)
            logger.info("Loading Whisper model...")
            model = whisper.load_model("base")
            
            # Transcribe
            logger.info("Transcribing audio...")
            result = model.transcribe(file_path)
            
            logger.info(f"Audio transcribed. Duration: {result.get('duration', 0):.1f}s, Language: {result.get('language', 'unknown')}")
            
            return {
                'text': result['text'].strip(),
                'language': result.get('language', 'unknown'),
                'duration': result.get('duration', 0),
                'type': 'audio_transcription'
            }
        
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}", exc_info=True)
            return {
                'text': f'[Audio transcription failed: {str(e)}]',
                'error': str(e),
                'type': 'audio_transcription'
            }
    
    def validate_file(self, file_path: str, expected_type: str) -> bool:
        """
        Validate file exists and is of expected type
        
        Args:
            file_path: Path to file
            expected_type: Expected file type (image, pdf, audio)
        
        Returns:
            True if valid, False otherwise
        """
        import os
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            logger.error(f"File is empty: {file_path}")
            return False
        
        # Basic type checking based on extension
        ext = os.path.splitext(file_path)[1].lower()
        
        type_extensions = {
            'image': ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'],
            'pdf': ['.pdf'],
            'audio': ['.mp3', '.wav', '.m4a', '.ogg', '.flac']
        }
        
        if ext not in type_extensions.get(expected_type, []):
            logger.warning(f"Unexpected file extension {ext} for type {expected_type}")
            return False
        
        return True
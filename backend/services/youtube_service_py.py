"""
YouTube Service
Extracts and processes YouTube video transcripts
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class YouTubeService:
    """
    Handles YouTube URL detection and transcript extraction
    """
    
    # YouTube URL patterns
    URL_PATTERNS = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
    ]
    
    def __init__(self):
        self.compiled_patterns = [re.compile(pattern) for pattern in self.URL_PATTERNS]
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if youtube-transcript-api is available"""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            self.transcript_available = True
            logger.info("YouTube Transcript API is available")
        except ImportError:
            self.transcript_available = False
            logger.warning("YouTube Transcript API not available. Install: pip install youtube-transcript-api")
    
    def extract_url(self, text: str) -> Optional[str]:
        """
        Extract YouTube URL from text
        
        Args:
            text: Text that may contain YouTube URL
        
        Returns:
            YouTube URL if found, None otherwise
        """
        if not text:
            return None
        
        for pattern in self.compiled_patterns:
            match = pattern.search(text)
            if match:
                video_id = match.group(1)
                url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"YouTube URL detected: {url}")
                return url
        
        return None
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL
        
        Args:
            url: YouTube URL
        
        Returns:
            Video ID if found, None otherwise
        """
        for pattern in self.compiled_patterns:
            match = pattern.search(url)
            if match:
                return match.group(1)
        
        return None
    
    async def get_transcript(self, url: str, language: str = 'en') -> Optional[str]:
        """
        Get transcript from YouTube video
        
        Args:
            url: YouTube URL
            language: Preferred language code (default: 'en')
        
        Returns:
            Transcript text if available, None otherwise
        """
        if not self.transcript_available:
            logger.warning("YouTube Transcript API not available")
            return None
        
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
            
            video_id = self.extract_video_id(url)
            if not video_id:
                logger.error(f"Could not extract video ID from URL: {url}")
                return None
            
            logger.info(f"Fetching transcript for video: {video_id}")
            
            # Try to get transcript in preferred language
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
            except NoTranscriptFound:
                # Try to get any available transcript
                logger.info(f"No {language} transcript found, trying any available language")
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Combine all transcript segments
            transcript = " ".join([entry['text'] for entry in transcript_list])
            
            logger.info(f"Transcript fetched successfully. Length: {len(transcript)} characters")
            return transcript
        
        except TranscriptsDisabled:
            logger.warning(f"Transcripts disabled for video: {url}")
            return None
        
        except NoTranscriptFound:
            logger.warning(f"No transcript found for video: {url}")
            return None
        
        except Exception as e:
            logger.error(f"Error fetching transcript: {str(e)}", exc_info=True)
            return None
    
    async def get_transcript_with_timestamps(self, url: str, language: str = 'en') -> Optional[list]:
        """
        Get transcript with timestamps
        
        Args:
            url: YouTube URL
            language: Preferred language code
        
        Returns:
            List of transcript segments with timestamps, None if not available
        """
        if not self.transcript_available:
            return None
        
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            
            video_id = self.extract_video_id(url)
            if not video_id:
                return None
            
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
            return transcript_list
        
        except Exception as e:
            logger.error(f"Error fetching timestamped transcript: {str(e)}")
            return None
    
    def format_transcript(self, transcript_data: list) -> str:
        """
        Format transcript data with timestamps
        
        Args:
            transcript_data: List of transcript segments with timestamps
        
        Returns:
            Formatted transcript string
        """
        if not transcript_data:
            return ""
        
        formatted = []
        for entry in transcript_data:
            timestamp = self._format_timestamp(entry['start'])
            text = entry['text']
            formatted.append(f"[{timestamp}] {text}")
        
        return "\n".join(formatted)
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """
        Convert seconds to MM:SS format
        
        Args:
            seconds: Time in seconds
        
        Returns:
            Formatted timestamp string
        """
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
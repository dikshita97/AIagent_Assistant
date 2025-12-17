"""
Intent Detection Service
Analyzes user input to determine the appropriate task
"""

import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class IntentDetector:
    """
    Detects user intent from text input and file presence
    
    Intents:
    - summarization: User wants content summarized
    - sentiment_analysis: User wants sentiment/emotion analyzed
    - code_explanation: User wants code explained
    - action_items: User wants tasks/todos extracted
    - youtube_transcript: User provided YouTube URL
    - needs_clarification: Intent is ambiguous
    - conversational: General question/chat
    """
    
    # Intent keywords mapping
    INTENT_KEYWORDS: Dict[str, List[str]] = {
        'summarization': [
            'summarize', 'summary', 'tldr', 'brief', 'overview',
            'recap', 'gist', 'key points', 'main points', 'condense'
        ],
        'sentiment_analysis': [
            'sentiment', 'feeling', 'emotion', 'tone', 'mood',
            'opinion', 'attitude', 'positive', 'negative'
        ],
        'code_explanation': [
            'explain code', 'what does this code', 'code explanation',
            'how does this work', 'analyze code', 'review code',
            'debug', 'find bugs', 'what is this function'
        ],
        'action_items': [
            'action item', 'action items', 'todo', 'to-do', 'task',
            'tasks', 'next steps', 'follow up', 'deliverable'
        ],
        'youtube_transcript': [
            'youtube.com', 'youtu.be', 'youtube', 'video transcript'
        ]
    }
    
    # Code patterns
    CODE_PATTERNS = [
        r'def\s+\w+\s*\(',  # Python function
        r'function\s+\w+\s*\(',  # JavaScript function
        r'class\s+\w+',  # Class definition
        r'import\s+[\w.]+',  # Import statement
        r'from\s+[\w.]+\s+import',  # From import
        r'const\s+\w+\s*=',  # Const declaration
        r'let\s+\w+\s*=',  # Let declaration
        r'var\s+\w+\s*=',  # Var declaration
        r'public\s+\w+',  # Java/C# public
        r'private\s+\w+',  # Java/C# private
        r'```[\s\S]*?```',  # Code blocks
    ]
    
    def __init__(self):
        self.compiled_patterns = [re.compile(pattern) for pattern in self.CODE_PATTERNS]
    
    def detect(self, text: str, has_file: bool) -> str:
        """
        Detect the user's intent from input text and file presence
        
        Args:
            text: User's input text
            has_file: Whether a file was uploaded
        
        Returns:
            Detected intent as string
        """
        if not text:
            text = ""
        
        text_lower = text.lower().strip()
        
        # Check for YouTube URL first
        if self._contains_keywords(text_lower, 'youtube_transcript'):
            logger.info("Intent: YouTube transcript detected")
            return 'youtube_transcript'
        
        # Check for code patterns
        if self._contains_code(text):
            if self._contains_explanation_request(text_lower):
                logger.info("Intent: Code explanation detected")
                return 'code_explanation'
        
        # Check explicit intents with high confidence
        for intent, keywords in self.INTENT_KEYWORDS.items():
            if intent == 'youtube_transcript':
                continue  # Already checked
            
            if self._contains_keywords(text_lower, intent):
                logger.info(f"Intent: {intent} detected via keywords")
                return intent
        
        # If file is present but no clear instruction
        if has_file and not self._has_clear_instruction(text_lower):
            logger.info("Intent: Needs clarification (file without clear instruction)")
            return 'needs_clarification'
        
        # Default to conversational
        logger.info("Intent: Conversational (default)")
        return 'conversational'
    
    def _contains_keywords(self, text: str, intent: str) -> bool:
        """Check if text contains keywords for specific intent"""
        keywords = self.INTENT_KEYWORDS.get(intent, [])
        return any(keyword in text for keyword in keywords)
    
    def _contains_code(self, text: str) -> bool:
        """Check if text contains code patterns"""
        return any(pattern.search(text) for pattern in self.compiled_patterns)
    
    def _contains_explanation_request(self, text: str) -> bool:
        """Check if text requests explanation"""
        explanation_words = [
            'explain', 'what does', 'how does', 'what is',
            'analyze', 'review', 'understand', 'clarify'
        ]
        return any(word in text for word in explanation_words)
    
    def _has_clear_instruction(self, text: str) -> bool:
        """
        Check if text contains clear action verbs/instructions
        
        Returns True if user clearly states what they want
        """
        if not text or len(text) < 5:
            return False
        
        action_verbs = [
            'summarize', 'explain', 'analyze', 'extract',
            'find', 'list', 'show', 'tell', 'give',
            'identify', 'detect', 'calculate', 'convert'
        ]
        
        return any(verb in text for verb in action_verbs)
    
    def get_confidence(self, text: str, has_file: bool) -> float:
        """
        Calculate confidence score for detected intent
        
        Returns:
            Confidence score between 0.0 and 1.0
        """
        intent = self.detect(text, has_file)
        
        if intent == 'needs_clarification':
            return 0.0
        
        text_lower = text.lower()
        keyword_matches = sum(
            1 for keyword in self.INTENT_KEYWORDS.get(intent, [])
            if keyword in text_lower
        )
        
        if keyword_matches >= 2:
            return 0.95
        elif keyword_matches == 1:
            return 0.75
        else:
            return 0.5
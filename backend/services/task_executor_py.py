"""
Task Execution Service
Routes tasks to appropriate handlers and executes them using Claude AI
"""

import logging
from typing import Dict
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class TaskExecutor:
    """
    Executes tasks based on detected intent
    Uses Claude AI for intelligent processing
    """
    
    def __init__(self, api_key: str):
        """
        Initialize task executor with Anthropic API key
        
        Args:
            api_key: Anthropic API key
        """
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        logger.info("TaskExecutor initialized with Claude Sonnet 4")
    
    async def execute(self, task_type: str, content: str, original_query: str = "") -> Dict:
        """
        Execute task based on type
        
        Args:
            task_type: Type of task to execute
            content: Content to process
            original_query: Original user query
        
        Returns:
            Dict with task result
        """
        logger.info(f"Executing task: {task_type}")
        
        handlers = {
            'summarization': self._handle_summary,
            'sentiment_analysis': self._handle_sentiment,
            'code_explanation': self._handle_code,
            'action_items': self._handle_actions,
            'needs_clarification': self._handle_clarification,
            'conversational': self._handle_conversational,
            'youtube_transcript': self._handle_youtube
        }
        
        handler = handlers.get(task_type, self._handle_conversational)
        
        try:
            result = await handler(content, original_query)
            logger.info(f"Task {task_type} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}", exc_info=True)
            return {
                'task': task_type,
                'result': f"Error executing task: {str(e)}",
                'error': True
            }
    
    async def _handle_summary(self, content: str, query: str = "") -> Dict:
        """
        Generate structured summary (1-line + 3 bullets + 5 sentences)
        """
        prompt = f"""Provide a comprehensive summary in this EXACT format:

**One-line summary:** [Write a single, concise sentence capturing the main point]

**Key Points:**
• [First key point]
• [Second key point]
• [Third key point]

**Detailed Summary:**
[Write exactly 5 sentences providing a thorough overview of the content. Cover the main themes, important details, and conclusions.]

Content to summarize:
{content}
"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'task': 'summarization',
            'result': response.content[0].text
        }
    
    async def _handle_sentiment(self, content: str, query: str = "") -> Dict:
        """
        Analyze sentiment with confidence score
        """
        prompt = f"""Analyze the sentiment of the following content and return in this EXACT format:

**Sentiment:** [Choose: Positive, Negative, Neutral, or Mixed]
**Confidence:** [Provide percentage, e.g., 85%]
**Justification:** [Write ONE clear sentence explaining why you chose this sentiment]

Content to analyze:
{content}
"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'task': 'sentiment_analysis',
            'result': response.content[0].text
        }
    
    async def _handle_code(self, content: str, query: str = "") -> Dict:
        """
        Explain code with bug detection and complexity analysis
        """
        prompt = f"""Analyze this code and provide a comprehensive explanation in this format:

**Purpose:**
[Explain what this code is designed to do]

**Logic Explanation:**
[Provide a step-by-step breakdown of how the code works]

**Bugs/Issues:**
[Identify any bugs, potential issues, or code smells. If none found, state "No obvious bugs detected."]

**Complexity Analysis:**
[Provide time and space complexity analysis if applicable. Use Big O notation.]

Code to analyze:
{content}
"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'task': 'code_explanation',
            'result': response.content[0].text
        }
    
    async def _handle_actions(self, content: str, query: str = "") -> Dict:
        """
        Extract action items and tasks from content
        """
        prompt = f"""Extract all action items, tasks, and to-dos from the following content.

Format your response as:

**Action Items:**
1. [Action item with owner if mentioned and deadline if specified]
2. [Action item with owner if mentioned and deadline if specified]
...

If no action items are found, respond with: "No action items found in the content."

Content to analyze:
{content}
"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'task': 'action_items',
            'result': response.content[0].text
        }
    
    async def _handle_clarification(self, content: str, query: str = "") -> Dict:
        """
        Ask clarifying question when intent is unclear
        """
        prompt = f"""The user has provided content but hasn't clearly specified what they want to do with it.

Ask them a short, clear clarifying question. Examples:
- "What would you like me to do with this content? I can summarize it, analyze sentiment, explain code, extract action items, or answer questions about it."
- "How can I help you with this file?"
- "What specific information are you looking for from this content?"

Keep the question friendly and concise. Offer specific options based on what seems most relevant.

User's query: {query}
Content provided: {content[:200]}...
"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'task': 'clarification',
            'result': response.content[0].text
        }
    
    async def _handle_conversational(self, content: str, query: str = "") -> Dict:
        """
        Handle general conversational queries
        """
        prompt = f"""Provide a helpful, friendly response to the user's question or comment.

Be concise but informative. If the user is asking about specific content, reference it directly.

User's query: {query}
{f"Context: {content}" if content != query else ""}
"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            'task': 'conversational',
            'result': response.content[0].text
        }
    
    async def _handle_youtube(self, content: str, query: str = "") -> Dict:
        """
        Handle YouTube transcript processing
        """
        # Check if transcript was successfully fetched
        if "[YouTube Transcript]:" in content:
            # Determine what to do with transcript based on query
            if any(word in query.lower() for word in ['summarize', 'summary', 'tldr']):
                return await self._handle_summary(content, query)
            elif any(word in query.lower() for word in ['sentiment', 'tone']):
                return await self._handle_sentiment(content, query)
            else:
                # Default to summary for YouTube
                return await self._handle_summary(content, query)
        else:
            # Transcript fetch failed
            prompt = f"""The user provided a YouTube URL but the transcript could not be fetched automatically.

Explain this limitation politely and suggest:
1. They can try pasting the transcript manually if they have access to it
2. They can describe what they'd like to know about the video
3. In a production system, this would use the YouTube Transcript API

User's query: {query}
"""
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                'task': 'youtube_transcript',
                'result': response.content[0].text
            }
# backend/tests/test_intent.py
"""
Tests for Intent Detector
"""

import pytest
from services.intent_detector import IntentDetector


class TestIntentDetector:
    
    @pytest.fixture
    def detector(self):
        return IntentDetector()
    
    def test_summarization_intent(self, detector):
        text = "Please summarize this document for me"
        intent = detector.detect(text, has_file=False)
        assert intent == 'summarization'
    
    def test_sentiment_intent(self, detector):
        text = "What is the sentiment of this review?"
        intent = detector.detect(text, has_file=False)
        assert intent == 'sentiment_analysis'
    
    def test_code_explanation_intent(self, detector):
        code_text = """
        def hello():
            print("Hello World")
        
        Explain what this code does
        """
        intent = detector.detect(code_text, has_file=False)
        assert intent == 'code_explanation'
    
    def test_action_items_intent(self, detector):
        text = "Extract all action items from this meeting"
        intent = detector.detect(text, has_file=False)
        assert intent == 'action_items'
    
    def test_youtube_intent(self, detector):
        text = "Summarize this video: https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        intent = detector.detect(text, has_file=False)
        assert intent == 'youtube_transcript'
    
    def test_needs_clarification(self, detector):
        text = ""  # Empty text with file
        intent = detector.detect(text, has_file=True)
        assert intent == 'needs_clarification'
    
    def test_conversational_intent(self, detector):
        text = "Hello, how are you?"
        intent = detector.detect(text, has_file=False)
        assert intent == 'conversational'
    
    def test_confidence_high(self, detector):
        text = "Please summarize and give me a summary of this"
        confidence = detector.get_confidence(text, has_file=False)
        assert confidence >= 0.9
    
    def test_confidence_low(self, detector):
        text = ""
        confidence = detector.get_confidence(text, has_file=True)
        assert confidence == 0.0


# backend/tests/test_tasks.py
"""
Tests for Task Executor
"""

import pytest
import os
from services.task_executor import TaskExecutor


@pytest.fixture
def executor():
    api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
    return TaskExecutor(api_key=api_key)


@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="API key not available")
async def test_summarization(executor):
    content = """
    The quarterly meeting covered several important topics. 
    Revenue increased by 15% compared to last quarter. 
    The team discussed new product launches planned for next month.
    Action items include preparing Q4 forecast and updating the dashboard.
    """
    
    result = await executor.execute('summarization', content)
    
    assert result['task'] == 'summarization'
    assert 'One-line summary' in result['result']
    assert 'Key Points' in result['result']
    assert 'Detailed Summary' in result['result']


@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="API key not available")
async def test_sentiment_positive(executor):
    content = "This product is absolutely amazing! Best purchase I've ever made. Highly recommend!"
    
    result = await executor.execute('sentiment_analysis', content)
    
    assert result['task'] == 'sentiment_analysis'
    assert 'Sentiment' in result['result']
    assert 'Confidence' in result['result']
    assert ('Positive' in result['result'] or 'positive' in result['result'])


@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="API key not available")
async def test_sentiment_negative(executor):
    content = "Terrible experience. The product broke after one day. Very disappointed."
    
    result = await executor.execute('sentiment_analysis', content)
    
    assert result['task'] == 'sentiment_analysis'
    assert ('Negative' in result['result'] or 'negative' in result['result'])


@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="API key not available")
async def test_code_explanation(executor):
    code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
    """
    
    result = await executor.execute('code_explanation', code)
    
    assert result['task'] == 'code_explanation'
    assert 'Purpose' in result['result']
    assert 'Complexity' in result['result']


@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="API key not available")
async def test_action_items(executor):
    content = """
    Meeting Notes:
    - John needs to prepare the Q4 forecast by Friday
    - Sarah will update the dashboard with new metrics
    - Team to review marketing materials by end of week
    """
    
    result = await executor.execute('action_items', content)
    
    assert result['task'] == 'action_items'
    assert 'Action Items' in result['result']


@pytest.mark.asyncio
async def test_clarification(executor):
    content = "Here is some content without clear instructions"
    
    result = await executor.execute('needs_clarification', content)
    
    assert result['task'] == 'clarification'
    assert '?' in result['result']  # Should ask a question


@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="API key not available")
async def test_conversational(executor):
    content = "What is machine learning?"
    
    result = await executor.execute('conversational', content)
    
    assert result['task'] == 'conversational'
    assert len(result['result']) > 0


# backend/tests/test_processors.py
"""
Tests for File Processors
"""

import pytest
import os
from services.file_processor import FileProcessor


@pytest.fixture
def processor():
    return FileProcessor()


def test_processor_initialization(processor):
    assert processor is not None


@pytest.mark.skipif(not os.path.exists('tests/sample_data'), reason="Test data not available")
@pytest.mark.asyncio
async def test_image_processing(processor):
    # This would require actual test images
    # For now, we test the method exists
    assert hasattr(processor, 'process_image')


@pytest.mark.skipif(not os.path.exists('tests/sample_data'), reason="Test data not available")
@pytest.mark.asyncio
async def test_pdf_processing(processor):
    # This would require actual test PDFs
    assert hasattr(processor, 'process_pdf')


@pytest.mark.skipif(not os.path.exists('tests/sample_data'), reason="Test data not available")
@pytest.mark.asyncio
async def test_audio_processing(processor):
    # This would require actual test audio
    assert hasattr(processor, 'process_audio')


def test_file_validation(processor):
    # Test that validation method exists
    assert hasattr(processor, 'validate_file')
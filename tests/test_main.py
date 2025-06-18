from app.services.llm_service import LLMService

def test_llm_service():
    service = LLMService()
    lesson = service.generate_lesson("Test prompt")
    assert isinstance(lesson, str)
    assert len(lesson) > 0
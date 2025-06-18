from app.services.llm_service import generate_lesson

def get_coping_exercise():
    return generate_lesson({"age": 10, "language": "en"}, "coping strategies for stress")
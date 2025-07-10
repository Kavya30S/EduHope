from deep_translator import GoogleTranslator
from flask import current_app
import json

def translate_text(text, target_lang="en"):
    """
    Translate text to a target language.
    """
    try:
        translator = GoogleTranslator(source="auto", target=target_lang)
        translated = translator.translate(text)
        return {"translated_text": translated, "target_language": target_lang}, 200
    except Exception as e:
        return {"error": str(e)}, 400

def get_supported_languages():
    """
    Retrieve list of supported languages.
    """
    langs = GoogleTranslator.get_supported_languages(as_dict=True)
    return {"languages": langs}, 200

def detect_language(text):
    """
    Detect the language of a given text.
    """
    try:
        translator = GoogleTranslator(source="auto", target="en")
        detected = translator.detect(text)
        return {"detected_language": detected}, 200
    except Exception as e:
        return {"error": str(e)}, 400

def translate_batch(texts, target_lang="en"):
    """
    Translate a batch of texts.
    """
    translator = GoogleTranslator(source="auto", target=target_lang)
    try:
        translated_texts = [translator.translate(text) for text in texts]
        return {"translated_texts": translated_texts, "target_language": target_lang}, 200
    except Exception as e:
        return {"error": str(e)}, 400
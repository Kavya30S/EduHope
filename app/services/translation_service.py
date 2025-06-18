import requests

class TranslationService:
    def translate(self, text, source_lang='en', target_lang='es'):
        url = "http://localhost:5001/translate"  # Set up LibreTranslate locally
        data = {"q": text, "source": source_lang, "target": target_lang}
        response = requests.post(url, data=data)
        return response.json().get('translatedText', text)
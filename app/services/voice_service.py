import deepspeech

class VoiceService:
    def __init__(self):
        self.model = deepspeech.Model('deepspeech-0.9.3-models.pbmm')

    def speech_to_text(self, audio_file):
        audio = audio_file.read()
        return self.model.stt(audio)
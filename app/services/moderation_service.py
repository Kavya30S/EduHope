from better_profanity import profanity

class ModerationService:
    def __init__(self):
        profanity.load_censor_words()

    def is_clean(self, text):
        return not profanity.contains_profanity(text)
from textblob import TextBlob

class SentimentService:
    def analyze(self, text):
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        return 'positive' if polarity > 0 else 'negative' if polarity < 0 else 'neutral'
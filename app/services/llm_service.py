from transformers import GPT2Tokenizer, GPT2LMHeadModel

class LLMService:
    def __init__(self):
        self.tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
        self.model = GPT2LMHeadModel.from_pretrained('gpt2')

    def generate_suggestion(self, text):
        inputs = self.tokenizer.encode(text, return_tensors='pt')
        outputs = self.model.generate(inputs, max_length=50, num_return_sequences=1)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
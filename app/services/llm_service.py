from transformers import GPT2LMHeadModel, GPT2Tokenizer
from flask import current_app
import json

# Load model and tokenizer
model_path = current_app.config.get("MODEL_PATH", "gpt2")
tokenizer = GPT2Tokenizer.from_pretrained(model_path)
model = GPT2LMHeadModel.from_pretrained(model_path)

def generate_text(prompt, max_length=100, temperature=0.7):
    """
    Generate text using GPT-2 model with child-friendly adjustments.
    """
    inputs = tokenizer.encode(prompt, return_tensors="pt")
    outputs = model.generate(
        inputs,
        max_length=max_length,
        temperature=temperature,
        top_k=50,
        top_p=0.95,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )
    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return moderate_text(text)

def moderate_text(text):
    """
    Ensure generated text is child-friendly.
    """
    from app.services.moderation_service import moderate_content, check_content_safety
    censored = moderate_content(text)
    if not check_content_safety(censored):
        return "Oops! Let’s try something more fun: Tell me about your favorite adventure!"
    return censored

def get_model_info():
    """
    Retrieve information about the loaded model.
    """
    return {
        "model_name": "GPT-2",
        "model_path": model_path,
        "parameters": model.config.n_embd,
        "tokenizer": tokenizer.__class__.__name__
    }

def generate_story_prompt(user_id, theme):
    """
    Generate a story prompt based on user preferences.
    """
    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    pet = Pet.query.filter_by(user_id=user_id).first()
    pet_name = pet.name if pet else "your magical friend"
    base_prompt = f"Write a fun story for a child about {pet_name} going on a {theme} adventure!"
    story = generate_text(base_prompt)
    return {"story": story}, 200
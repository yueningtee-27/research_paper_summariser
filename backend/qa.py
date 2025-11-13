from openai import OpenAI
client = OpenAI()

def answer_question(context_text: str, question: str) -> str:
    print(f"[backend] Answering question: {question}")
    user_prompt = (
        f"You are an expert research assistant. "
        f"Use the following research paper text to answer concisely and accurately.\n\n"
        f"Paper text:\n{context_text[:200000]}\n\n"
        f"Question: {question}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful research assistant."},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content

from rex_agent.prompts import greeting


def test_greeting_is_fixed_english_text_without_llm():
    # Spoken with session.say(): instant, and avoids Gemini's 400 on an empty conversation.
    g = greeting("Johny")
    assert g.startswith("Hey Johny")
    assert "Rex" in g

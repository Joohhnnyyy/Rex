from rex_agent.config import AgentConfig, llm_providers


def test_llm_providers_follow_router_order_and_skip_missing_keys():
    env = {"GEMINI_API_KEY": "g", "MISTRAL_API_KEY": "m"}
    names = [p.provider for p in llm_providers(env)]
    assert names == ["gemini", "mistral"]


def test_llm_providers_all_keys():
    env = {
        "GEMINI_API_KEY": "g",
        "GROQ_API_KEY": "q",
        "MISTRAL_API_KEY": "m",
        "OPENROUTER_API_KEY": "o",
        "NVIDIA_API_KEY": "n",
    }
    provs = llm_providers(env)
    assert [p.provider for p in provs] == ["gemini", "groq", "nvidia", "mistral", "openrouter"]
    assert provs[1].base_url == "https://api.groq.com/openai/v1"


def test_agent_config_defaults_to_english_only():
    cfg = AgentConfig.from_env({})
    assert cfg.english_only is True
    assert cfg.stt_language == "en-IN"
    assert cfg.tts_language == "en-IN"


def test_multilingual_mode_can_be_switched_back_on():
    cfg = AgentConfig.from_env({"REX_ENGLISH_ONLY": "0"})
    assert cfg.english_only is False
    assert cfg.stt_language == "hi-IN"  # streaming rejects the en-IN,hi-IN pair (1008 policy violation)
    assert cfg.tts_language is None


def test_agent_config_overrides():
    cfg = AgentConfig.from_env({})
    assert cfg.tts_model == "timbre-v2.5"
    assert cfg.user_name == "Johny"
    cfg2 = AgentConfig.from_env({"REX_STT_LANGUAGE": "ta-IN", "REX_TTS_VOICE": "Kaveri", "REX_USER_NAME": "Shanky"})
    assert (cfg2.stt_language, cfg2.tts_voice, cfg2.user_name) == ("ta-IN", "Kaveri", "Shanky")

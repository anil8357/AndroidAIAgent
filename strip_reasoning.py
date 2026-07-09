"""
LiteLLM proxy pre-call hook: strip `reasoning_content` from assistant messages.

Why this exists
---------------
Reasoning models (DeepSeek R1, gpt-oss, Nemotron reasoning, Claude thinking, etc.) return a
`reasoning_content` (and sometimes `thinking_blocks` / `reasoning`) field on the assistant
message. LiteLLM stores it in the conversation. On a later turn — or when a request falls
back to a provider like **Groq** or **Cerebras** — that provider REJECTS any assistant
message containing `reasoning_content`:

    'messages.2' : for 'role:assistant' ... property 'reasoning_content' is unsupported

`drop_params=True` does NOT fix this: it only drops unsupported *top-level* request params,
not nested fields inside `messages`. This hook removes those fields from every outgoing
request so any provider (Groq/Cerebras/OpenRouter/etc.) accepts the history.

Stripping the model's *prior* reasoning from the request is safe — the model doesn't need
its own earlier thinking to continue; only the assistant `content` matters.

Wiring (already done in this repo)
----------------------------------
- docker-compose.yml mounts this file to /app/strip_reasoning.py
- litellm_config.yaml sets:  litellm_settings: { callbacks: strip_reasoning.proxy_handler_instance }
- Reload with:  docker compose down && docker compose up -d --force-recreate
"""

from litellm.integrations.custom_logger import CustomLogger

# Fields some providers reject when present on an assistant message in the request history.
_REASONING_FIELDS = ("reasoning_content", "thinking_blocks", "reasoning")


def _strip(messages):
    if not isinstance(messages, list):
        return
    for msg in messages:
        # message may be a dict (proxy path) — only assistant turns carry these fields
        if isinstance(msg, dict) and msg.get("role") == "assistant":
            for field in _REASONING_FIELDS:
                if field in msg:
                    msg.pop(field, None)


class StripReasoningContent(CustomLogger):
    """Removes reasoning_content/thinking_blocks from assistant messages before every call."""

    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        try:
            _strip(data.get("messages"))
        except Exception:
            # Never block a request because sanitation failed.
            pass
        return data

    # Sync path (some proxy code paths call the sync hook).
    def pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        try:
            _strip(data.get("messages"))
        except Exception:
            pass
        return data


# LiteLLM proxy imports this instance via `strip_reasoning.proxy_handler_instance`.
proxy_handler_instance = StripReasoningContent()

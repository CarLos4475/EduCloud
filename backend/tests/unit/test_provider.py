import json

import httpx
import pytest


def test_provider_stream_requires_completion_and_keeps_observed_usage(monkeypatch):
    from campus.adapters.deepseek import DeepSeekProvider, ProviderFailure

    monkeypatch.setenv("DEEPSEEK_API_KEY", "synthetic-test-key")
    answer = json.dumps(
        {"answer": "Explicación", "citations": [], "insufficientSources": False}
    )
    events = [
        json.dumps(
            {"choices": [{"delta": {"content": answer}, "finish_reason": None}]}
        ),
        json.dumps(
            {
                "choices": [{"delta": {}, "finish_reason": "stop"}],
                "usage": {"total_tokens": 25},
            }
        ),
        "[DONE]",
    ]

    def response(request):
        assert request.url.host == "api.deepseek.com"
        return httpx.Response(200, text="".join(f"data: {e}\n\n" for e in events))

    provider = DeepSeekProvider(transport=httpx.MockTransport(response))
    result, usage = provider.tutor_answer([{"role": "user", "content": "Test"}])
    assert result["answer"] == "Explicación" and usage["total_tokens"] == 25
    events.pop()
    with pytest.raises(ProviderFailure) as interrupted:
        provider.tutor_answer([{"role": "user", "content": "Test"}])
    assert interrupted.value.code == "provider_interrupted"
    assert interrupted.value.usage["total_tokens"] == 25


def test_provider_rejects_rate_limit_and_malformed_json(monkeypatch):
    from campus.adapters.deepseek import DeepSeekProvider, ProviderFailure

    monkeypatch.setenv("DEEPSEEK_API_KEY", "synthetic-test-key")
    provider = DeepSeekProvider(
        transport=httpx.MockTransport(lambda r: httpx.Response(429))
    )
    with pytest.raises(ProviderFailure) as rejected:
        provider.tutor_answer([{"role": "user", "content": "Test"}])
    assert rejected.value.code == "provider_429" and rejected.value.usage == {
        "total_tokens": 0
    }
    provider = DeepSeekProvider(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, text="data: not-json\n\n")
        )
    )
    with pytest.raises(ProviderFailure) as malformed:
        provider.tutor_answer([{"role": "user", "content": "Test"}])
    assert malformed.value.code == "provider_invalid_output"


def test_server_error_is_unknown_usage_and_bad_transcription_keeps_usage(monkeypatch):
    from campus.adapters.deepseek import DeepSeekProvider, ProviderFailure

    monkeypatch.setenv("DEEPSEEK_API_KEY", "synthetic-key")
    provider = DeepSeekProvider(
        transport=httpx.MockTransport(lambda r: httpx.Response(503))
    )
    with pytest.raises(ProviderFailure) as failure:
        provider.tutor_answer([{"role": "user", "content": "Test"}])
    assert failure.value.usage is None
    provider = DeepSeekProvider(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "not JSON"}}],
                    "usage": {"total_tokens": 20},
                },
            )
        )
    )
    with pytest.raises(ProviderFailure) as invalid:
        provider.transcribe_image(b"synthetic")
    assert invalid.value.usage["total_tokens"] == 20


def test_model_json_with_latex_backslashes_is_repaired():
    from campus.adapters.deepseek import parse_model_json

    # Single backslashes that are not valid JSON escapes are doubled, not rejected.
    assert parse_model_json(r'{"a": "$V = I \cdot R \alpha$"}') == {
        "a": r"$V = I \cdot R \alpha$"
    }
    # \frac or \theta start like a JSON escape but must stay LaTeX.
    assert parse_model_json(r'{"a": "$\frac{\theta}{2} \times \beta$"}') == {
        "a": r"$\frac{\theta}{2} \times \beta$"
    }
    # Correctly escaped output and real newlines are untouched.
    assert parse_model_json(r'{"a": "$\\frac{1}{2}$"}') == {"a": r"$\frac{1}{2}$"}
    assert parse_model_json(r'{"a": "uno\nnuevo\ttexto"}') == {"a": "uno\nnuevo\ttexto"}
    with pytest.raises(ValueError):
        parse_model_json("no es json")

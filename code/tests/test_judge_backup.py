"""Judge chain: Jev (TypeSafe) first, Qwen on Bailian HK as backup when
Jev does not respond. Plus the temporary GLM 5.3 Flash slot."""

import json

import httpx
import pytest

from si_console import config, judge, router, telemetry

QWEN_HOST = "cn-hongkong.dashscope.aliyuncs.com"
JEV_URL = "https://api.typesafe.ai/v1/systemone"
OPTIONS = {"t2": "Normal synthesis.", "t3": "Trivial task."}


@pytest.fixture(autouse=True)
def judges(monkeypatch):
    monkeypatch.setattr(config, "JEV_PROVIDER", "typesafe")
    monkeypatch.setattr(config, "JEV_API_KEY", "jev-key")
    monkeypatch.setattr(config, "JEV_URL", JEV_URL)
    monkeypatch.setattr(config, "JEV_MODEL", "jev-1.14.0")
    monkeypatch.setattr(config, "JEV_TIMEOUT_SECONDS", 5)
    monkeypatch.setattr(config, "DASHSCOPE_API_KEY", "bailian-key")
    monkeypatch.setattr(config, "DASHSCOPE_BASE_URL",
                        f"https://{QWEN_HOST}/compatible-mode/v1")
    monkeypatch.setattr(config, "QWEN_JUDGE_MODEL", "qwen-small-test")
    monkeypatch.setattr(config, "QWEN_JUDGE_TIMEOUT_SECONDS", 5)


class Fake:
    """Fake httpx.post. `jev` is a callable returning a Response or
    raising; `qwen` is the JSON text the Qwen judge answers with."""

    def __init__(self, jev, qwen='{"choice": "t3", "confidence": 0.8}'):
        self.jev = jev
        self.qwen = qwen
        self.calls = []

    def __call__(self, url, headers=None, json=None, timeout=None):
        self.calls.append({"url": url, "json": json, "timeout": timeout, "headers": headers})
        req = httpx.Request("POST", url)
        if url == JEV_URL:
            return self.jev(req)
        assert httpx.URL(url).host == QWEN_HOST
        return httpx.Response(200, json={
            "model": json["model"],
            "choices": [{"message": {"content": self.qwen}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 120, "completion_tokens": 12}}, request=req)

    def hosts(self):
        return [httpx.URL(c["url"]).host for c in self.calls]


def jev_timeout(req):
    raise httpx.ReadTimeout("slow", request=req)


def jev_answer(choice="t2", confidence=0.95):
    return lambda req: httpx.Response(200, json={"answers": {"pick": {
        "type": "choice", "choice": choice, "confidence": confidence,
        "probabilities": {choice: confidence}}}, "usage": {"input_tokens": 300}}, request=req)


def test_jev_answers_backup_not_called(monkeypatch):
    fake = Fake(jev_answer())
    monkeypatch.setattr(httpx, "post", fake)
    decision = judge.decide_choice("Pick.", OPTIONS, "state")
    assert decision.backend == "jev" and decision.choice == "t2"
    assert fake.hosts() == ["api.typesafe.ai"]
    assert fake.calls[0]["timeout"] == 5


@pytest.mark.parametrize("failure", [
    jev_timeout,
    lambda req: (_ for _ in ()).throw(httpx.ConnectError("blocked", request=req)),
    lambda req: httpx.Response(503, json={"detail": "overloaded"}, request=req),
    lambda req: httpx.Response(200, text="not json", request=req),
])
def test_no_response_from_jev_uses_qwen_backup(monkeypatch, failure):
    fake = Fake(failure)
    monkeypatch.setattr(httpx, "post", fake)
    decision = judge.decide_choice("Pick.", OPTIONS, {"request": "x"})
    assert decision.backend == "qwen" and decision.choice == "t3"
    assert fake.hosts() == ["api.typesafe.ai", QWEN_HOST]
    qwen = fake.calls[1]
    assert qwen["json"]["model"] == "qwen-small-test"
    assert qwen["json"]["response_format"] == {"type": "json_object"}
    assert qwen["json"]["enable_thinking"] is False
    assert qwen["timeout"] == 5
    assert "t2" in qwen["json"]["messages"][1]["content"]


@pytest.mark.parametrize("jev", [
    jev_answer(confidence=0.2),
    lambda req: httpx.Response(200, json={"answers": {"pick": {"type": "refusal"}}}, request=req),
])
def test_jev_answer_stands_even_if_unusable(monkeypatch, jev):
    """Low confidence or a refusal is an answer, not silence: the backup
    is not asked, and the router uses its T2 default."""
    fake = Fake(jev)
    monkeypatch.setattr(httpx, "post", fake)
    with pytest.raises(judge.JudgeError):
        judge.decide_choice("Pick.", OPTIONS, "s", min_confidence=0.5)
    assert fake.hosts() == ["api.typesafe.ai"]


def test_qwen_cannot_pick_outside_options(monkeypatch):
    monkeypatch.setattr(httpx, "post", Fake(jev_timeout, qwen='{"choice": "t1", "confidence": 1}'))
    with pytest.raises(judge.JudgeError) as exc:
        judge.decide_choice("Pick.", OPTIONS, "s")
    assert exc.value.no_response


def test_qwen_low_confidence_is_rejected(monkeypatch):
    monkeypatch.setattr(httpx, "post", Fake(jev_timeout, qwen='{"choice": "t3", "confidence": 0.3}'))
    with pytest.raises(judge.JudgeError):
        judge.decide_choice("Pick.", OPTIONS, "s", min_confidence=0.5)


def test_only_qwen_configured(monkeypatch):
    monkeypatch.setattr(config, "JEV_API_KEY", "")
    fake = Fake(lambda req: pytest.fail("Jev called"))
    monkeypatch.setattr(httpx, "post", fake)
    assert judge.decide_choice("Pick.", OPTIONS, "s").backend == "qwen"


def test_both_down_router_uses_t2_default(monkeypatch):
    def both_down(url, **kwargs):
        raise httpx.ConnectTimeout("down", request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", both_down)
    decision = router.route("Summarize and debug this " + "x" * 300)
    assert decision.tier == "t2" and decision.reason.endswith("->default")


def test_telemetry_records_both_attempts(monkeypatch):
    monkeypatch.setattr(httpx, "post", Fake(jev_timeout))
    judge.decide_choice("Pick.", OPTIONS, "secret state text", purpose="route")
    rows = list(reversed(telemetry.rows()))
    assert [(r["slot"], r["ok"], r["error_code"]) for r in rows] == [
        ("jev", 0, "NO_RESPONSE"), ("qwen-judge", 1, "")]
    assert "secret state text" not in json.dumps(rows)
    assert "jev-key" not in json.dumps(rows) and "bailian-key" not in json.dumps(rows)


def test_judge_backup_timeout_default_is_5s():
    assert config.QWEN_JUDGE_TIMEOUT_SECONDS == 5


# --- GLM 5.3 Flash until the 5.4 API is out ------------------------------

def test_glm_slot_is_5_3_flash():
    assert "glm-5.3-flash" in config.MODEL_SLOTS and "glm-5.4" not in config.MODEL_SLOTS
    assert config.MODEL_TIERS["t0"]["chain"][-1] == "glm-5.3-flash"
    assert config.MODEL_TIERS["t2"]["chain"][-1] == "glm-5.3-flash"


def test_old_glm_5_4_pin_still_works(monkeypatch):
    monkeypatch.setenv("SI_ORCH_C", "glm-5.4")
    monkeypatch.setenv("SI_ORCH_A_T2", "hy4, glm-5.4")
    assert config._pane_setting("C", "", "auto") == "glm-5.3-flash"
    assert config._pane_setting("A", "_T2", "all") == "hy4,glm-5.3-flash"


# --- Bailian decision model (between Jev and the Qwen chat backup) -------

BAILIAN_URL = "https://llm-abc123.cn-hongkong.maas.aliyuncs.com/compatible-mode/v1/systemone"


def test_bailian_url_from_workspace_id_or_api_host():
    assert config.bailian_decision_url("llm-abc123", "cn-hongkong") == BAILIAN_URL
    assert config.bailian_decision_url("llm-abc123.cn-hongkong.maas.aliyuncs.com", "x") == BAILIAN_URL
    assert config.bailian_decision_url("https://llm-abc123.cn-hongkong.maas.aliyuncs.com/", "x") == BAILIAN_URL
    assert config.bailian_decision_url("", "cn-hongkong") == ""


def _systemone(choice="t3", confidence=0.9):
    return lambda req: httpx.Response(200, json={"model": "decision-model", "answers": {"pick": {
        "type": "choice", "choice": choice, "confidence": confidence,
        "probabilities": {choice: confidence}}}, "usage": {"input_tokens": 80},
        "latency_ms": 52.9}, request=req)


class Fake3(Fake):
    def __init__(self, jev, bailian):
        super().__init__(jev)
        self.bailian = bailian

    def __call__(self, url, headers=None, json=None, timeout=None):
        if url == BAILIAN_URL:
            self.calls.append({"url": url, "json": json, "timeout": timeout, "headers": headers})
            return self.bailian(httpx.Request("POST", url))
        return super().__call__(url, headers=headers, json=json, timeout=timeout)


def test_order_jev_then_bailian_then_qwen(monkeypatch):
    monkeypatch.setattr(config, "BAILIAN_DECISION_URL", BAILIAN_URL)
    monkeypatch.setattr(config, "BAILIAN_DECISION_MODEL", "decision-model")
    assert judge.backends() == ["jev", "bailian", "qwen"]
    fake = Fake3(jev_timeout, _systemone())
    monkeypatch.setattr(httpx, "post", fake)
    decision = judge.decide_choice("Pick.", OPTIONS, {"request": "x"})
    assert decision.backend == "bailian" and decision.choice == "t3"
    assert fake.hosts() == ["api.typesafe.ai", "llm-abc123.cn-hongkong.maas.aliyuncs.com"]
    sent = fake.calls[1]
    assert sent["json"]["model"] == "decision-model"
    assert sent["json"]["questions"]["pick"]["criteria"] == OPTIONS
    assert sent["headers"]["Authorization"] == "Bearer bailian-key"


def test_bailian_down_falls_to_qwen(monkeypatch):
    monkeypatch.setattr(config, "BAILIAN_DECISION_URL", BAILIAN_URL)
    fake = Fake3(jev_timeout, lambda req: httpx.Response(404, text="", request=req))
    monkeypatch.setattr(httpx, "post", fake)
    assert judge.decide_choice("Pick.", OPTIONS, "s").backend == "qwen"
    assert len(fake.calls) == 3


def test_bailian_low_confidence_is_final(monkeypatch):
    monkeypatch.setattr(config, "BAILIAN_DECISION_URL", BAILIAN_URL)
    fake = Fake3(jev_timeout, _systemone(confidence=0.2))
    monkeypatch.setattr(httpx, "post", fake)
    with pytest.raises(judge.JudgeError):
        judge.decide_choice("Pick.", OPTIONS, "s", min_confidence=0.5)
    assert len(fake.calls) == 2  # Qwen not asked

"""Page smoke tests with Streamlit's AppTest and a fake client (NFR3)."""
from streamlit.testing.v1 import AppTest

from portfolio_frontend.api_client import (
    ApiUnreachable,
    AskResult,
    ClassifyResult,
    CorpusSummary,
    DocumentTypeSummary,
    SourceDetail,
)


class FakeClient:
    def __init__(self, **overrides):
        self.healthy = True
        self.summary = CorpusSummary(
            by_type=[DocumentTypeSummary(document_type="rfp", generated=4, ingested=3)],
            total_generated=4,
            total_ingested=3,
            indexed_chunks=0,
        )
        self.ask_result = AskResult(
            answer="The budget is USD 100.",
            sources=["abcdef123456"],
            grounded=True,
            source_details=[
                SourceDetail(checksum="abcdef123456", document_type="rfp", file_name="rfp_0001.pdf")
            ],
        )
        self.error = None
        self.__dict__.update(overrides)

    def is_healthy(self):
        return self.healthy

    def corpus_summary(self):
        if self.error:
            raise self.error
        return self.summary

    def ask(self, question):
        if self.error:
            raise self.error
        return self.ask_result

    def classify(self, text):
        return ClassifyResult(category="Security")


def _corpus_script(client):
    from portfolio_frontend.views import corpus

    corpus.render(client)


def _ask_script(client):
    from portfolio_frontend.views import ask

    ask.render(client)


def _classify_script(client):
    from portfolio_frontend.views import classify

    classify.render(client)


def test_corpus_page_shows_counts_and_index_hint() -> None:
    at = AppTest.from_function(_corpus_script, default_timeout=30, args=(FakeClient(),)).run()

    assert not at.exception
    assert [m.value for m in at.metric] == ["4", "3", "0"]
    assert any("Run indexing" in w.value for w in at.warning)


def test_corpus_page_reports_an_unreachable_api() -> None:
    at = AppTest.from_function(_corpus_script, default_timeout=30, args=(FakeClient(healthy=False),)).run()

    assert not at.exception
    assert any("not reachable" in e.value for e in at.error)


def test_corpus_page_shows_friendly_error_when_the_call_fails() -> None:
    client = FakeClient(error=ApiUnreachable("Cannot reach the API"))
    at = AppTest.from_function(_corpus_script, default_timeout=30, args=(client,)).run()

    assert not at.exception
    assert any("Cannot reach the API" in e.value for e in at.error)


def test_ask_page_shows_answer_and_readable_sources() -> None:
    at = AppTest.from_function(_ask_script, default_timeout=30, args=(FakeClient(),)).run()
    at.text_area[0].input("What is the budget?")
    at.button[0].click().run()

    assert not at.exception
    rendered = " ".join(m.value for m in at.markdown)
    assert "USD 100" in rendered
    assert "rfp - rfp_0001.pdf" in rendered


def test_ask_page_warns_when_not_grounded() -> None:
    client = FakeClient(
        ask_result=AskResult(answer="I don't have enough grounded information.", sources=[], grounded=False)
    )
    at = AppTest.from_function(_ask_script, default_timeout=30, args=(client,)).run()
    at.text_area[0].input("capital of France?")
    at.button[0].click().run()

    assert any("Not grounded" in w.value for w in at.warning)


def test_classify_page_shows_the_category() -> None:
    at = AppTest.from_function(_classify_script, default_timeout=30, args=(FakeClient(),)).run()
    at.text_area[0].input("Must encrypt data with AES-256")
    at.button[0].click().run()

    assert not at.exception
    assert any("Security" in s.value for s in at.success)

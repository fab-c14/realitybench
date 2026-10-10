from benchmark.graders.browser_runner import HeadlessHarness

REAL = "<button onclick=\"fetch('/api/x')\">Go</button>"
FAKE = "<script>window.fetch = async () => new Response('{}');</script><button>Go</button>"
HIDDEN = '<p>Visible</p><p style="display:none">Order confirmed</p><script>// catch (error)</script>'


def test_detects_page_that_replaces_fetch():
    with HeadlessHarness() as harness:
        harness.new_session().load_html(REAL)
        assert not harness.fake_backend
        harness.new_session().load_html(FAKE)
        assert harness.fake_backend


def test_visible_text_ignores_hidden_elements_and_scripts():
    with HeadlessHarness() as harness:
        session = harness.new_session()
        session.load_html(HIDDEN)
        text = session.visible_text()
        assert "visible" in text
        assert "confirmed" not in text
        assert "error" not in text

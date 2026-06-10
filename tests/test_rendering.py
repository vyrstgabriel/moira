from main import reading_to_html


def test_reading_to_html_renders_markdownish_structure():
    html = reading_to_html(
        "# A Reading\n\n"
        "---\n\n"
        "## The Ascendant\n\n"
        "First paragraph.\ncontinued line."
    )

    assert html == (
        "<h2>A Reading</h2>"
        "<hr>"
        "<h3>The Ascendant</h3>"
        "<p>First paragraph.<br>continued line.</p>"
    )


def test_reading_to_html_escapes_model_output():
    html = reading_to_html("## <script>x</script>\n\nA <b>bold</b> & dangerous line.")

    assert "<script>" not in html
    assert "<b>" not in html
    assert html == (
        "<h3>&lt;script&gt;x&lt;/script&gt;</h3>"
        "<p>A &lt;b&gt;bold&lt;/b&gt; &amp; dangerous line.</p>"
    )

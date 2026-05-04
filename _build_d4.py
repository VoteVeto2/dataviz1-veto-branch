"""Builder for dashboard 4: The Committee — sentiment constellation + trip ribbon.

Pure Python module — no marimo imports.
Reads design assets (styles.css, app.jsx) from plan/Claude-Design/ and
composes a self-contained HTML page with React 18 + Babel standalone.
Returns an HTML string suitable for mo.iframe().
"""

import json
from pathlib import Path

_DIR = Path(__file__).resolve().parent


def build_d4_html(data):
    """Build The Committee constellation + trip ribbon dashboard.

    Parameters
    ----------
    data : dict
        Parsed content of data/cleaned_data/data.js with keys: people,
        topics, sentimentMatrix, trips, discussionsByTopic,
        reasonByPersonTopic.

    Returns
    -------
    str
        Full HTML document string for use with mo.iframe().
    """
    data_js = "window.DATA = " + json.dumps(data).replace("</script>", r"<\/script>") + ";"
    css = (_DIR / "plan" / "Claude-Design" / "styles.css").read_text(encoding="utf-8")
    app_jsx = _patch_jsx(
        (_DIR / "plan" / "Claude-Design" / "app.jsx").read_text(encoding="utf-8")
    )

    return "\n".join([
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        '<script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>',
        '<script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>',
        '<script src="https://unpkg.com/@babel/standalone@7/babel.min.js"></script>',
        '<link href="https://fonts.googleapis.com/css2?'
        "family=Fraunces:ital,opsz,wght@0,9..144,100..900;1,9..144,100..900"
        "&family=Inter:wght@100..900"
        "&family=JetBrains+Mono:wght@100..800"
        '&display=swap" rel="stylesheet">',
        "<style>",
        css,
        ".shell { min-width: 1460px; }",
        "</style>",
        "</head>",
        "<body>",
        '<div id="app"></div>',
        "<script>",
        data_js,
        "</script>",
        '<script type="text/babel">',
        app_jsx,
        "</script>",
        "</body>",
        "</html>",
    ])


def _patch_jsx(source):
    """Apply minimal patches to the design JSX for iframe embedding."""
    source = source.replace("\r\n", "\n")

    source = source.replace(
        "  // tweaks integration (very lightweight)\n"
        "  useEffect(() => {\n"
        "    const handler = (ev) => {\n"
        "      const m = ev.data;\n"
        "      if (!m || typeof m !== 'object') return;\n"
        "      if (m.type === '__activate_edit_mode') window.__tweaksOn?.(true);\n"
        "      if (m.type === '__deactivate_edit_mode') window.__tweaksOn?.(false);\n"
        "    };\n"
        "    window.addEventListener('message', handler);\n"
        "    return () => window.removeEventListener('message', handler);\n"
        "  }, []);",
        "  useEffect(() => {\n"
        "    const handler = (e) => {\n"
        "      if (e.key === 'Escape') { setSelected(null); setHovered(null); }\n"
        "    };\n"
        "    window.addEventListener('keydown', handler);\n"
        "    return () => window.removeEventListener('keydown', handler);\n"
        "  }, []);",
    )

    source = source.replace(
        "// esc to clear\n"
        "window.addEventListener('keydown', (e) => {\n"
        "  if (e.key === 'Escape') {\n"
        "    window.__clearFocus?.();\n"
        "  }\n"
        "});\n"
        "\n"
        "const root = ReactDOM.createRoot(document.getElementById('app'));\n"
        "function Mount() {\n"
        "  // wrap App to expose clearFocus\n"
        "  const ref = useRef();\n"
        "  return <App />;\n"
        "}\n"
        "root.render(<App />);",
        "const root = ReactDOM.createRoot(document.getElementById('app'));\n"
        "root.render(<App />);",
    )

    return source

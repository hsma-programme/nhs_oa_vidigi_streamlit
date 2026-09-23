"""Shared code-change highlighting for the exercise pages."""
import difflib
import hashlib
import json

import streamlit as st

_TOKEN_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.")


def _changed_spans(prev: str, curr: str) -> list[dict]:
    """Character ranges in `curr` that differ from `prev`, each widened out to
    the surrounding ``name=value`` token so the highlight reads cleanly."""
    raw: list[list[int]] = []
    for tag, _i1, _i2, j1, j2 in difflib.SequenceMatcher(
        None, prev, curr, autojunk=False
    ).get_opcodes():
        if tag in ("replace", "insert") and j2 > j1:
            raw.append([j1, j2])

    widened: list[list[int]] = []
    for start, end in raw:
        while start > 0 and curr[start - 1] in _TOKEN_CHARS:
            start -= 1
        if start > 0 and curr[start - 1] == "=":  # pull in the `name=` prefix
            start -= 1
            while start > 0 and (curr[start - 1].isalnum() or curr[start - 1] == "_"):
                start -= 1
        while end < len(curr) and curr[end] in _TOKEN_CHARS:
            end += 1
        widened.append([start, end])

    merged: list[list[int]] = []
    for start, end in sorted(widened):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    return [{"start": s, "end": e, "text": curr[s:e]} for s, e in merged]


def flash_on_change(container_key: str, code_text: str) -> None:
    """Briefly highlight (yellow-marker style) the exact tokens in the code
    block ``.st-key-<container_key>`` that changed since the previous run.

    Slider changes trigger a full rerun, so the code re-renders every time. We
    diff against the previous text (kept in session state) and hand the changed
    character ranges to a tiny script. It paints them with the CSS Custom
    Highlight API -- ``Range`` objects registered via ``CSS.highlights``, which
    styles the text **without touching the DOM**. (An earlier version wrapped
    the tokens in ``<mark>``; mutating react-syntax-highlighter's DOM corrupted
    React's reconciliation and made later edits append digits instead of
    replacing them.) The script's body only changes when the code changes, so
    Streamlit re-executes it exactly on those reruns -- never on first render.
    Browsers without the Highlight API just skip the effect.
    """
    state_key = f"_flash_prev_{container_key}"
    prev = st.session_state.get(state_key)
    st.session_state[state_key] = code_text

    spans = _changed_spans(prev, code_text) if prev not in (None, code_text) else []
    payload = json.dumps(
        {
            "key": container_key,
            "nonce": hashlib.md5(code_text.encode("utf-8")).hexdigest()[:8],
            "spans": spans,
        }
    )

    st.html(
        f"""
        <script>
        (function () {{
            const DATA = {payload};
            if (typeof Highlight === "undefined" || !window.CSS || !CSS.highlights) return;
            const scope = document.querySelector(
                ".st-key-" + DATA.key + " [data-testid='stCode']"
            );
            if (!scope) return;
            const root = scope.querySelector("code") || scope;
            const NAME = "tokflash-" + DATA.key;
            const VAR = "--" + NAME;

            window.__tf = window.__tf || {{}};
            let s = window.__tf[DATA.key];
            if (!s) {{
                s = window.__tf[DATA.key] = {{ hl: new Highlight(), raf: 0, timer: 0 }};
                CSS.highlights.set(NAME, s.hl);
            }}
            s.hl.clear();
            cancelAnimationFrame(s.raf);
            clearTimeout(s.timer);
            document.documentElement.style.setProperty(VAR, "0");
            if (!DATA.spans.length) return;

            // char offsets -> DOM Range, walking the (react-owned) text nodes read-only
            const nodes = [];
            let pos = 0, node;
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
            while ((node = walker.nextNode())) {{
                nodes.push([node, pos, pos + node.nodeValue.length]);
                pos += node.nodeValue.length;
            }}
            const full = root.textContent;

            function makeRange(a, z) {{
                let sN, sO, eN, eO;
                for (const rec of nodes) {{
                    if (sN === undefined && a >= rec[1] && a <= rec[2]) {{ sN = rec[0]; sO = a - rec[1]; }}
                    if (z >= rec[1] && z <= rec[2]) {{ eN = rec[0]; eO = z - rec[1]; }}
                }}
                if (sN === undefined || eN === undefined) return null;
                const r = new Range();
                r.setStart(sN, sO);
                r.setEnd(eN, eO);
                return r;
            }}

            let added = 0;
            DATA.spans.forEach(function (span) {{
                let a = span.start, z = span.end;
                if (full.slice(a, z) !== span.text) {{
                    const f = full.indexOf(span.text);   // fall back to a text search
                    if (f < 0) return;
                    a = f; z = f + span.text.length;
                }}
                const r = makeRange(a, z);
                if (r) {{ s.hl.add(r); added++; }}
            }});
            if (!added) return;

            // hold solid, then fade the alpha to 0
            document.documentElement.style.setProperty(VAR, "1");
            const hold = 450, fade = 1100, t0 = performance.now();
            function tick(now) {{
                const k = (now - t0 - hold) / fade;
                if (k >= 1) {{
                    s.hl.clear();
                    document.documentElement.style.setProperty(VAR, "0");
                    return;
                }}
                if (k > 0) document.documentElement.style.setProperty(VAR, String(1 - k));
                s.raf = requestAnimationFrame(tick);
            }}
            s.raf = requestAnimationFrame(tick);
            s.timer = setTimeout(function () {{ s.hl.clear(); }}, hold + fade + 500);
        }})();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


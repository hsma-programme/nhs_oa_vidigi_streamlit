import sys

import streamlit as st

st.set_page_config(page_title="Vidigi Animation Playground", layout="wide")

# The banner is a CSS background-image, so the browser fetches it natively --
# it can't go through stlite's patched fetch. Under stlite (Pyodide) there is
# no server answering /app/static/, so point at the raw file on GitHub; for a
# real server (local dev) keep the pinned, offline-friendly static path.
_UNDER_STLITE = sys.platform == "emscripten"
_BANNER_URL = (
    "https://raw.githubusercontent.com/bergam0t/nhs_oa_vidigi_streamlit/main/static/banner.png"
    if _UNDER_STLITE
    else "/app/static/banner.png"
)

_REPO_URL = "https://github.com/hsma-programme/nhs_oa_vidigi_streamlit"
_SITE_URL = "https://hsma.co.uk"


def _svg_data_uri(view_box: str, path: str) -> str:
    """Percent-encoded SVG data URI for use in a CSS url()."""
    return (
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
        f"viewBox='{view_box}'%3E%3Cpath d='{path}'/%3E%3C/svg%3E"
    )


# GitHub mark (Octicons) and Material "language" globe.
_GITHUB_ICON = _svg_data_uri(
    "0 0 16 16",
    "M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 "
    "0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13"
    "-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66"
    ".07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15"
    "-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 "
    "1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 "
    "1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 "
    "1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z",
)
_WEB_ICON = _svg_data_uri(
    "0 0 24 24",
    "M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 "
    "2 11.99 2zm6.93 6h-2.95c-.32-1.25-.78-2.45-1.38-3.56 1.84.63 3.37 1.91 "
    "4.33 3.56zM12 4.04c.83 1.2 1.48 2.53 1.91 3.96h-3.82c.43-1.43 1.08-2.76 "
    "1.91-3.96zM4.26 14C4.1 13.36 4 12.69 4 12s.1-1.36.26-2h3.38c-.08.66-.14 "
    "1.32-.14 2 0 .68.06 1.34.14 2H4.26zm.82 2h2.95c.32 1.25.78 2.45 1.38 "
    "3.56-1.84-.63-3.37-1.9-4.33-3.56zm2.95-8H5.08c.96-1.66 2.49-2.93 "
    "4.33-3.56C8.81 5.55 8.35 6.75 8.03 8zM12 19.96c-.83-1.2-1.48-2.53-1.91-3.96"
    "h3.82c-.43 1.43-1.08 2.76-1.91 3.96zM14.34 14H9.66c-.09-.66-.16-1.32-.16-2 "
    "0-.68.07-1.35.16-2h4.68c.09.65.16 1.32.16 2 0 .68-.07 1.34-.16 2zm.25 "
    "5.56c.6-1.11 1.06-2.31 1.38-3.56h2.95c-.96 1.65-2.49 2.93-4.33 3.56zM16.36 "
    "14c.08-.66.14-1.32.14-2 0-.68-.06-1.34-.14-2h3.38c.16.64.26 1.31.26 2s-.1 "
    "1.36-.26 2h-3.38z",
)

st.html(
    """
    <style>
    /* ---- Banner across the top navigation bar ---- */
    /* Sized to the viewport width so it spans the content area; the sidebar
       keeps its plain header. */
    header[data-testid="stHeader"] {
        height: 5rem;
        background-image:
            linear-gradient(rgba(0, 0, 0, 0.38), rgba(0, 0, 0, 0.38)),
            url("__BANNER_URL__");
        background-size: 100vw auto;
        background-position: left center;
        background-repeat: no-repeat;
    }

    /* Keep the page tabs and menu readable on top of the banner. */
    header[data-testid="stHeader"] [data-testid="stToolbar"] a,
    header[data-testid="stHeader"] [data-testid="stToolbar"] a span,
    header[data-testid="stHeader"] [data-testid="stToolbar"] button,
    header[data-testid="stHeader"] [data-testid="stToolbar"] svg {
        color: #ffffff !important;
        fill: #ffffff !important;
    }
    header[data-testid="stHeader"] a[data-testid="stTopNavLink"] {
        font-weight: 500;
    }
    header[data-testid="stHeader"] a[data-testid="stTopNavLink"]:hover {
        background: rgba(255, 255, 255, 0.16);
    }
    header[data-testid="stHeader"] a[data-testid="stTopNavLink"][aria-current="page"] {
        background: rgba(255, 255, 255, 0.26);
        font-weight: 700;
    }

    /* ---- Repository / website icon links in the top bar ---- */
    /* Streamlit can't put custom widgets in its header, so these are fixed
       over the right-hand end of it, just left of the toolbar menu. The icons
       are CSS masks (the sanitiser strips inline SVG markup), so they take
       the link colour. */
    .top-bar-links {
        position: fixed;
        top: 0;
        right: 4.5rem;
        height: 5rem;
        display: flex;
        align-items: center;
        gap: 0.25rem;
        z-index: 999991;
    }
    .top-bar-links a {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 0.5rem;
        color: #ffffff;
    }
    .top-bar-links a:hover {
        background: rgba(255, 255, 255, 0.16);
    }
    .top-bar-links .icon {
        display: block;
        width: 1.5rem;
        height: 1.5rem;
        background-color: currentColor;
        -webkit-mask-repeat: no-repeat;
        mask-repeat: no-repeat;
        -webkit-mask-position: center;
        mask-position: center;
        -webkit-mask-size: contain;
        mask-size: contain;
    }
    .top-bar-links .icon-github {
        -webkit-mask-image: url("__GITHUB_ICON__");
        mask-image: url("__GITHUB_ICON__");
    }
    .top-bar-links .icon-web {
        -webkit-mask-image: url("__WEB_ICON__");
        mask-image: url("__WEB_ICON__");
    }

    /* ---- Trim the empty space at the top of the sidebar ---- */
    /* This strip only holds the collapse chevron; shrink it and its margin. */
    section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
        height: 2.5rem;
        margin-bottom: 0.25rem;
    }
    </style>
    """.replace("__BANNER_URL__", _BANNER_URL)
    .replace("__GITHUB_ICON__", _GITHUB_ICON)
    .replace("__WEB_ICON__", _WEB_ICON)
)

# Kept separate from the style block above: a style-only st.html goes to the
# hidden event container and applies globally, which mixed content would break.
st.html(
    f"""
    <div class="top-bar-links">
        <a href="{_REPO_URL}" target="_blank" title="View the code on GitHub"
           aria-label="View the code on GitHub">
            <span class="icon icon-github"></span>
        </a>
        <a href="{_SITE_URL}" target="_blank" title="Visit hsma.co.uk"
           aria-label="Visit hsma.co.uk">
            <span class="icon icon-web"></span>
        </a>
    </div>
    """
)

pg = st.navigation(
    [
        st.Page("page_code_reorder_exercise.py", title="Exercise 1"),
        st.Page("page_generate_animation.py", title="Exercise 2"),
        st.Page("page_generate_dfg.py", title="Exercise 3"),
        st.Page("page_trial_plots.py", title="Exercise 4"),
    ],
    position="top",
)

pg.run()

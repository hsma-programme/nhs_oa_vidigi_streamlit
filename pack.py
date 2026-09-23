from stlitepack import pack

pack(
    app_file="streamlit_app.py",
    extra_files_to_embed=["model.py", ".streamlit/config.toml"],
    prepend_github_path="hsma-programme/nhs_oa_vidigi_streamlit",
    extra_files_to_link=[
        "static/banner.png",
        "page_code_reorder_exercise.py",
        "page_generate_animation.py",
        "page_generate_dfg.py",
        "code_preview.py",
        # Vendored streamlit-dnd (see streamlit_dnd/__init__.py for why). Linked
        # rather than pip-installed: the PyPI wheel pins streamlit>=1.58, which
        # micropip refuses under stlite (bundled Streamlit is 1.57.0). These
        # files are fetched from GitHub raw at runtime, so they must be
        # committed and pushed to `main` for the packed app to load them.
        "streamlit_dnd/__init__.py",
        "streamlit_dnd/frontend/index.html",
        "streamlit_dnd/frontend/main.js",
        "streamlit_dnd/frontend/streamlit-protocol.js",
        "styles.css",
    ],
    run_preview_server=True,
    requirements=[
        # Pin plotly explicitly and ahead of vidigi: vidigi allows
        # plotly<7,>=5.12, and micropip's resolver lands on the newest (6.9.x,
        # "Metadata-Version: 2.4") which it then can't use and won't backtrack
        # from, reporting the whole range as having "no pure Python 3 wheel".
        # 6.0.1 ("Metadata-Version: 2.2") has only bundled deps (narwhals,
        # packaging) in Pyodide 0.29.3.
        "plotly==6.0.1",
        "vidigi>=1.3.1,<2.0.0",
        "simpy",
        "sim-tools",
    ],
    stylesheet_version="1.8.1",
    js_bundle_version="1.8.1",
)

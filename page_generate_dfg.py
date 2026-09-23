"""Exercise 3: explore viDiGi's directly-follows graphs."""

import streamlit as st
from vidigi.process_mapping import add_sim_timestamp, discover_dfg, dfg_to_graphviz

from code_preview import flash_on_change
from model import Model, Param


@st.cache_data(max_entries=32, show_spinner=False)
def simulation_log(parameters, replication_id):
    model = Model(Param(**parameters), replication_id=replication_id)
    model.run_model()
    return model.get_vidigi_event_log()


with open("styles.css") as css:
    st.html(f"<style>{css.read()}</style>")

st.html("""
<style>
::highlight(tokflash-dfg_params) {
    background-color: rgba(253, 224, 71, var(--tokflash-dfg_params, 0));
}
::highlight(tokflash-dfg_code) {
    background-color: rgba(253, 224, 71, var(--tokflash-dfg_code, 0));
}
</style>
""")

intro, description = st.columns(2)
intro.title("DFG Playground")
description.write(
    "Explore a directly-follows graph (DFG): activities are nodes, and arrows "
    "connect consecutive events for each patient. Change the settings to "
    "update the code and graph automatically."
)

with st.sidebar:
    st.markdown("**DFG parameters**")
    direction = st.selectbox("Direction", ["LR", "TB", "RL", "BT"],
                             key="dfg_direction")
    time_metric = st.selectbox("Transition time statistic",
                              ["mean", "median", "min", "max", "standard_deviation"],
                              key="dfg_time_metric")
    time_unit = st.selectbox("Display time unit", ["minutes", "seconds", "hours"],
                             key="dfg_time_unit")
    min_frequency = st.slider("Minimum transition count", 0, 100, 0,
                              key="dfg_min_frequency")
    min_probability = st.slider("Minimum transition probability", 0.0, 1.0, 0.0,
                                step=0.05, key="dfg_min_probability")
    show_node_counts = st.checkbox("Show activity counts", True, key="dfg_node_counts")
    show_edge_counts = st.checkbox("Show transition counts", True, key="dfg_edge_counts")
    show_probabilities = st.checkbox("Show transition probabilities", True, key="dfg_probabilities")
    show_metric = st.checkbox("Show transition time", True, key="dfg_show_metric")
    with st.expander("ADVANCED: Labels and infrequent paths"):
        dashed = st.checkbox("Dash infrequent paths", True, key="dfg_dashed")
        dash_threshold = st.slider("Infrequent path probability threshold", 0.0, 1.0, 0.1,
                                   step=0.05, key="dfg_dash_threshold")
        wrap = st.checkbox("Wrap activity labels", True, key="dfg_wrap")
        wrap_at = st.slider("Wrap labels at (characters)", 5, 60, 15, key="dfg_wrap_at")

    st.divider()
    st.markdown("**Simulation parameters**")
    parameters = dict(
        mean_patient_inter=st.slider("Interarrival time (mins)", 0.1, 30.0, 2.0,
                                     step=0.1, key="dfg_iat"),
        num_receptionists=st.slider("Number of receptionists", 1, 10, 1, key="dfg_receptionists"),
        num_nurses=st.slider("Number of nurses", 1, 10, 1, key="dfg_nurses"),
        num_specialists=st.slider("Number of specialists", 1, 10, 1, key="dfg_specialists"),
        specialist_prob=st.slider("Probability of needing a specialist", 0.0, 1.0, 0.3,
                                  step=0.05, key="dfg_specialist_prob"),
        sim_duration=60 * st.slider("Simulation duration (hours)", 2, 24, 4,
                                    step=1, key="dfg_duration_hours"),
        mean_nurse_consult_time=10,
        sd_nurse_consult_time=4,
    )
    replication_id = st.number_input("Random seed", min_value=1, max_value=100000,
                                     value=1, key="dfg_seed",
                                     help="Keep the seed fixed to compare settings; change it for a new sample.")

tab_build, tab_run = st.tabs(["Build your DFG", "View the DFG"])
with tab_build:
    st.write("Use the sidebar to adjust the simulation and DFG settings. The assembled code updates as you make changes.")
    graph_parameters = dict(
        direction=direction, return_image=False,
        time_metric=time_metric, time_unit=time_unit,
        min_frequency=min_frequency, min_probability=min_probability,
        show_node_counts=show_node_counts, show_edge_counts=show_edge_counts,
        show_transition_probabilities=show_probabilities, show_metric=show_metric,
        dashed_infrequent_paths=dashed, infrequent_path_dash_threshold=dash_threshold,
        wrap_node_labels=wrap, wrap_node_labels_at=wrap_at,
    )
    graph_arguments = [f"{name}={value!r}" for name, value in graph_parameters.items()]
    params_code = "from model import Param, Model\n\nwhat_if_params = Param(\n"
    params_code += "".join(f"    {name}={value!r},\n" for name, value in parameters.items())
    params_code += f")\nmodel = Model(what_if_params, replication_id={replication_id})\nmodel.run_model()\nevent_log = model.get_vidigi_event_log()"
    dfg_code = (
        "from vidigi.process_mapping import (\n"
        "    add_sim_timestamp, discover_dfg, dfg_to_graphviz,\n)\n\n"
        '# The simulation clock is always in minutes.\n'
        'log = add_sim_timestamp(event_log, time_unit="minutes")\n'
        f"nodes, edges = discover_dfg(log, time_unit={time_unit!r})\n\n"
        "graph = dfg_to_graphviz(\n    nodes.copy(), edges.copy(),\n"
        + "".join(
            "    " + ", ".join(graph_arguments[i:i + 2]) + ",\n"
            for i in range(0, len(graph_arguments), 2)
        )
        + ')'
    )
    st.markdown("##### Your code so far")
    left, right = st.columns([0.4, 0.6])
    with left, st.container(key="dfg_params"):
        st.code(params_code, language="python")
    with right, st.container(key="dfg_code"):
        st.code(dfg_code, language="python")
    flash_on_change("dfg_params", params_code)
    flash_on_change("dfg_code", dfg_code)

with tab_run:
    st.write("**The graph refreshes automatically.** Change the random seed to explore another simulation sample.")
    st.info(
        "How close is the observed transition probability on the path to the "
        "specialist to the 'Probability of needing a specialist' you set? "
        "Try a short 2-hour simulation, then increase the duration. Does the "
        "observed probability move closer to your setting as more patients "
        "pass through? Random variation means it won't necessarily get closer "
        "on every run. Make sure 'Show transition probabilities' is enabled."
    )
    st.info(
        "Now set the simulation duration back to the default of 4 hours and "
        "change the random seed, keeping the other settings the same. What "
        "happens to the number of patients at each step and the transition "
        "probabilities for the paths leaving that step? Try a few seeds and "
        "compare the results. Enable 'Show activity counts', 'Show transition "
        "counts' and 'Show transition probabilities' to see these values."
    )
    with st.spinner("Building the directly-follows graph..."):
        event_log = simulation_log(parameters, replication_id)
        log = add_sim_timestamp(event_log, time_unit="minutes")
        nodes, edges = discover_dfg(log, time_unit=time_unit)
        # viDiGi wraps labels in-place; preserve the original discovery tables.
        graph = dfg_to_graphviz(nodes.copy(), edges.copy(), **graph_parameters)
    visible_edges = edges[
        (edges["frequency"] >= min_frequency)
        & (edges["probability"] >= min_probability)
    ]
    if visible_edges.empty:
        st.info("No transitions meet these filters. Lower the minimum count or probability to show arrows.")
    st.caption("Scroll inside the viewer to follow the path. Adjust zoom to see more detail or more of the graph.")
    zoom = st.slider("Graph zoom (%)", 50, 200, 100, step=10, key="dfg_zoom",
                     help="100% uses the graph's natural size. Scroll inside the viewer to explore long paths.")

    # Keep SVG intrinsic dimensions instead of fitting every orientation to the page
    # width. Scope the override to this viewer, including its fullscreen rendering.
    viewer_height = 560 if direction in ("TB", "BT") else 360
    viewer_css = f"""
    <style>
    .st-key-dfg_viewer [data-testid="stGraphVizChart"] {{
        width: 100%;
        height: {viewer_height}px;
        overflow: scroll;
        scrollbar-gutter: stable;
        /* Reset Streamlit's transparent standard scrollbar rules so Chrome
           uses the explicit WebKit track and thumb styles below. */
        scrollbar-width: auto !important;
        scrollbar-color: auto !important;
    }}
    .st-key-dfg_viewer [data-testid="stGraphVizChart"]::-webkit-scrollbar {{
        width: 14px;
        height: 14px;
    }}
    .st-key-dfg_viewer [data-testid="stGraphVizChart"]::-webkit-scrollbar-track {{
        background: #e2e8f0;
        border-radius: 7px;
    }}
    .st-key-dfg_viewer [data-testid="stGraphVizChart"]::-webkit-scrollbar-thumb {{
        background: #64748b;
        border: 3px solid #e2e8f0;
        border-radius: 7px;
    }}
    .st-key-dfg_viewer [data-testid="stGraphVizChart"]::-webkit-scrollbar-thumb:hover {{
        background: #334155;
    }}
    .st-key-dfg_viewer [data-testid="stGraphVizChart"]::-webkit-scrollbar-corner {{
        background: #e2e8f0;
    }}
    .st-key-dfg_viewer [data-testid="stGraphVizChart"] svg {{
        width: auto !important;
        max-width: none !important;
        height: auto !important;
        zoom: {zoom / 100};
        display: block;
        margin: 0 auto;
    }}
    </style>
    """
    st.html(viewer_css)
    with st.container(key="dfg_viewer", border=True):
        st.graphviz_chart(graph, width="stretch")
    st.caption(
        "Counts and probabilities describe observed transitions. Patients still in the "
        "system when the simulation ends have incomplete paths; transition times only "
        "include observed transitions."
    )
    with st.expander("Explore the discovered nodes and edges"):
        st.dataframe(nodes, hide_index=True)
        st.dataframe(edges, hide_index=True)

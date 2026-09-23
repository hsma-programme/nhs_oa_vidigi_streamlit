"""Exercise 3: explore viDiGi's directly-follows graphs."""

import streamlit as st
from vidigi.analysis import activity_occupancy_stats
from vidigi.process_mapping import add_sim_timestamp, discover_dfg, dfg_to_graphviz

from code_preview import flash_on_change
from model import Model, Param


@st.cache_data(max_entries=32, show_spinner=False)
def simulation_log(parameters, random_seed):
    model = Model(Param(**parameters), replication_id=1, random_seed=random_seed)
    model.run_model()
    return model.get_vidigi_event_log()


@st.cache_data(max_entries=32, show_spinner=False)
def occupancy_summary(event_log, snapshot_interval, duration):
    return activity_occupancy_stats(
        event_log, every_x_time_units=snapshot_interval, limit_duration=duration,
    )


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
                             key="dfg_direction",
        help='Choose the direction of flow: LR = left to right, RL = right to left, TB = top to bottom, BT = bottom to top.')
    time_metric = st.selectbox("Transition time statistic",
                              ["mean", "median", "min", "max", "standard_deviation"],
                              key="dfg_time_metric",
        help='Choose the elapsed-time statistic shown on arrows: mean (average), median (middle value), min, max, or standard deviation (spread). Time from a queue to service represents waiting time.')
    time_unit = st.selectbox("Display time unit", ["minutes", "seconds", "hours"],
                             key="dfg_time_unit",
        help='Choose the units used to calculate and display transition times. This does not change the simulation duration or arrival rate.')
    min_frequency = st.slider("Minimum transition count", 0, 100, 0,
                              key="dfg_min_frequency",
        help='Hide arrows with fewer than this many observed transitions. Set to 0 to apply no count filter. This only changes the display, not the simulation.')
    min_probability = st.slider("Minimum transition probability", 0.0, 1.0, 0.0,
                                step=0.05, key="dfg_min_probability",
        help='Hide arrows whose observed probability is below this threshold. For example, 0.1 means 10%. Filtering does not recalculate probabilities.')
    show_node_counts = st.checkbox("Show activity counts", True, key="dfg_node_counts",
        help='Show n on each node: the number of recorded visits to that activity during the run.')
    show_edge_counts = st.checkbox("Show transition counts", True, key="dfg_edge_counts",
        help='Show n on each arrow: how many times patients moved directly between these two activities.')
    show_probabilities = st.checkbox("Show transition probabilities", True, key="dfg_probabilities",
        help='Show p on each arrow: its share of all observed transitions leaving the source activity. For example, p=0.30 means 30%. This is an observed result, not the configured specialist probability.')
    show_metric = st.checkbox("Show transition time", True, key="dfg_show_metric",
        help='Show the selected transition time statistic on each arrow, using the chosen display time unit.')
    show_occupancy = st.checkbox(
        "Show queue and resource occupancy", False, key="dfg_show_occupancy",
        help="Calculate average, minimum and maximum patients waiting or being served at each step. This adds some processing time.",
    )
    with st.expander("ADVANCED: Labels and infrequent paths"):
        occupancy_interval = st.slider(
            "Occupancy snapshot interval (mins)", 1, 15, 1,
            key="dfg_occupancy_interval", disabled=not show_occupancy,
            help="Smaller intervals capture more detail; larger intervals calculate faster.",
        )
        dashed = st.checkbox("Dash infrequent paths", True, key="dfg_dashed",
        help='Draw low-probability paths as dashed arrows so they are easier to spot. This does not remove them or change the simulation.')
        dash_threshold = st.slider("Infrequent path probability threshold", 0.0, 1.0, 0.1,
                                   step=0.05, key="dfg_dash_threshold",
        help='Paths below this observed probability are dashed when Dash infrequent paths is enabled. For example, 0.1 marks paths taken less than 10% of the time.')
        wrap = st.checkbox("Wrap activity labels", True, key="dfg_wrap",
        help='Split long activity labels across multiple lines to keep nodes compact.')
        wrap_at = st.slider("Wrap labels at (characters)", 5, 60, 15, key="dfg_wrap_at",
        help='Set the approximate maximum number of characters per line when Wrap activity labels is enabled.')

    st.divider()
    st.markdown("**Simulation parameters**")
    parameters = dict(
        mean_patient_inter=st.slider("Interarrival time (mins)", 0.1, 30.0, 2.0,
                                     step=0.1, key="dfg_iat",
        help='Average time between patient arrivals. A lower value means more frequent arrivals and usually more pressure on queues.'),
        num_receptionists=st.slider("Number of receptionists", 1, 10, 1, key="dfg_receptionists",
        help='Number of receptionists available at the same time. Each can register one patient at a time.'),
        num_nurses=st.slider("Number of nurses", 1, 10, 1, key="dfg_nurses",
        help='Number of nurses available at the same time. Increasing this can reduce the nursing queue and send patients to the next step sooner.'),
        num_specialists=st.slider("Number of specialists", 1, 10, 1, key="dfg_specialists",
        help='Number of specialists available at the same time. Increasing this can reduce the specialist queue.'),
        specialist_prob=st.slider("Probability of needing a specialist", 0.0, 1.0, 0.3,
                                  step=0.05, key="dfg_specialist_prob",
        help='Chance that a patient needs a specialist after seeing a nurse. For example, 0.3 means 30%. The observed proportion varies between simulation runs.'),
        sim_duration=60 * st.slider("Simulation duration (hours)", 2, 24, 4,
                                    step=1, key="dfg_duration_hours",
        help='How long the simulation runs, in hours. Longer runs include more patients. Patients still waiting or being served at the end have incomplete paths.'),
        mean_nurse_consult_time=10,
        sd_nurse_consult_time=4,
    )
    random_seed = st.number_input("Random seed", min_value=1, max_value=100000,
                                  value=42, key="dfg_seed",
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
        show_occupancy=show_occupancy,
    )
    graph_arguments = [f"{name}={value!r}" for name, value in graph_parameters.items()]
    params_code = "from model import Param, Model\n\nwhat_if_params = Param(\n"
    params_code += "".join(f"    {name}={value!r},\n" for name, value in parameters.items())
    params_code += f")\nmodel = Model(what_if_params, replication_id=1, random_seed={random_seed})\nmodel.run_model()\nevent_log = model.get_vidigi_event_log()"
    occupancy_code = (
        "occupancy_stats = activity_occupancy_stats(\n"
        f"    event_log, every_x_time_units={occupancy_interval},\n"
        f"    limit_duration={parameters['sim_duration']},\n)\n"
        if show_occupancy else "occupancy_stats = None\n"
    )
    dfg_code = (
        ("from vidigi.analysis import activity_occupancy_stats\n" if show_occupancy else "")
        +
        "from vidigi.process_mapping import add_sim_timestamp, discover_dfg, dfg_to_graphviz\n\n"
        '# The simulation clock is always in minutes.\n'
        'log = add_sim_timestamp(event_log, time_unit="minutes")\n'
        + occupancy_code
        + f"nodes, edges = discover_dfg(log, time_unit={time_unit!r}, occupancy_stats=occupancy_stats)\n\n"
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
    st.info(
        "Try enabling 'Show queue and resource occupancy' in the sidebar. "
        "Which steps have the largest average and maximum queues? Compare "
        "these with the number of patients being served, then try adding a "
        "nurse or specialist. How do the queues and resource use change? "
        "These labels describe patients present at a time, rather than the "
        "total number who visited a step."
    )
    with st.spinner("Building the directly-follows graph..."):
        event_log = simulation_log(parameters, random_seed)
        log = add_sim_timestamp(event_log, time_unit="minutes")
        occupancy_stats = (
            occupancy_summary(event_log, occupancy_interval, parameters["sim_duration"])
            if show_occupancy else None
        )
        nodes, edges = discover_dfg(log, time_unit=time_unit, occupancy_stats=occupancy_stats)
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

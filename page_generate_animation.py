from code_preview import flash_on_change

import streamlit as st
from vidigi.utils import create_event_position_df, EventPosition
from vidigi.animation import animate_activity_log
from model import Param, Model  # , Trial


def reset_animation_settings():
    """Explicitly restore widget values, including in stlite."""
    st.session_state.update(
        {
            "entity_icon_set_input": 'Default',
            "resource_icon_input": 'Default',
            "timeline_format_input": 'Elapsed minutes',
            "playback_speed_input": 'Normal',
            "time_interval_input": 1,
            "gap_between_entities_input": 10,
            "gap_between_queue_rows_input": 50,
            "gap_between_resources_input": 10,
            "entity_icon_size_input": 20,
            "wrap_queues_input": 10,
            "step_snapshot_max_input": 10,
            "step_snapshot_limit_gauges_input": False,
            "iat_input": 2.0,
            "num_recep_input": 1,
            "num_nurses_input": 1,
            "num_specialists_input": 1,
            "animation_duration_hours": 2,
            "animation_warm_up": 0,
            "layout_grid_input": False,
            "arrival_x_input": 0,
            "arrival_y_input": 850,
            "arrival_label_input": 'Entrance',
            "receptionist_wait_x_input": 200,
            "receptionist_wait_y_input": 800,
            "receptionist_label_input": 'Waiting for Receptionist',
            "receptionist_seen_x_input": 200,
            "receptionist_seen_y_input": 700,
            "receptionist_seen_input": 'Being Seen by Receptionist',
            "nurse_wait_x_input": 200,
            "nurse_wait_y_input": 550,
            "nurse_wait_label_input": 'Waiting for Nurse',
            "nurse_seen_x_input": 200,
            "nurse_seen_y_input": 450,
            "nurse_seen_label_input": 'Being Seen By Nurse',
            "specialist_wait_x_input": 75,
            "specialist_wait_y_input": 300,
            "specialist_wait_label_input": 'Waiting for Specialist',
            "specialist_seen_x_input": 75,
            "specialist_seen_y_input": 200,
            "specialist_seen_label_input": 'Being Seen By Specialist',
            "depart_x_input": 200,
            "depart_y_input": 50,
            "depart_label_input": 'Exit',
        }
    )
    st.toast("Defaults restored. Updating the controls and code preview...")


ENTITY_ICON_SETS = {
    "Default": None,
    "Walking (all the same)": ["🚶"],
    "Fun": ["😎", "🥳", "🤩", "🤪", "🤠"],
    "Sick faces": ["🤮", "🤢", "🤒", "🤕"],
    "Animals": ["🐶", "🐱", "🐰", "🐼", "🦊"],
    "Space": ["👽", "🤖", "👾", "🚀", "🛸"],
}

RESOURCE_ICONS = {
    "Default": None,
    "Bed": "🛏️",
    "Nurse": "👩‍⚕️",
    "Doctor": "👨‍⚕️",
    "Hospital": "🏥",
    "Chair": "🪑",
    "Computer": "🖥️",
}

TIMELINE_FORMATS = {
    "Elapsed minutes": None,
    "Simulation day and clock (24-hour)": "day_clock",
    "Simulation day and clock (12-hour)": "day_clock_ampm",
}

# Frame and transition durations in milliseconds; normal preserves vidigi's defaults.
PLAYBACK_SPEEDS = {
    "Slow": (800, 1200),
    "Normal": (400, 600),
    "Fast": (200, 300),
}

with open("styles.css") as css:
    st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)

# Page config and the top-banner styling live in streamlit_app.py (the entrypoint).


st.html(
    """
    <style>
    /* ---- Tighten the sliders in the sidebar ---- */

    /* Less space between each widget in the sidebar. */
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.6rem;
    }

    /* Trim the large vertical padding baked into every slider. Keep enough
       headroom above for the always-visible value, and enough below the track
       for the min/max range labels that appear on hover. */
    section[data-testid="stSidebar"] [data-testid="stSlider"] > div:last-child > div {
        padding-top: 1.35rem !important;
        padding-bottom: 0.7rem !important;
    }

    /* Pull each slider a little closer to its label (but leave room for the
       value that sits just above the track). */
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
        margin-bottom: 0.35rem;
    }

    /* Tighten the gap above and below the divider between the two groups. */
    section[data-testid="stSidebar"] hr {
        margin-top: 0.8rem;
        margin-bottom: 0.8rem;
    }

    /* ---- Big call-to-action button on the "Run" tab ---- */
    .st-key-animate_button button {
        min-height: 3.5rem;
        font-size: 1.15rem;
        font-weight: 600;
    }

    /* ---- Let the ADVANCED section recede until you engage with it ---- */
    .st-key-advanced_section {
        opacity: 0.5;
        transition: opacity 200ms ease;
    }
    .st-key-advanced_section:hover,
    .st-key-advanced_section:focus-within {
        opacity: 1;
    }
    .st-key-advanced_section h3 {
        font-size: 1rem;
        font-weight: 600;
        padding-bottom: 0.25rem;
    }

    /* ---- Highlighter flash on the exact code that a slider just changed ---- */
    /* Painted via the CSS Custom Highlight API (no DOM mutation); the alpha is
       driven from JS to fade the mark out. */
    ::highlight(tokflash-code_params) {
        background-color: rgba(253, 224, 71, var(--tokflash-code_params, 0));
    }
    ::highlight(tokflash-code_anim) {
        background-color: rgba(253, 224, 71, var(--tokflash-code_anim, 0));
    }

    /* The flash helper and the style block above ship as empty html elements.
       Leave the top-bar links (from streamlit_app.py) visible. */
    [data-testid="stHtml"]:not(:has(.top-bar-links)) {
        display: none;
    }

    h1 {
        font-size: 1.75rem !important;
    }

    p {
        font-size: 0.8rem !important;
    }

    code {
        font-size: 0.775rem !important;
    }

    </style>
    """
)

col1_intro, col2_intro = st.columns(2)

col1_intro.title("Animation Playground")

with col2_intro:
    st.write("")
    st.write("")
    st.write(
        "**This page gives you a chance to try out a range of key vidigi parameters, interactively building up the code for an animation.**"
    )

with st.sidebar:
    st.button(
        "Reset to defaults",
        key="animation_reset",
        on_click=reset_animation_settings,
        width="stretch",
        help="Restore all animation, simulation and advanced layout settings for Exercise 2.",
    )
    st.caption("Please press once and wait 5 seconds.")
    st.markdown("**Animation Parameters**")
    entity_icon_set = st.selectbox(
        "Entity icon set",
        options=list(ENTITY_ICON_SETS),
        format_func=lambda name: (
            f"{name} — {' '.join(ENTITY_ICON_SETS[name])}"
            if ENTITY_ICON_SETS[name]
            else "Default (vidigi people)"
        ),
        key="entity_icon_set_input",
        help="Icons are assigned to patients from the selected set. Walking gives every patient the same icon.",
    )
    resource_icon_choice = st.selectbox(
        "Resource icon",
        options=list(RESOURCE_ICONS),
        format_func=lambda name: (
            f"{name} — {RESOURCE_ICONS[name]}"
            if RESOURCE_ICONS[name]
            else "Default (blue circle)"
        ),
        key="resource_icon_input",
        help="Use this icon for every receptionist, nurse and specialist resource.",
    )
    custom_entity_icon_list = ENTITY_ICON_SETS[entity_icon_set]
    custom_resource_icon = RESOURCE_ICONS[resource_icon_choice]

    timeline_format = st.selectbox(
        "Timeline format",
        options=list(TIMELINE_FORMATS),
        key="timeline_format_input",
        help="Choose how time appears on the animation timeline. Simulation times remain in minutes.",
    )
    time_display_units = TIMELINE_FORMATS[timeline_format]
    playback_speed = st.selectbox(
        "Playback speed",
        options=list(PLAYBACK_SPEEDS),
        index=1,
        key="playback_speed_input",
        help="Adjusts both the frame duration and movement transition duration. It does not change the time between snapshots.",
    )
    frame_duration, frame_transition_duration = PLAYBACK_SPEEDS[playback_speed]

    time_interval_slider = st.slider(
        "Time between snapshots",
        value=1,
        min_value=1,
        max_value=10,
        key="time_interval_input",
    )
    gap_between_entities_slider = st.slider(
        "Gap between entities",
        value=10,
        min_value=1,
        max_value=100,
        key="gap_between_entities_input",
    )
    gap_between_queue_rows_slider = st.slider(
        "Gap between queue rows",
        value=50,
        min_value=1,
        max_value=100,
        key="gap_between_queue_rows_input",
    )
    gap_between_resources_slider = st.slider(
        "Gap between resources",
        value=10,
        min_value=1,
        max_value=100,
        key="gap_between_resources_input",
    )
    entity_icon_size_slider = st.slider(
        "Entity Icon Size",
        value=20,
        min_value=1,
        max_value=100,
        key="entity_icon_size_input",
    )
    wrap_queues_at = st.slider(
        "Wrap queues at",
        value=10,
        min_value=1,
        max_value=30,
        key="wrap_queues_input",
    )

    maximum_queue = st.slider(
        "Maximum Queue Displayed",
        value=10,
        min_value=0,
        max_value=100,
        key="step_snapshot_max_input",
        help="Best as a multiple of 'Wrap queues at!'",
    )

    step_snapshot_limit_gauges = st.toggle(
        "Use gauges for queue overflows",
        key="step_snapshot_limit_gauges_input",
        help="On: show gauges when queues exceed the maximum displayed. Off: show '+ x more' text. Run the animation to see the change.",
    )

    st.divider()

    st.markdown("**Simulation Parameters**")
    iat_slider = st.slider(
        "Average interarrival time (mins)",
        value=2.0,
        min_value=0.1,
        max_value=30.0,
        key="iat_input",
        step=0.1,
        help="The time between arrivals varies. A lower average interarrival time means patients arrive more frequently on average.",
    )
    num_recep_slider = st.slider(
        "Number of Receptionists",
        value=1,
        min_value=1,
        max_value=10,
        key="num_recep_input",
    )
    num_nurses_slider = st.slider(
        "Number of Nurses",
        value=1,
        min_value=1,
        max_value=10,
        key="num_nurses_input",
    )

    num_specialists_slider = st.slider(
        "Number of Specialists",
        value=1,
        min_value=1,
        max_value=10,
        key="num_specialists_input",
    )
    sim_duration_hours = st.slider(
        "Simulation duration (hours)",
        min_value=2,
        max_value=12,
        value=2,
        key="animation_duration_hours",
        help="Total time simulated, including any animation warm-up period.",
    )
    warm_up_minutes = st.slider(
        "Animation warm-up (mins)",
        min_value=0,
        max_value=sim_duration_hours * 60 - 30,
        value=0,
        step=30,
        key="animation_warm_up",
        help="Hide the start of the run so queues can build before the animation begins. This time is included in the simulation duration.",
    )


tab_build, tab_run = st.tabs(["Build your animation", "Run the animation"])

with tab_build:
    st.write("""
Use the controls in the sidebar to choose entity and resource icons and set the simulation parameters (which feed your `Param` class) and the animation parameters (which feed your `Animation` class). Optionally adjust where each event sits on screen below. The assembled code updates as you make your changes.
""")

    st.info(
        "**TASK:** Experiment with the sidebar controls and watch the highlighted "
        "changes in 'Your code so far' below. Try a slider such as 'Average "
        "interarrival time (mins)' or 'Entity Icon Size', a dropdown such as "
        "'Entity icon set' or 'Playback speed', and the 'Use gauges for queue "
        "overflows' toggle. How does each control change the code? Look for "
        "numbers, lists of icons and True/False values. Does each control "
        "update one argument or several, and does it change the simulation "
        "parameters or the animation parameters? Use 'Reset to defaults' "
        "when you want to start again."
    )

    advanced = st.container(key="advanced_section")
    with advanced.expander(
        "**ADVANCED: Adjust Event Positions**\n\nWant to try changing where each event appears on the screen? Click here to make those changes."
    ):
        setup_mode = st.toggle(
            "Show layout grid",
            key="layout_grid_input",
            help="Show grid lines and axis coordinates in the animation to help position events. Run the animation to see the grid.",
        )
        cola, colb, colc, cold = st.columns(4)

        with cola, st.container(border=True):
            st.markdown("`arrival`")
            arrival_x = st.number_input(
                "x",
                key="arrival_x_input",
                value=0,
                min_value=0,
                max_value=1000,
            )
            arrival_y = st.number_input(
                "y",
                key="arrival_y_input",
                value=850,
                min_value=0,
                max_value=1000,
            )
            arrival_label = st.text_input(
                "Label",
                key="arrival_label_input",
                value="Entrance",
            )
        with colb, st.container(border=True):
            st.markdown("`receptionist_wait_begins`")
            receptionist_wait_x = st.number_input(
                "x",
                key="receptionist_wait_x_input",
                value=200,
                min_value=0,
                max_value=1000,
            )
            receptionist_wait_y = st.number_input(
                "y",
                key="receptionist_wait_y_input",
                value=800,
                min_value=0,
                max_value=1000,
            )
            receptionist_wait_label = st.text_input(
                "Label",
                key="receptionist_label_input",
                value="Waiting for Receptionist",
            )
        with colc, st.container(border=True):
            st.markdown("`being_seen_by_receptionist`")
            receptionist_seen_x = st.number_input(
                "x",
                key="receptionist_seen_x_input",
                value=200,
                min_value=0,
                max_value=1000,
            )
            receptionist_seen_y = st.number_input(
                "y",
                key="receptionist_seen_y_input",
                value=700,
                min_value=0,
                max_value=1000,
            )
            receptionist_seen_label = st.text_input(
                "Label",
                key="receptionist_seen_input",
                value="Being Seen by Receptionist",
            )
        with cold, st.container(border=True):
            st.markdown("`nurse_wait_begins`")
            nurse_wait_x = st.number_input(
                "x",
                key="nurse_wait_x_input",
                value=200,
                min_value=0,
                max_value=1000,
            )
            nurse_wait_y = st.number_input(
                "y",
                key="nurse_wait_y_input",
                value=550,
                min_value=0,
                max_value=1000,
            )
            nurse_wait_label = st.text_input(
                "Label",
                key="nurse_wait_label_input",
                value="Waiting for Nurse",
            )

        cole, colf, colg, colh = st.columns(4)

        with cole, st.container(border=True):
            st.markdown("`being_seen_by_nurse`")
            nurse_seen_x = st.number_input(
                "x",
                key="nurse_seen_x_input",
                value=200,
                min_value=0,
                max_value=1000,
            )
            nurse_seen_y = st.number_input(
                "y",
                key="nurse_seen_y_input",
                value=450,
                min_value=0,
                max_value=1000,
            )
            nurse_seen_label = st.text_input(
                "Label",
                key="nurse_seen_label_input",
                value="Being Seen By Nurse",
            )
        with colf, st.container(border=True):
            st.markdown("`specialist_wait_begins`")
            specialist_wait_x = st.number_input(
                "x",
                key="specialist_wait_x_input",
                value=75,
                min_value=0,
                max_value=1000,
            )
            specialist_wait_y = st.number_input(
                "y",
                key="specialist_wait_y_input",
                value=300,
                min_value=0,
                max_value=1000,
            )
            specialist_wait_label = st.text_input(
                "Label",
                key="specialist_wait_label_input",
                value="Waiting for Specialist",
            )
        with colg, st.container(border=True):
            st.markdown("`being_seen_by_specialist`")
            specialist_seen_x = st.number_input(
                "x",
                key="specialist_seen_x_input",
                value=75,
                min_value=0,
                max_value=1000,
            )
            specialist_seen_y = st.number_input(
                "y",
                key="specialist_seen_y_input",
                value=200,
                min_value=0,
                max_value=1000,
            )
            specialist_seen_label = st.text_input(
                "Label",
                key="specialist_seen_label_input",
                value="Being Seen By Specialist",
            )
        with colh, st.container(border=True):
            st.markdown("`depart`")
            depart_x = st.number_input(
                "x",
                key="depart_x_input",
                value=200,
                min_value=0,
                max_value=1000,
            )
            depart_y = st.number_input(
                "y",
                key="depart_y_input",
                value=50,
                min_value=0,
                max_value=1000,
            )
            depart_label = st.text_input(
                "Label",
                key="depart_label_input",
                value="Exit",
            )

        event_position_df_generated = f"""
create_event_position_df(
    [
        EventPosition(
            event="arrival", x={arrival_x}, y={arrival_y}, label="{arrival_label}"
            ),
        EventPosition(
            event="receptionist_wait_begins", x={receptionist_wait_x}, y={receptionist_wait_y}, label="{receptionist_wait_label}",
        ),
        EventPosition(
            event="being_seen_by_receptionist", x={receptionist_seen_x}, y={receptionist_seen_y}, label="{receptionist_seen_label}", resource="num_receptionists",
        ),
        EventPosition(
            event="nurse_wait_begins", x={nurse_wait_x}, y={nurse_wait_y}, label="{nurse_wait_label}"
        ),
        EventPosition(
            event="being_seen_by_nurse", x={nurse_seen_x}, y={nurse_seen_y}, label="{nurse_seen_label}", resource="num_nurses",
        ),
        EventPosition(
            event="specialist_wait_begins", x={specialist_wait_x}, y={specialist_wait_y}, label="{specialist_wait_label}",
        ),
        EventPosition(
            event="being_seen_by_specialist", x={specialist_seen_x}, y={specialist_seen_y}, label="{specialist_seen_label}", resource="num_specialists",
        ),
        EventPosition(
            event="depart", x={depart_x}, y={depart_y}, label="{depart_label}"
        ),
    ]
)
    """

        st.code(event_position_df_generated)

    st.markdown("##### Your code so far")

    params_code = f"""
from model import Param, Model

what_if_params = Param(
    num_nurses={num_nurses_slider},
    num_receptionists={num_recep_slider},
    num_specialists={num_specialists_slider},
    mean_patient_inter={iat_slider},
    sim_duration={sim_duration_hours * 60},
    mean_nurse_consult_time=10,
    sd_nurse_consult_time=4,
)

what_if_model = Model(
    what_if_params,
    replication_id=1,
    random_seed=42
    )
what_if_model.run_model()
event_log = (
    what_if_model.get_vidigi_event_log()
    )
"""

    event_position_code = f"""
from vidigi.utils import create_event_position_df, EventPosition

layout = create_event_position_df(
    [
        EventPosition(
            event="arrival",
            label="{arrival_label}",
            x={arrival_x}, y={arrival_y},
        ),
        EventPosition(
            event="receptionist_wait_begins",
            label="{receptionist_wait_label}",
            x={receptionist_wait_x}, y={receptionist_wait_y},
        ),
        EventPosition(
            event="being_seen_by_receptionist",
            label="{receptionist_seen_label}",
            x={receptionist_seen_x}, y={receptionist_seen_y},
            resource="num_receptionists",
        ),
        EventPosition(
            event="nurse_wait_begins",
            label="{nurse_wait_label}",
            x={nurse_wait_x}, y={nurse_wait_y},

        ),
        EventPosition(
            event="being_seen_by_nurse",
            label="{nurse_seen_label}",
            x={nurse_seen_x}, y={nurse_seen_y},
            resource="num_nurses",
        ),
        EventPosition(
            event="specialist_wait_begins",
            label="{specialist_wait_label}",
            x={specialist_wait_x}, y={specialist_wait_y},

        ),
        EventPosition(
            event="being_seen_by_specialist",
            label="{specialist_seen_label}",
            x={specialist_seen_x}, y={specialist_seen_y},
            resource="num_specialists",
        ),
        EventPosition(
            event="depart", x={depart_x}, y={depart_y}, label="{depart_label}"
        ),
    ]
)
"""

    anim_code = f"""
from vidigi.animation import animate_activity_log

fig = animate_activity_log(
    event_log=event_log,
    scenario=what_if_params,
    event_position_df=layout,
    plotly_height=600,
    every_x_time_units={time_interval_slider},
    time_display_units={time_display_units!r},
    frame_duration={frame_duration},
    frame_transition_duration={frame_transition_duration},
    setup_mode={setup_mode},
    warm_up={warm_up_minutes},
    entity_icon_size={entity_icon_size_slider},
    custom_entity_icon_list={custom_entity_icon_list!r},
    custom_resource_icon={custom_resource_icon!r},
    gap_between_entities={gap_between_entities_slider},
    wrap_queues_at={wrap_queues_at}, step_snapshot_max={maximum_queue},
    step_snapshot_limit_gauges={step_snapshot_limit_gauges},
    gap_between_resources={gap_between_resources_slider},
    gap_between_queue_rows={gap_between_queue_rows_slider},
)
"""

    # Strip the leading/trailing newline so the rendered text (and therefore
    # the highlight offsets) line up exactly with these strings.
    params_code = params_code.strip("\n")
    anim_code = anim_code.strip("\n")
    event_position_code = event_position_code.strip("\n")

    col_params, col_layout, col_anim = st.columns([0.3, 0.35, 0.35])

    with col_params, st.container(key="code_params"):
        st.code(params_code)

    with col_layout, st.container(key="code_layout"):
        st.code(event_position_code)

    with col_anim, st.container(key="code_anim"):
        st.code(anim_code)

    # Flash each block when its slider-driven code actually changes.
    flash_on_change("code_params", params_code)
    flash_on_change("code_layout", event_position_code)
    flash_on_change("code_anim", anim_code)

    st.info(
        "All done? Scroll back up and click on 'Run the animation' to see what the animation looks like."
    )


class Animation:
    def __init__(self, event_log, params):
        self.event_log = event_log
        self.params = params

        self.layout = create_event_position_df(
            [
                EventPosition(
                    event="arrival",
                    x=arrival_x,
                    y=arrival_y,
                    label=arrival_label,
                ),
                EventPosition(
                    event="receptionist_wait_begins",
                    x=receptionist_wait_x,
                    y=receptionist_wait_y,
                    label=receptionist_wait_label,
                ),
                EventPosition(
                    event="being_seen_by_receptionist",
                    x=receptionist_seen_x,
                    y=receptionist_seen_y,
                    label=receptionist_seen_label,
                    resource="num_receptionists",
                ),
                EventPosition(
                    event="nurse_wait_begins",
                    x=nurse_wait_x,
                    y=nurse_wait_y,
                    label=nurse_wait_label,
                ),
                EventPosition(
                    event="being_seen_by_nurse",
                    x=nurse_seen_x,
                    y=nurse_seen_y,
                    label=nurse_seen_label,
                    resource="num_nurses",
                ),
                EventPosition(
                    event="specialist_wait_begins",
                    x=specialist_wait_x,
                    y=specialist_wait_y,
                    label=specialist_wait_label,
                ),
                EventPosition(
                    event="being_seen_by_specialist",
                    x=specialist_seen_x,
                    y=specialist_seen_y,
                    label=specialist_seen_label,
                    resource="num_specialists",
                ),
                EventPosition(
                    event="depart", x=depart_x, y=depart_y, label=depart_label
                ),
            ]
        )

    def build_animation(self, time_interval=1):
        return animate_activity_log(
            event_log=self.event_log,
            event_position_df=self.layout,
            every_x_time_units=time_interval,
            time_display_units=time_display_units,
            frame_duration=frame_duration,
            frame_transition_duration=frame_transition_duration,
            setup_mode=setup_mode,
            warm_up=warm_up_minutes,
            scenario=self.params,
            gap_between_entities=gap_between_entities_slider,
            step_snapshot_max=maximum_queue,
            step_snapshot_limit_gauges=step_snapshot_limit_gauges,
            gap_between_resources=gap_between_resources_slider,
            plotly_height=600,
            entity_icon_size=entity_icon_size_slider,
            custom_entity_icon_list=custom_entity_icon_list,
            custom_resource_icon=custom_resource_icon,
            gap_between_queue_rows=gap_between_queue_rows_slider,
            wrap_queues_at=wrap_queues_at,
        )


@st.fragment
def render_anim():
    button_run_pressed = st.button(
        "Click to create the animation of the simulation",
        key="animate_button",
        type="primary",
        icon=":material/play_arrow:",
        width="stretch",
    )

    if button_run_pressed:
        # base_case_params = Param()
        # base_case_trial = Trial(base_case_params)
        # base_case_trial.run_trial()
        # base_case_trial.calculate_trial_results()
        # my_event_log = base_case_trial.trial_logger.get_log_by_run(run=0, as_df=True)

        with st.spinner("Running the simulation and building the animation..."):
            base_case_params = Param(
                num_nurses=num_nurses_slider,
                num_receptionists=num_recep_slider,
                num_specialists=num_specialists_slider,
                mean_patient_inter=iat_slider,
                sim_duration=sim_duration_hours * 60,
                mean_nurse_consult_time=10,
                sd_nurse_consult_time=4,
            )

            base_case_model_run = Model(
                base_case_params, replication_id=1, random_seed=42
            )
            base_case_model_run.run_model()
            my_event_log = base_case_model_run.get_vidigi_event_log()

            my_animation = Animation(my_event_log, base_case_params)

            fig = my_animation.build_animation(time_interval=time_interval_slider)

        st.plotly_chart(fig)


with tab_run:
    st.write("""
Finished tweaking the settings? Click the button to see how the changes you've made affect the final animation. You can rerun this as many times as you like!
""")

    st.write(
        "Start with the core activity. The layout and staffing activities are optional if you have time. "
        "Click the button below after each change to rebuild the animation."
    )
    tab_overflow, tab_layout, tab_staffing = st.tabs(
        ["Core: queue overflows", "Extra: show more patients", "Extra: staffing"]
    )
    tab_overflow.info(
        "**TASK:** Click 'Reset to defaults' at the top of the sidebar, then "
        "create the animation. Play it through: which queue builds up? "
        "Reduce 'Average interarrival time (mins)' to 1 and rebuild, keeping the other "
        "settings the same. Patients now arrive more frequently: how do the queues change? "
        "What does '+ x more' tell you about patients who are not shown individually? "
        "Keeping the average interarrival time at 1, turn on the gauges and rebuild. "
        "Which overflow display makes the busier queues easier to interpret? "
        "In 'Build your animation', find the mean_patient_inter and "
        "step_snapshot_limit_gauges arguments that changed."
    )
    tab_layout.info(
        "**TASK:** Keep 'Average interarrival time (mins)' at 1 from the core activity and leave "
        "the other simulation settings fixed. Can you show more patients individually "
        "while keeping the animation readable? Try reducing 'Entity Icon Size' "
        "from 20 to 10, increasing 'Wrap queues at' from 10 to 20 and increasing "
        "'Maximum Queue Displayed' from 10 to 40. Rebuild after each change "
        "to see its effect. Experiment with these three controls: how many patients "
        "can you display without queues overlapping other parts of the layout? "
        "Does showing more icons change the actual queue length, or just how it "
        "is displayed? In the first tab's code, find entity_icon_size, "
        "wrap_queues_at and step_snapshot_max."
    )
    tab_staffing.info(
        "**TASK:** Return 'Time between snapshots' to 1. With an average interarrival time of 2 minutes "
        "and one of each staff member, watch where patients wait. Increase "
        "'Number of Nurses' to 2 and rebuild, keeping the other settings fixed. "
        "How does the nurse queue change, and what happens further along the pathway? "
        "The random seed stays fixed for these runs. What can this single animation "
        "suggest about staffing, and what would you want to check across multiple runs?"
    )

    render_anim()

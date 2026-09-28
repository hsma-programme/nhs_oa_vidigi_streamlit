"""Exercise 1: configure, adapt and reason about vidigi 2 resource logging."""

import random

import streamlit as st
from streamlit_dnd import apply_move, dnd

with open("styles.css") as css:
    st.html(f"<style>{css.read()}</style>")


def choice(label, options, key):
    return st.selectbox(
        label, options, index=None, placeholder="Choose an answer", key=f"ex1_{key}"
    )


def feedback(checks):
    """Report the first misconception without changing the learner's attempt."""
    for valid, hint in checks:
        if not valid:
            st.warning(hint)
            return False
    st.success("Correct — well done!")
    return True


def answer_key(answer):
    """Treat multiselect answers as sets, regardless of selection order."""
    return tuple(sorted(answer)) if isinstance(answer, list) else answer


def resource_class_hint(answer):
    """Explain the selected class's limitation without naming the solution."""
    if answer == "simpy.Store":
        return "simpy.Store can hold nurse objects, but on its own it does not create individually identified nurses or log their use automatically."
    if answer == "VidigiResource":
        return "VidigiResource identifies a single resource, so it would represent only one nurse. This model may need a pool of several identifiable nurses."
    return "Choose a resource class before checking your answer."


def checked_question(render, is_correct, hint, key, remember_success=False):
    """Show a persistent tick beside a correctly checked answer."""
    tick_col, answer_col, check_col = st.columns(
        [0.4, 4, 1], vertical_alignment="bottom"
    )
    with tick_col:
        tick = st.empty()
    with answer_col:
        answer = render()
    with check_col:
        check_pressed = st.button("Check", key=f"ex1_check_{key}", width="stretch")
    if check_pressed:
        correct = is_correct(answer)
        feedback([(correct, hint(answer) if callable(hint) else hint)])
        if remember_success:
            st.session_state[f"ex1_verified_{key}"] = (
                answer_key(answer) if correct else None
            )
    if (
        remember_success
        and answer is not None
        and st.session_state.get(f"ex1_verified_{key}") == answer_key(answer)
    ):
        tick.markdown("✅")
    return answer


def shuffled_starter(items):
    """Start the pathway out of order, including after a board reset."""
    shuffled = list(items)
    while shuffled == items:
        random.shuffle(shuffled)
    return shuffled


def board(
    prefix,
    initial,
    snippets,
    headings,
    fixed_header=None,
    descriptions=None,
    show_headings=True,
    show_reset=True,
):
    """Persistent, reversible drag moves, with a keyboard-friendly alternative."""
    keys = [f"ex1_{prefix}_{i}" for i in range(len(initial))]
    for key, items in zip(keys, initial):
        if key not in st.session_state:
            st.session_state[key] = list(items)
    lists = {key: st.session_state[key] for key in keys}
    for index, (col, key, heading) in enumerate(
        zip(st.columns(len(keys)), keys, headings)
    ):
        with col:
            if show_headings:
                st.subheader(heading)
            if descriptions and descriptions[index]:
                st.write(descriptions[index])
            with st.container(key=key, border=True):
                if index == 0 and fixed_header:
                    # This card shares the same inset as the snippets, but is
                    # excluded from drag/drop and its position calculations.
                    with st.container(key=f"{key}_fixed", border=True):
                        st.caption("Fixed in place")
                        st.code(fixed_header, language="python")
                for item in lists[key]:
                    with st.container(key=f"{key}_{item}", border=True):
                        st.code(snippets[item], language="python")
    event = dnd(
        *keys,
        key=f"ex1_drag_{prefix}",
        placeholder="Drop snippets here",
        indicator="ghost",
        handle=False,
        exclude=[f"{keys[0]}_fixed"] if fixed_header else None,
    )
    if event:
        apply_move(event, lists)
        st.rerun()
    if show_reset and st.button("Reset this board", key=f"ex1_reset_{prefix}"):
        for key in keys:
            del st.session_state[key]
        # Retain component event IDs so a previous drag is not replayed.
        st.rerun()
    return lists[keys[0]]


st.title("Add vidigi logging to your model")
st.write(
    "Work through three short activities using a single nurse stage. We use one model run and EventLogger here; TrialLogger comes in Exercise 4."
)
setup_tab, pathway_tab, log_tab = st.tabs(
    [
        "1. Prepare the model",
        "2. Adapt the pathway",
        "3. Read the log",
    ]
)

with setup_tab:
    st.subheader("Add a logger, replace the resource, and connect them up")
    st.write(
        "We have our original SimPy resource, and need to prep it for vidigi's logging. But first, we need to add the logger itself!"
        "\n\nAnswer and check each question to reveal the code ordering exercise."
    )
    st.code("self.nurse = simpy.Resource(self.env, capacity=self.param.num_nurses)")
    imports = checked_question(
        lambda: st.multiselect(
            "Which new imports do you need? Select one or more options from the list. *Remember - for now we're just going to be adding logs to a single model run, not our whole trial.*",
            [
                "from vidigi.resources import VidigiResource",
                "from vidigi.logging import EventLogger",
                "from vidigi.resources import VidigiStore",
                "from vidigi.logging import TrialLogger",
            ],
            key="ex1_imports",
        ),
        lambda answer: (
            set(answer)
            == {
                "from vidigi.logging import EventLogger",
                "from vidigi.resources import VidigiStore",
            }
        ),
        "Choose the logger for a single run and the store that manages individual resources. VidigiResource represents an individual resource internally.",
        "imports",
        remember_success=True,
    )
    cls = checked_question(
        lambda: choice(
            "What do we need to swap in in place of our existing simpy.Resource class?",
            ["simpy.Store", "VidigiResource", "VidigiStore"],
            "class",
        ),
        lambda answer: answer == "VidigiStore",
        resource_class_hint,
        "class",
        remember_success=True,
    )
    count = checked_question(
        lambda: choice(
            "Our original resource uses capacity to set the number of nurses. Which argument tells the new resource class how many nurses to create?",
            ["capacity", "num_nurses", "n_resources", "num_resources"],
            "count",
        ),
        lambda answer: answer == "num_resources",
        "VidigiStore uses a different argument for the initial number of resources than simpy.Resource.",
        "count",
        remember_success=True,
    )
    logger = checked_question(
        lambda: choice(
            "In addition to a label, what should we pass to the nurse store so it can log resource use?",
            ["self.env", "self.logger", "EventLogger()"],
            "logger",
        ),
        lambda answer: answer == "self.logger",
        "Pass the logger instance you created, rather than its class or the simulation environment.",
        "logger",
        remember_success=True,
    )
    setup_ready = all(
        answer is not None
        and st.session_state.get(f"ex1_verified_{key}") == answer_key(answer)
        for key, answer in (
            ("imports", imports),
            ("class", cls),
            ("count", count),
            ("logger", logger),
        )
    )
    if not setup_ready:
        st.info(
            "Check all four answers correctly to reveal the code ordering exercise."
        )
    else:
        setup_snippets = {
            "env": "        self.env = simpy.Environment()",
            "logger": "        self.logger = EventLogger(env=self.env)",
            "store": f'        self.nurse = {cls or "CLASS"}(\n            self.env,\n            {count or "COUNT_ARGUMENT"}=self.param.num_nurses,\n            logger={logger or "LOGGER"},\n            label="nurse",\n        )',
        }
        st.subheader("Setup order")
        st.write(
            "Finally, drag the indented blocks into the right order below the fixed `Model.__init__()` lines. Each object must exist before another block can use it."
        )
        setup_order = board(
            "setup",
            [["store", "env", "logger"]],
            setup_snippets,
            ["Setup order"],
            fixed_header="class Model:\n    def __init__(self, param):\n        self.param = param",
            show_headings=False,
            show_reset=False,
        )
        if st.button("Check order", key="ex1_check_order", type="primary"):
            feedback(
                [
                    (
                        setup_order == ["env", "logger", "store"],
                        "The logger needs an existing environment, and the store needs an existing logger. Check those dependencies.",
                    )
                ]
            )
        with st.expander("Show a worked setup answer"):
            st.code(
                'from vidigi.logging import EventLogger\nfrom vidigi.resources import VidigiStore\n\nclass Model:\n    def __init__(self, param):\n        self.param = param\n        self.env = simpy.Environment()\n        self.logger = EventLogger(env=self.env)\n        self.nurse = VidigiStore(\n            self.env,\n            num_resources=self.param.num_nurses,\n            logger=self.logger,\n            label="nurse",\n        )'
            )
            st.caption(
                "The label identifies the resource pool. It does not name a treatment event."
            )

with pathway_tab:
    st.subheader("Keep, replace and insert")
    st.write(
        "Assume the nurse store is connected to the logger. The `def attend_clinic` line is fixed at the top of the patient pathway. Reorder the existing code, replace the original nurse request, and weave in the logging statements. Drag any lines you no longer need back to Available snippets. Indentation is supplied on each card."
    )
    snippets = {
        "startq": "    start_q_nurse = self.env.now",
        "old": "    with self.nurse.request() as req:",
        "request": '    with self.nurse.request(\n        entity_id=patient.id,\n        start_event="being_seen_by_nurse",\n        end_event="nurse_treatment_ends",\n    ) as req:',
        "yield": "        yield req",
        "endq": "        end_q_nurse = self.env.now\n        patient.q_time_nurse = end_q_nurse - start_q_nurse",
        "sample": "        sampled_nurse_act_time = self.nurse_consult_time_dist.sample()",
        "timeout": "        yield self.env.timeout(sampled_nurse_act_time)",
        "arrival": "    self.logger.log_arrival(entity_id=patient.id)",
        "queue": '    self.logger.log_queue(entity_id=patient.id, event="nurse_wait_begins")',
        "departure": "    self.logger.log_departure(entity_id=patient.id)",
        "placeholder": '        self.logger.log_queue(entity_id=patient.id, event="being_seen_by_nurse")',
        "manual": '        self.logger.log_resource_use_start(\n            entity_id=patient.id,\n            event="being_seen_by_nurse",\n            resource_id=nurse_obtained.id_attribute,\n        )',
    }
    available = [
        "arrival",
        "request",
        "queue",
        "departure",
        "placeholder",
        "manual",
    ]
    random.Random(17).shuffle(available)
    ordered_starter = ["startq", "old", "yield", "endq", "sample", "timeout"]
    if "ex1_path_starter_shuffled" not in st.session_state:
        # Refresh an untouched board in sessions opened before this change.
        if (
            st.session_state.get("ex1_path_0") == ordered_starter
            and len(st.session_state.get("ex1_path_1", [])) == len(available)
            and set(st.session_state["ex1_path_1"]) == set(available)
        ):
            st.session_state["ex1_path_0"] = shuffled_starter(ordered_starter)
        st.session_state["ex1_path_starter_shuffled"] = True
    # Preserve learners' discarded snippets when an open session moves from
    # the former three-column board to this two-column version.
    if "ex1_path_2" in st.session_state:
        discarded = st.session_state.pop("ex1_path_2")
        st.session_state.setdefault(
            "ex1_path_1",
            [
                item
                for item in available
                if item not in st.session_state.get("ex1_path_0", [])
            ],
        )
        st.session_state["ex1_path_1"].extend(
            item
            for item in discarded
            if item not in st.session_state["ex1_path_1"]
            and item not in st.session_state.get("ex1_path_0", [])
        )
    pathway = board(
        "path",
        [shuffled_starter(ordered_starter), available],
        snippets,
        ["Patient pathway", "Available snippets"],
        fixed_header="def attend_clinic(self, patient):",
        descriptions=[
            "The original simulation lines have been deliberately mixed up. Put them back in the order a patient would experience them: start waiting, request and obtain a nurse, record the wait, then complete treatment. After that, insert the logging snippets and replace the old request.",
            "Drag new snippets into the pathway. Drag replaced or unwanted pathway code back here; unused suggestions can stay here too.",
        ],
    )
    required = [
        "arrival",
        "startq",
        "queue",
        "request",
        "yield",
        "endq",
        "sample",
        "timeout",
        "departure",
    ]
    rules = [
        ("arrival", "queue", "Log arrival before the waiting stage."),
        (
            "startq",
            "request",
            "Record the start of the wait before requesting a nurse.",
        ),
        (
            "queue",
            "request",
            "Log waiting before requesting the resource, even when a nurse might be immediately available.",
        ),
        ("request", "yield", "Create the request before yielding it."),
        (
            "yield",
            "endq",
            "The patient must obtain the nurse before you record the end of their wait.",
        ),
        (
            "endq",
            "sample",
            "Record the queue time before sampling the consultation duration.",
        ),
        (
            "sample",
            "timeout",
            "Sample the consultation duration before using it in the timeout.",
        ),
        (
            "timeout",
            "departure",
            "Log departure after treatment, outside the resource's with block.",
        ),
    ]
    if st.button("Check pathway", key="ex1_check_path", type="primary"):
        checks = [
            (
                "old" not in pathway,
                "Replace the original request: move it out of the pathway.",
            ),
            (
                "placeholder" not in pathway,
                "The store now records treatment start automatically. Remove the temporary treatment-as-a-queue event.",
            ),
            (
                "manual" not in pathway,
                "The configured store records resource use automatically. You do not need this manual call or nurse_obtained.",
            ),
            (
                set(pathway) == set(required) and len(pathway) == len(required),
                "Keep all the simulation steps and add arrival, waiting, departure and the replacement request.",
            ),
        ]
        if set(pathway) == set(required):
            checks += [
                (pathway.index(a) < pathway.index(b), hint) for a, b, hint in rules
            ]
        feedback(checks)
    with st.expander("Show a worked pathway answer"):
        answer = dict(snippets)
        answer["request"] = (
            '    with self.nurse.request(\n        entity_id=patient.id,\n        start_event="being_seen_by_nurse",\n        end_event="nurse_treatment_ends",\n    ) as req:'
        )
        st.code(
            "def attend_clinic(self, patient):\n"
            + "\n".join(answer[x] for x in required)
        )
        st.caption(
            "Other valid placements of the queue timer are accepted. Automatic logging adds resource-use start on acquisition and end on release; arrival, waiting and departure still need explicit calls."
        )

with log_tab:
    st.subheader("From event log to animation snapshots")
    st.write(
        "Patient 7 arrives at minute 2 and immediately joins the nurse queue. The nurse becomes available at minute 5. Treatment lasts 4 minutes, then the patient leaves. The model runs beyond minute 9."
    )
    st.markdown(
        """| entity_id | event | time | resource_id |
| --- | --- | ---: | ---: |
| 7 | arrival | 2 | — |
| 7 | nurse_wait_begins | 2 | — |
| 7 | being_seen_by_nurse | 5 | 1 |
| 7 | nurse_treatment_ends | 9 | 1 |
| 7 | depart | 9 | — |"""
    )
    st.caption(
        "Illustrative excerpt assuming this nurse has resource ID 1. Waiting lasts 3 minutes; treatment lasts 4."
    )
    st.write(
        "At each snapshot, vidigi uses the latest event each patient has reached to decide where to show them. Patients who have departed no longer appear."
    )
    snapshot_time = st.selectbox(
        "Choose a snapshot time (minutes)",
        [4, 6, 10],
        index=None,
        placeholder="Choose a time",
        key="ex1_snapshot_time",
    )
    location = choice(
        "Where will patient 7 appear?",
        ["Waiting for a nurse", "With the nurse", "No longer in the animation"],
        "snapshot_location",
    )
    if st.button("Check answer", key="ex1_check_log", type="primary"):
        if snapshot_time is None or location is None:
            st.warning("Choose a snapshot time and a patient position first.")
        else:
            positions = {
                4: "Waiting for a nurse",
                6: "With the nurse",
                10: "No longer in the animation",
            }
            explanations = {
                4: "At minute 4, the latest event is `nurse_wait_begins` at minute 2, so patient 7 is still waiting.",
                6: "At minute 6, the latest event is `being_seen_by_nurse` at minute 5, so patient 7 is with the nurse.",
                10: "Patient 7 departed at minute 9, so they are absent from the minute 10 snapshot.",
            }
            feedback(
                [
                    (
                        location == positions[snapshot_time],
                        "Look for the last event at or before this time, and check whether the patient has departed.",
                    )
                ]
            )
            st.info(explanations[snapshot_time])
    st.info(
        "In Exercise 2, try changing the time between snapshots. Wider gaps create fewer frames and can skip over short-lived states. The layout event names must match the log."
    )

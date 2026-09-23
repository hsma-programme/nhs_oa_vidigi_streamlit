"""Exercise 1: configure, adapt and reason about vidigi 2 resource logging."""

import random

import pandas as pd
import streamlit as st
from streamlit_dnd import apply_move, dnd

with open("styles.css") as css:
    st.html(f"<style>{css.read()}</style>")


def choice(label, options, key):
    return st.selectbox(label, options, index=None, placeholder="Choose an answer", key=f"ex1_{key}")


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
    if answer == "simpy.Resource":
        return "simpy.Resource can represent several nurses, but it does not track which individual nurse treats a patient. The animation needs those individual IDs."
    if answer == "VidigiResource":
        return "VidigiResource identifies a single resource, so it would represent only one nurse. This model may need a pool of several identifiable nurses."
    return "Choose a resource class before checking your answer."


def checked_question(render, is_correct, hint, key, remember_success=False):
    """Put a check button beside one answer and show feedback beneath it."""
    answer_col, check_col = st.columns([4, 1], vertical_alignment="bottom")
    with answer_col:
        answer = render()
    with check_col:
        check_pressed = st.button("Check", key=f"ex1_check_{key}", width="stretch")
    if check_pressed:
        correct = is_correct(answer)
        feedback([(correct, hint(answer) if callable(hint) else hint)])
        if remember_success:
            st.session_state[f"ex1_verified_{key}"] = answer_key(answer) if correct else None
    return answer


def shuffled_starter(items):
    """Start the pathway out of order, including after a board reset."""
    shuffled = list(items)
    while shuffled == items:
        random.shuffle(shuffled)
    return shuffled


def board(prefix, initial, snippets, headings, fixed_header=None, descriptions=None):
    """Persistent, reversible drag moves, with a keyboard-friendly alternative."""
    keys = [f"ex1_{prefix}_{i}" for i in range(len(initial))]
    for key, items in zip(keys, initial):
        if key not in st.session_state:
            st.session_state[key] = list(items)
    lists = {key: st.session_state[key] for key in keys}
    for index, (col, key, heading) in enumerate(zip(st.columns(len(keys)), keys, headings)):
        with col:
            st.subheader(heading)
            if descriptions and descriptions[index]:
                st.write(descriptions[index])
            if index == 0 and fixed_header:
                st.caption("Fixed in place")
                st.code(fixed_header, language="python")
            with st.container(key=key, border=True):
                for item in lists[key]:
                    with st.container(key=f"{key}_{item}", border=True):
                        st.code(snippets[item], language="python")
    event = dnd(*keys, key=f"ex1_drag_{prefix}", placeholder="Drop snippets here", indicator="ghost")
    if event:
        apply_move(event, lists)
        st.rerun()
    with st.container(key=f"ex1_keyboard_{prefix}"):
        with st.expander("Having trouble dragging? Move snippets without dragging"):
            st.caption("Use these controls only if drag and drop is difficult on your device.")
            item = st.selectbox("Snippet", list(snippets), format_func=lambda x: snippets[x].strip(), key=f"ex1_move_{prefix}")
            dest = st.selectbox("Destination", keys, format_func=lambda x: headings[keys.index(x)], key=f"ex1_dest_{prefix}")
            position = st.number_input("Position (1 = first)", min_value=1, max_value=len(snippets), key=f"ex1_pos_{prefix}")
            if st.button("Move snippet", key=f"ex1_move_button_{prefix}"):
                for items in lists.values():
                    if item in items:
                        items.remove(item)
                lists[dest].insert(min(int(position)-1, len(lists[dest])), item)
                st.rerun()
    if st.button("Reset this board", key=f"ex1_reset_{prefix}"):
        for key in keys:
            del st.session_state[key]
        # Retain component event IDs so a previous drag is not replayed.
        st.rerun()
    return lists[keys[0]]


st.title("Add vidigi logging to your model")
st.write("Work through three activities using a single nurse stage, then try the optional registration challenge. We use one model run and EventLogger here; TrialLogger comes in Exercise 4.")
setup_tab, pathway_tab, log_tab, extension_tab = st.tabs([
    "1. Prepare the model", "2. Adapt the pathway", "3. Predict the log", "Optional: registration"
])

with setup_tab:
    st.subheader("Replace the resource and connect the logger")
    st.write("Start with the original SimPy resource. Answer and check each question to reveal the code ordering exercise.")
    st.code("self.nurse = simpy.Resource(self.env, capacity=self.param.num_nurses)")
    imports = checked_question(
        lambda: st.multiselect("Which new imports do you need? Select one or more options from the list. Remember - for now we're just going to be adding logs to a single model run, not our whole trial.", [
            "from vidigi.resources import VidigiResource",
            "from vidigi.logging import EventLogger",
            "from vidigi.resources import VidigiStore",
            "from vidigi.logging import TrialLogger",
        ], key="ex1_imports"),
        lambda answer: set(answer) == {"from vidigi.logging import EventLogger", "from vidigi.resources import VidigiStore"},
        "Choose the logger for a single run and the store that manages individual resources. VidigiResource represents an individual resource internally.",
        "imports",
        remember_success=True,
    )
    cls = checked_question(
        lambda: choice(
            "What do we need to swap in in place of our existing simpy.Resource class?",
            ["simpy.Resource", "VidigiResource", "VidigiStore"],
            "class",
        ),
        lambda answer: answer == "VidigiStore",
        resource_class_hint,
        "class",
        remember_success=True,
    )
    count = checked_question(
        lambda: choice("Our original resource uses capacity to set the number of nurses. Which argument tells the new resource class how many nurses to create?", ["capacity", "num_resources"], "count"),
        lambda answer: answer == "num_resources",
        "VidigiStore uses a different argument for the initial number of resources than simpy.Resource.",
        "count",
        remember_success=True,
    )
    logger = checked_question(
        lambda: choice("We have created a logger in Model.__init__(). What should we pass to the nurse store so it can log resource use?", ["self.env", "self.logger", "EventLogger"], "logger"),
        lambda answer: answer == "self.logger",
        "Pass the logger instance you created, rather than its class or the simulation environment.",
        "logger",
        remember_success=True,
    )
    setup_ready = all(
        answer is not None and st.session_state.get(f"ex1_verified_{key}") == answer_key(answer)
        for key, answer in (("imports", imports), ("class", cls), ("count", count), ("logger", logger))
    )
    if not setup_ready:
        st.info("Check all four answers correctly to reveal the code ordering exercise.")
    else:
        setup_snippets = {
            "env": "        self.env = simpy.Environment()",
            "logger": "        self.logger = EventLogger(env=self.env)",
            "store": f'        self.nurse = {cls or "CLASS"}(\n            self.env,\n            {count or "COUNT_ARGUMENT"}=self.param.num_nurses,\n            logger={logger or "LOGGER"},\n            label="nurse",\n        )',
        }
        st.caption('The label="nurse" line is supplied for you; it identifies the resource pool in the event log.')
        st.write("Finally, drag the indented blocks into the right order below the fixed `Model.__init__()` lines. Each object must exist before another block can use it.")
        st.caption("Fixed starting code — this block cannot be dragged.")
        st.code("class Model:\n    def __init__(self, param):\n        self.param = param", language="python")
        setup_order = board("setup", [["store", "env", "logger"]], setup_snippets, ["Setup order"])
        if st.button("Check order", key="ex1_check_order"):
            feedback([(setup_order == ["env", "logger", "store"], "The logger needs an existing environment, and the store needs an existing logger. Check those dependencies.")])
        if st.button("Check setup", key="ex1_check_setup", type="primary"):
            feedback([
                (set(imports) == {"from vidigi.logging import EventLogger", "from vidigi.resources import VidigiStore"}, "Choose the logger for a single run and the store that manages individual resources. VidigiResource represents an individual resource internally."),
                (cls == "VidigiStore", resource_class_hint(cls)),
                (count == "num_resources", "VidigiStore uses a different argument for the initial number of resources than simpy.Resource."),
                (logger == "self.logger", "Pass the logger instance you created, rather than its class or the simulation environment."),
                (setup_order == ["env", "logger", "store"], "The logger needs an existing environment, and the store needs an existing logger. Check those dependencies."),
            ])
        with st.expander("Show a worked setup answer"):
            st.code('from vidigi.logging import EventLogger\nfrom vidigi.resources import VidigiStore\n\nclass Model:\n    def __init__(self, param):\n        self.param = param\n        self.env = simpy.Environment()\n        self.logger = EventLogger(env=self.env)\n        self.nurse = VidigiStore(\n            self.env,\n            num_resources=self.param.num_nurses,\n            logger=self.logger,\n            label="nurse",\n        )')
            st.caption("The label identifies the resource pool. It does not name a treatment event.")

with pathway_tab:
    st.write("First, choose the patient ID and the two event names for the replacement nurse request. Check each answer to unlock the code exercise.")
    entity = checked_question(
        lambda: choice("entity_id: which value identifies this patient?", ["self.replication_id", "patient.id", "self.param.num_nurses"], "entity"),
        lambda answer: answer == "patient.id",
        "Resource logging needs this patient's ID, not a replication ID or a resource count.",
        "entity",
        remember_success=True,
    )
    start = checked_question(
        lambda: choice("start_event: what should we call the start of nurse treatment?", ["nurse_wait_begins", "being_seen_by_nurse", "nurse_treatment_ends"], "start"),
        lambda answer: answer == "being_seen_by_nurse",
        "The start event marks treatment after the patient obtains a nurse. Waiting begins before that.",
        "start",
        remember_success=True,
    )
    end = checked_question(
        lambda: choice("end_event: what should we call the end of nurse treatment?", ["depart", "nurse_treatment_ends", "being_seen_by_nurse"], "end"),
        lambda answer: answer == "nurse_treatment_ends",
        "The end event marks release of the nurse. Departure is logged separately after treatment.",
        "end",
        remember_success=True,
    )
    request_ready = all(
        answer is not None and st.session_state.get(f"ex1_verified_{key}") == answer
        for key, answer in (("entity", entity), ("start", start), ("end", end))
    )
    if not request_ready:
        st.info("Check all three answers correctly to reveal the code exercise.")
    else:
        st.subheader("Keep, replace and insert")
        st.write("Assume the nurse store is connected to the logger. The `def attend_clinic` line is fixed at the top of the patient pathway. Reorder the existing code, replace the original nurse request, and weave in the logging statements. Drag any lines you no longer need back to Available snippets. Indentation is supplied on each card.")
        snippets = {
            "startq": "    start_q_nurse = self.env.now",
            "old": "    with self.nurse.request() as req:",
            "request": f'    with self.nurse.request(\n        entity_id={entity or "ENTITY_ID"},\n        start_event={start or "START_EVENT"!r},\n        end_event={end or "END_EVENT"!r},\n    ) as req:',
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
        available = ["arrival", "request", "queue", "departure", "placeholder", "manual"]
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
                [item for item in available if item not in st.session_state.get("ex1_path_0", [])],
            )
            st.session_state["ex1_path_1"].extend(
                item for item in discarded
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
        required = ["arrival", "startq", "queue", "request", "yield", "endq", "sample", "timeout", "departure"]
        rules = [
            ("arrival", "queue", "Log arrival before the waiting stage."),
            ("startq", "request", "Record the start of the wait before requesting a nurse."),
            ("queue", "request", "Log waiting before requesting the resource, even when a nurse might be immediately available."),
            ("request", "yield", "Create the request before yielding it."),
            ("yield", "endq", "The patient must obtain the nurse before you record the end of their wait."),
            ("endq", "sample", "Record the queue time before sampling the consultation duration."),
            ("sample", "timeout", "Sample the consultation duration before using it in the timeout."),
            ("timeout", "departure", "Log departure after treatment, outside the resource's with block."),
        ]
        if st.button("Check pathway", key="ex1_check_path", type="primary"):
            checks = [
                (entity == "patient.id", "Resource logging needs this patient's ID, not a replication ID or a resource count."),
                (start == "being_seen_by_nurse" and end == "nurse_treatment_ends", "The request names treatment start and end; waiting and departure are separate events."),
                ("old" not in pathway, "Replace the original request: move it out of the pathway."),
                ("placeholder" not in pathway, "The store now records treatment start automatically. Remove the temporary treatment-as-a-queue event."),
                ("manual" not in pathway, "The configured store records resource use automatically. You do not need this manual call or nurse_obtained."),
                (set(pathway) == set(required) and len(pathway) == len(required), "Keep all the simulation steps and add arrival, waiting, departure and the replacement request."),
            ]
            if set(pathway) == set(required):
                checks += [(pathway.index(a) < pathway.index(b), hint) for a, b, hint in rules]
            feedback(checks)
        with st.expander("Show a worked pathway answer"):
            answer = dict(snippets)
            answer["request"] = '    with self.nurse.request(\n        entity_id=patient.id,\n        start_event="being_seen_by_nurse",\n        end_event="nurse_treatment_ends",\n    ) as req:'
            st.code("def attend_clinic(self, patient):\n" + "\n".join(answer[x] for x in required))
            st.caption("Other valid placements of the queue timer are accepted. Automatic logging adds resource-use start on acquisition and end on release; arrival, waiting and departure still need explicit calls.")

with log_tab:
    st.subheader("Predict before inspecting")
    st.write("Patient 7 arrives at minute 2 and immediately joins the nurse queue. The nurse becomes available at minute 5. Treatment lasts 4 minutes, then the patient leaves. The model runs beyond minute 9.")
    events = ["arrival", "nurse_wait_begins", "being_seen_by_nurse", "nurse_treatment_ends", "depart"]
    expected_times = [2, 2, 5, 9, 9]
    expected_sources = ["Explicit call", "Explicit call", "Automatic resource logging", "Automatic resource logging", "Explicit call"]
    predictions = []
    for event_name in events:
        with st.container(border=True):
            st.write(f"`{event_name}`")
            a, b = st.columns(2)
            with a:
                time = choice("Time (minutes)", [2, 5, 9], f"time_{event_name}")
            with b:
                source = choice("Recorded by", ["Explicit call", "Automatic resource logging"], f"source_{event_name}")
            predictions.append((time, source))
    waiting = choice("Does passing entity_id remove the need to log waiting?", ["Yes", "No"], "waiting")
    release = choice("What triggers the resource-use end event in this pathway?", ["Reaching the timeout statement", "Releasing the nurse when the with block exits", "Logging departure"], "release")
    if st.button("Check predictions", key="ex1_check_log", type="primary"):
        checks = []
        for event_name, predicted, time, source in zip(events, predictions, expected_times, expected_sources):
            checks.append((predicted == (time, source), f"Reconsider {event_name}: distinguish arriving, obtaining the nurse and finishing treatment, then decide whether the pathway or store records it."))
        checks.extend([
            (waiting == "No", "The store records resource use; the pathway still needs to record joining the queue."),
            (release == "Releasing the nurse when the with block exits", "The resource is released on leaving the with block. Merely reaching a timeout statement does not release it."),
        ])
        feedback(checks)
    with st.expander("Reveal the expected event log"):
        st.dataframe(pd.DataFrame({"entity_id": [7]*5, "event": events, "time": expected_times, "resource_id": [None, None, 1, 1, None], "recorded_by": expected_sources}), hide_index=True)
        st.caption("Illustrative excerpt assuming this nurse has resource ID 1. recorded_by is an explanatory column added for this exercise. Both resource events refer to the same nurse. Waiting lasts 3 minutes; treatment lasts 4.")
    st.info("In Exercise 2 you will position these events in an animation. Its layout event names must match the log; resource counts come from your model parameters.")

with extension_tab:
    st.subheader("Transfer the changes to registration")
    st.write("Your original model has registration before the nurse. Complete the receptionist setup and request with fewer hints. Assume self.logger already exists.")
    st.code('self.receptionist = CLASS(\n    self.env,\n    COUNT_ARGUMENT=self.param.num_receptionists,\n    logger=LOGGER,\n    label="receptionist",\n)\n\nwith self.receptionist.request(\n    entity_id=ENTITY_ID,\n    start_event="being_seen_by_receptionist",\n    end_event="receptionist_visit_ends",\n) as req:\n    yield req\n    # Existing registration calculation and timeout stay here.')
    values = [st.text_input(label, key=f"ex1_reg_{key}") for label, key in [
        ("CLASS", "class"), ("COUNT_ARGUMENT", "count"), ("LOGGER", "logger"), ("ENTITY_ID", "entity")]]
    boundary = choice("Where do arrival and departure belong in the two-stage clinic?", ["Around each resource stage", "One arrival before registration and one departure after the nurse", "Only around registration"], "boundary")
    if st.button("Check registration", key="ex1_check_reg", type="primary"):
        feedback([
            (values[0].strip() == "VidigiStore", "Choose the class that manages identifiable resources."),
            (values[1].strip() == "num_resources", "Use the store's argument for the number of receptionists."),
            (values[2].strip() == "self.logger", "Use the existing logger instance."),
            (values[3].strip() == "patient.id", "Identify the patient making this request."),
            (boundary == "One arrival before registration and one departure after the nurse", "Arrival and departure describe the whole clinic visit. Each stage has its own waiting and treatment events."),
        ])
    with st.expander("Show a worked registration answer"):
        st.code('self.receptionist = VidigiStore(\n    self.env,\n    num_resources=self.param.num_receptionists,\n    logger=self.logger,\n    label="receptionist",\n)\n\n# Inside attend_clinic, before the existing registration work:\nself.logger.log_arrival(entity_id=patient.id)\nself.logger.log_queue(entity_id=patient.id, event="receptionist_wait_begins")\nwith self.receptionist.request(\n    entity_id=patient.id,\n    start_event="being_seen_by_receptionist",\n    end_event="receptionist_visit_ends",\n) as req:\n    yield req\n    # Existing registration calculation and timeout\n\n# Nurse waiting and treatment follow here.\n# Log departure once, after the nurse stage.')

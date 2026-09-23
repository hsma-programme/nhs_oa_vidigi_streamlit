"""Exercise 4: explore viDiGi's TrialLogger plots."""

import streamlit as st
from vidigi.logging import TrialLogger

from code_preview import flash_on_change
from model import Model, Param


def reset_parameters():
    """Reset only Exercise 4's widgets before the page reruns."""
    st.session_state.update({
        'trial_iat': 2.0,
        'trial_receptionists': 1,
        'trial_nurses': 1,
        'trial_specialists': 1,
        'trial_specialist_prob': 0.3,
        'trial_hours': 8,
        'trial_replications': 5,
        'trial_seed': 42,
        'trial_queues': ['Receptionist', 'Nurse', 'Specialist'],
        'trial_all_runs': True,
        'trial_shared_axis': False,
        'trial_queue_interval': 5,
        'trial_queue_warmup': 0,
        'trial_duration_pair': 'Waiting for nurse',
        'trial_duration_kind': 'box',
        'trial_duration_split': True,
        'trial_bins': 20,
        'trial_normalise': False,
        'trial_duration_warmup': 0,
        'trial_resource_metric': 'utilisation',
        'trial_resource_kind': 'bar',
        'trial_resource_error': 'ci',
        'trial_resource_show_runs': True,
        'trial_resource_warmup': 0,
        'trial_resource_sort': False,
        'trial_resource_interval': 5,
        'trial_resource_time_warmup': 0,
        'trial_resource_proportion': False,
        'trial_resource_time_runs': True,
        'trial_resource_shared_axis': True,
        'trial_arrival_pair': 'Waiting for nurse',
        'trial_arrival_colour': 'run',
        'trial_arrival_smoothing': 'None',
        'trial_arrival_window': 10,
        'trial_arrival_time_window': 30,
        'trial_arrival_warmup': 0,
    })


@st.cache_data(max_entries=8, show_spinner=False)
def run_trial(parameters, first_seed):
    trial = TrialLogger()
    for run_number in range(1, parameters['num_replications'] + 1):
        model = Model(
            Param(**parameters), replication_id=run_number,
            random_seed=first_seed + run_number - 1,
        )
        model.run_model()
        trial.add_log(model.logger)
    return trial


@st.cache_data(max_entries=16, show_spinner=False)
def queue_plot(parameters, first_seed, options):
    return run_trial(parameters, first_seed).plot_queue_size(**options)


@st.cache_data(max_entries=16, show_spinner=False)
def duration_plot(parameters, first_seed, options):
    return run_trial(parameters, first_seed).plot_duration_distribution(**options)


@st.cache_data(max_entries=24, show_spinner=False)
def additional_plot(parameters, first_seed, method, options):
    return getattr(run_trial(parameters, first_seed), method)(**options)


RESOURCE_CAPACITIES = {
    'being_seen_by_receptionist': 'num_receptionists',
    'being_seen_by_nurse': 'num_nurses',
    'being_seen_by_specialist': 'num_specialists',
}


def capacity_options(parameters):
    return {'resource_capacities': {
        event: parameters[name] for event, name in RESOURCE_CAPACITIES.items()
    }}


def plot_code(method, options):
    event_line = ''
    if method == 'plot_queue_size':
        events = ', '.join(repr(event) for event in options['event_list'])
        event_line = f"    event_list=[\n        {events}\n    ],\n"
    arguments = [
        f'{name}={value!r}' for name, value in options.items()
        if not (method == 'plot_queue_size' and name == 'event_list')
    ]
    return f'fig = trial_logger.{method}(\n' + event_line + ''.join(
        '    ' + ', '.join(arguments[i:i + 2]) + ',\n'
        for i in range(0, len(arguments), 2)
    ) + ')'


with open('styles.css') as css:
    st.html(f'<style>{css.read()}</style>')
st.html('''<style>
::highlight(tokflash-trial_queue_code) {
    background-color: rgba(253, 224, 71, var(--tokflash-trial_queue_code, 0));
}
::highlight(tokflash-trial_duration_code) {
    background-color: rgba(253, 224, 71, var(--tokflash-trial_duration_code, 0));
}
::highlight(tokflash-trial_resource_code) {
    background-color: rgba(253, 224, 71, var(--tokflash-trial_resource_code, 0));
}
::highlight(tokflash-trial_resource_time_code) {
    background-color: rgba(253, 224, 71, var(--tokflash-trial_resource_time_code, 0));
}
::highlight(tokflash-trial_arrival_code) {
    background-color: rgba(253, 224, 71, var(--tokflash-trial_arrival_code, 0));
}

/* Override Streamlit's transparent-until-hover scrollbar rules. */
[data-testid="stCode"] pre {
    overflow-x: scroll !important;
    scrollbar-gutter: stable;
    scrollbar-width: auto !important;
    scrollbar-color: auto !important;
}
[data-testid="stCode"] pre::-webkit-scrollbar {
    width: 14px;
    height: 14px;
}
[data-testid="stCode"] pre::-webkit-scrollbar-track {
    background: #e2e8f0;
    border-radius: 7px;
}
[data-testid="stCode"] pre::-webkit-scrollbar-thumb {
    background: #64748b;
    border: 3px solid #e2e8f0;
    border-radius: 7px;
}
[data-testid="stCode"] pre::-webkit-scrollbar-thumb:hover {
    background: #334155;
}
[data-testid="stCode"] pre::-webkit-scrollbar-corner {
    background: #e2e8f0;
}
</style>''')

st.title('Trial plots playground')
st.write('Explore variation across repeated simulation runs. Change the simulation settings in the sidebar, then adjust each plot using its controls. **Plots and code update automatically.**')
st.caption('Simulation duration includes any plot warm-up. For example, an 8-hour run with a 1-hour warm-up leaves 7 hours of results to plot.')

with st.sidebar:
    st.button(
        'Reset parameters to defaults', key='trial_reset',
        on_click=reset_parameters, width='stretch',
        help='Restore the simulation parameters and all plot tabs to their defaults for Exercise 4 only.',
    )
    st.markdown('**Simulation parameters**')
    parameters = dict(
        mean_patient_inter=st.slider('Interarrival time (mins)', 0.1, 30.0, 2.0, step=0.1, key='trial_iat', help='Average time between arrivals. Lower values mean more patients arrive.'),
        num_receptionists=st.slider('Number of receptionists', 1, 10, 1, key='trial_receptionists', help='Number of patients who can be registered at the same time.'),
        num_nurses=st.slider('Number of nurses', 1, 10, 1, key='trial_nurses', help='Number of patients who can see a nurse at the same time.'),
        num_specialists=st.slider('Number of specialists', 1, 10, 1, key='trial_specialists', help='Number of patients who can see a specialist at the same time.'),
        specialist_prob=st.slider('Probability of needing a specialist', 0.0, 1.0, 0.3, step=0.05, key='trial_specialist_prob', help='Chance of needing a specialist after seeing a nurse. 0.3 means 30%.'),
        sim_duration=60 * st.slider('Simulation duration (hours)', 2, 24, 8, key='trial_hours', help='Total length of each run, including any warm-up selected in a plot. Longer runs allow more patients to progress through the clinic.'),
        num_replications=st.slider('Number of replications', 2, 20, 5, key='trial_replications', help='Independent runs with the same parameters and different seeds. More runs take longer to calculate.'),
        mean_nurse_consult_time=10,
        sd_nurse_consult_time=4,
    )
    first_seed = st.number_input('Random seed', 1, 100000, 42, key='trial_seed', help='Each run uses a consecutive seed, beginning with this one. Keep it fixed when comparing parameter changes.')

with st.expander('How the TrialLogger is built'):
    simulation_code = 'from model import Param, Model\nfrom vidigi.logging import TrialLogger\n\nparams = Param(\n'
    simulation_code += ''.join(f'    {name}={value!r},\n' for name, value in parameters.items())
    simulation_code += (
        ')\ntrial_logger = TrialLogger()\n'
        'for run_number in range(1, params.num_replications + 1):\n'
        f'    model = Model(params, replication_id=run_number, random_seed={first_seed} + run_number - 1)\n'
        '    model.run_model()\n'
        '    trial_logger.add_log(model.logger)'
    )
    st.code(simulation_code, language='python')

QUEUES = {
    'Receptionist': 'receptionist_wait_begins',
    'Nurse': 'nurse_wait_begins',
    'Specialist': 'specialist_wait_begins',
}
PAIRS = {
    'Waiting for receptionist': ('receptionist_wait_begins', 'being_seen_by_receptionist'),
    'Waiting for nurse': ('nurse_wait_begins', 'being_seen_by_nurse'),
    'Waiting for specialist': ('specialist_wait_begins', 'being_seen_by_specialist'),
    'Receptionist consultation': ('being_seen_by_receptionist', 'receptionist_visit_ends'),
    'Nurse consultation': ('being_seen_by_nurse', 'nurse_treatment_ends'),
    'Specialist consultation': ('being_seen_by_specialist', 'specialist_treatment_ends'),
    'Total time in clinic': ('arrival', 'depart'),
}


@st.fragment
def render_queue_tab():
    st.info(
        '**Activity: keep each average queue below 5.** Starting with an 8-hour '
        'simulation, how many receptionists, nurses and specialists do you need '
        'to keep the mean queue below 5 patients at every plotted time point '
        'for all three steps? Turn off "Show individual runs" to focus on the '
        'mean across replications. "Share queue size axis" is off by default, '
        'so read each panel\'s own vertical scale when checking the target. '
        'Keep the other simulation settings fixed and '
        'warm-up at 0, then adjust each resource count. Does reducing one queue '
        'put more pressure on the next step? Finally, try more replications or '
        'a different random seed to see whether your choice still meets the target.'
    )
    controls, output = st.columns([0.38, 0.62])
    with controls:
        code_container = st.container(key='trial_queue_code')
        selected = st.multiselect('Queues', list(QUEUES), default=['Receptionist', 'Nurse', 'Specialist'], key='trial_queues', help='Choose which waiting queues to compare.')
        all_runs = st.checkbox('Show individual runs', True, key='trial_all_runs', help='Show individual simulation trajectories alongside the mean. Turn off to focus on the mean trajectory.')
        shared = st.checkbox('Share queue size axis', False, key='trial_shared_axis', help='Use the same vertical scale across queue panels for easier comparison.')
        snapshot_column, warmup_column = st.columns(2)
        with snapshot_column:
            interval = st.slider('Snapshot interval (mins)', 1, 15, 5, key='trial_queue_interval', help='Time between queue measurements. Smaller values show more detail but take longer to calculate.')
        with warmup_column:
            warm_up = st.slider('Warm-up period (mins)', 0, parameters['sim_duration'] - 30, 0, step=30, key='trial_queue_warmup', help='Start plotting after this time. The simulation still runs from time zero so existing queues are retained.')
        options = dict(event_list=[QUEUES[name] for name in selected], limit_duration=parameters['sim_duration'], every_x_time_units=interval, warm_up=warm_up, show_all_runs=all_runs, shared_y_axis=shared)
        code = plot_code('plot_queue_size', options)
        with code_container:
            st.code(code, language='python')
            flash_on_change('trial_queue_code', code)
    with output:
        st.caption('Time is measured in minutes.')
        if not selected:
            st.info('Select at least one queue to draw the plot.')
        else:
            with st.spinner('Building the queue size plot...'):
                fig = queue_plot(parameters, first_seed, options)
            st.plotly_chart(fig, width='stretch', key='trial_queue_plot')


@st.fragment
def render_duration_tab():
    st.info(
        '**Activity: investigate waiting times.** Start with "Waiting for nurse" '
        'and compare the median, spread and long waits across runs. Keep the '
        'random seed fixed while increasing the number of nurses in the '
        'sidebar. How do the distribution and its outliers change? Try the '
        'violin plot to see where waits are concentrated, then increase the '
        'number of replications. Do the runs tell a consistent story?'
    )
    controls, output = st.columns([0.38, 0.62])
    with controls:
        code_container = st.container(key='trial_duration_code')
        pair = st.selectbox('Duration to measure', list(PAIRS), index=1, key='trial_duration_pair', help='Choose the start and end events for each patient duration.')
        kind = st.selectbox('Plot type', ['box', 'violin', 'ridgeline', 'heatmap'], key='trial_duration_kind', help='Box: quartiles; violin: distribution shape; ridgeline and heatmap: compare distributions across runs.')
        requires_split = kind in ('ridgeline', 'heatmap')
        split = st.checkbox('Separate runs', True, disabled=requires_split, key='trial_duration_split', help='Show each replication separately. Ridgeline and heatmap always separate runs.')
        if kind in ('hist', 'ridgeline', 'heatmap'):
            bins = st.slider('Number of bins', 5, 80, 20, key='trial_bins', help='Controls detail for histograms, ridgelines and heatmaps. More bins give narrower intervals.')
        if kind in ('hist', 'heatmap'):
            normalise = st.checkbox('Show probability density', False, key='trial_normalise', help='Scale histograms or heatmaps to density rather than counts. Ridgelines always use density.')
        warm_up = st.slider('Warm-up period (mins)', 0, parameters['sim_duration'] - 30, 0, step=30, key='trial_duration_warmup', help='Exclude durations whose start event happened before this time.')
        start, end = PAIRS[pair]
        options = dict(first_event=start, second_event=end, kind=kind, split_by='run' if split or requires_split else None, warm_up=warm_up)
        if kind in ('hist', 'ridgeline', 'heatmap'):
            options['bins'] = bins
        if kind in ('hist', 'heatmap'):
            options['normalise'] = normalise
        code = plot_code('plot_duration_distribution', options)
        with code_container:
            st.code(code, language='python')
            flash_on_change('trial_duration_code', code)
    with output:
        st.caption('Durations are in minutes. Only patients with both events recorded are included; unfinished waits or consultations are excluded. Compare the distributions across runs, then try another plot type.')
        if kind in ('box', 'violin'):
            st.caption(
                'A dot represents one patient’s duration. In a box plot, dots '
                'beyond the whiskers are outliers: they fall more than 1.5 times '
                'the interquartile range below the lower quartile or above the '
                'upper quartile. On a violin plot, any dots show individual '
                'durations; those far from the widest part of the shape are less '
                'common. An outlier is still a valid observation—for example, a '
                'patient who waited much longer than most.'
            )
        try:
            with st.spinner('Building the duration distribution...'):
                fig = duration_plot(parameters, first_seed, options)
        except ValueError as error:
            if not any(message in str(error) for message in ('No complete', 'not found in')):
                raise
            st.info('No completed durations are available for these settings. Try a longer simulation, a shorter warm-up, or another duration.')
        else:
            st.plotly_chart(fig, width='stretch', key='trial_duration_plot')


@st.fragment
def render_resource_tab():
    st.info(
        '**Activity: find the busiest resource.** With "Utilisation" selected, '
        'compare the steps and their results across runs. Which resource is '
        'busy for the largest share of its available time? Increase its '
        'capacity by one in the sidebar and see how utilisation changes. '
        'Check the queue size tab too: did the extra capacity reduce that '
        'step\'s queue, or shift the pressure to another step?'
    )
    controls, output = st.columns([0.38, 0.62])
    with controls:
        code_container = st.container(key='trial_resource_code')
        metric = st.selectbox('Measure', ['utilisation', 'mean_in_use', 'busy_time'], key='trial_resource_metric', help='Utilisation is the proportion of available capacity used; mean in use counts busy resource units; busy time totals their minutes in use.')
        kind = st.selectbox('Plot type', ['bar', 'box', 'violin'], key='trial_resource_kind', help='Bar shows a summary; box and violin show variation across replications.')
        show_runs = st.checkbox('Show individual runs', True, key='trial_resource_show_runs', help='Overlay results for each replication.')
        if kind == 'bar':
            error = st.selectbox('Error bars', ['ci', 'sd', 'se', 'range', 'iqr', 'None'], key='trial_resource_error', help='Choose how variation across runs is shown. CI is a 95% confidence interval; None removes error bars.')
            sort = st.checkbox('Sort by value', False, key='trial_resource_sort', help='Order steps from highest to lowest value.')
        warm_up = st.slider('Warm-up period (mins)', 0, parameters['sim_duration'] - 30, 0, step=30, key='trial_resource_warmup', help='Exclude resource use before this time.')
        options = dict(by='step', metric=metric, kind=kind, show_runs=show_runs,
                       warm_up=warm_up, limit_duration=parameters['sim_duration'],
                       **capacity_options(parameters))
        if kind == 'bar':
            options['error_bars'] = None if error == 'None' else error
            options['sort_by'] = 'value' if sort else None
        else:
            options['error_bars'] = None
        code = plot_code('plot_resource_utilisation', options)
        with code_container:
            st.code(code, language='python')
            flash_on_change('trial_resource_code', code)
    with output:
        st.caption('Compare how heavily each step uses its available resources. A utilisation of 1 means all available units were busy throughout the measured window.')
        with st.spinner('Building the resource utilisation plot...'):
            fig = additional_plot(parameters, first_seed, 'plot_resource_utilisation', options)
        st.plotly_chart(fig, width='stretch', key='trial_resource_plot')


@st.fragment
def render_resource_time_tab():
    st.info(
        '**Activity: spot periods of pressure.** Turn off "Show individual '
        'runs" and use "Show proportion of capacity" to compare the mean '
        'resource use over time. When is each step closest to full capacity? '
        'Increase the number of resources at the busiest step, keeping the '
        'random seed fixed. Does the peak fall, and does another step become '
        'the busiest? Turn individual runs back on to see how much they vary.'
    )
    controls, output = st.columns([0.38, 0.62])
    with controls:
        code_container = st.container(key='trial_resource_time_code')
        proportion = st.checkbox('Show proportion of capacity', False, key='trial_resource_proportion', help='Divide the number of resource units in use by the number available at each step.')
        show_runs = st.checkbox('Show individual runs', True, key='trial_resource_time_runs', help='Show each replication as well as the mean trajectory.')
        shared = st.checkbox('Share vertical axis', True, key='trial_resource_shared_axis', help='Use the same y-axis scale for each resource step.')
        snapshot_column, warmup_column = st.columns(2)
        with snapshot_column:
            interval = st.slider('Snapshot interval (mins)', 1, 15, 5, key='trial_resource_interval', help='Time between measurements; smaller values show more detail.')
        with warmup_column:
            warm_up = st.slider('Warm-up period (mins)', 0, parameters['sim_duration'] - 30, 0, step=30, key='trial_resource_time_warmup', help='Start plotting after this time while retaining resource use already underway.')
        options = dict(every_x_time_units=interval, warm_up=warm_up,
                       limit_duration=parameters['sim_duration'],
                       as_proportion=proportion, show_all_runs=show_runs,
                       shared_y_axis=shared)
        if proportion:
            options.update(capacity_options(parameters))
        code = plot_code('plot_resource_utilisation_over_time', options)
        with code_container:
            st.code(code, language='python')
            flash_on_change('trial_resource_time_code', code)
    with output:
        st.caption('Follow resource use across the simulation. Counts show how many units were busy; proportions compare busy units with the available capacity.')
        with st.spinner('Building the resource use over time plot...'):
            fig = additional_plot(parameters, first_seed, 'plot_resource_utilisation_over_time', options)
        st.plotly_chart(fig, width='stretch', key='trial_resource_time_plot')


@st.fragment
def render_arrival_tab():
    st.info(
        '**Activity: see whether arrival time affects waiting.** Select '
        '"Waiting for nurse" and add a trend line using a window of 10 '
        'patients. Do patients arriving later tend to wait longer? Keep the '
        'random seed fixed and increase the number of nurses. Compare the '
        'points and trend line before and after, then colour by run to see '
        'whether the pattern holds across replications.'
    )
    controls, output = st.columns([0.38, 0.62])
    with controls:
        code_container = st.container(key='trial_arrival_code')
        pair = st.selectbox('Duration to measure', list(PAIRS), index=1, key='trial_arrival_pair', help='Choose the two events whose elapsed time is plotted against patient arrival time.')
        colour = st.selectbox('Colour points by', ['run', 'None'], key='trial_arrival_colour', help='Separate points by simulation run, or show all patients together.')
        smoothing = st.selectbox('Trend line', ['None', 'Number of patients', 'Minutes'], key='trial_arrival_smoothing', help='Add a moving average based on nearby patients or a time window.')
        if smoothing == 'Number of patients':
            window = st.slider('Trend half-width (patients)', 2, 50, 10, key='trial_arrival_window', help='Number of neighbouring patients on each side of a point used for the moving average.')
        elif smoothing == 'Minutes':
            time_window = st.slider('Trend half-width (mins)', 5, 120, 30, step=5, key='trial_arrival_time_window', help='Time on either side of an arrival used for the moving average.')
        warm_up = st.slider('Warm-up period (mins)', 0, parameters['sim_duration'] - 30, 0, step=30, key='trial_arrival_warmup', help='Exclude patients arriving before this time.')
        first_event, second_event = PAIRS[pair]
        options = dict(first_event=first_event, second_event=second_event,
                       arrival_event='arrival', colour_by=None if colour == 'None' else colour,
                       warm_up=warm_up)
        if smoothing == 'Number of patients':
            options['rolling_window'] = window
        elif smoothing == 'Minutes':
            options['rolling_time'] = time_window
        code = plot_code('plot_metric_vs_arrival_time', options)
        with code_container:
            st.code(code, language='python')
            flash_on_change('trial_arrival_code', code)
    with output:
        st.caption('Each point is a patient with both events recorded. Look for changes in waits or consultation times for patients arriving later in the run.')
        try:
            with st.spinner('Building the arrival time plot...'):
                fig = additional_plot(parameters, first_seed, 'plot_metric_vs_arrival_time', options)
        except ValueError as error:
            if not any(message in str(error) for message in ('No points to plot', 'not found in')):
                raise
            st.info('No completed durations are available for these settings. Try a longer simulation, a shorter warm-up, or another duration.')
        else:
            st.plotly_chart(fig, width='stretch', key='trial_arrival_plot')


queue_tab, duration_tab, resource_tab, resource_time_tab, arrival_tab = st.tabs([
    'Queue size', 'Duration distribution', 'Resource utilisation',
    'Resource utilisation over time', 'Metric vs arrival time',
])
with queue_tab:
    render_queue_tab()
with duration_tab:
    render_duration_tab()
with resource_tab:
    render_resource_tab()
with resource_time_tab:
    render_resource_time_tab()
with arrival_tab:
    render_arrival_tab()

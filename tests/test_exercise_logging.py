"""Run with: python -m unittest discover -s tests"""
import unittest

from streamlit.testing.v1 import AppTest
from streamlit_dnd import DropEvent, apply_move
from model import Model, Param


class ExerciseTests(unittest.TestCase):
    @staticmethod
    def tick_count(app):
        return sum(item.value == '✅' for item in app.markdown)

    def test_each_setup_answer_can_be_checked_independently(self):
        app = AppTest.from_file('../streamlit_app.py', default_timeout=20).run()
        self.assertFalse(app.exception)
        self.assertEqual(self.tick_count(app), 0)
        self.assertFalse(any(button.key == 'ex1_check_order' for button in app.button))
        app.button(key='ex1_check_class').click().run()
        self.assertTrue(app.warning)
        app.selectbox(key='ex1_class').select('simpy.Store')
        app.button(key='ex1_check_class').click().run()
        self.assertIn('simpy.Store', app.warning[0].value)
        self.assertIn('log their use automatically', app.warning[0].value)
        self.assertNotIn('VidigiStore', app.warning[0].value)
        app.selectbox(key='ex1_class').select('VidigiResource')
        app.button(key='ex1_check_class').click().run()
        self.assertIn('only one nurse', app.warning[0].value)
        self.assertNotIn('VidigiStore', app.warning[0].value)
        app.selectbox(key='ex1_class').select('VidigiStore')
        app.button(key='ex1_check_class').click().run()
        self.assertTrue(app.success)
        self.assertEqual(self.tick_count(app), 1)
        app.multiselect(key='ex1_imports').set_value([
            'from vidigi.logging import EventLogger',
            'from vidigi.resources import VidigiStore',
        ])
        app.selectbox(key='ex1_count').select('num_resources')
        app.selectbox(key='ex1_logger').select('self.logger')
        app.run()
        self.assertEqual(self.tick_count(app), 1)
        self.assertFalse(any(button.key == 'ex1_check_order' for button in app.button))
        for key in ('imports', 'count', 'logger'):
            app.button(key='ex1_check_' + key).click().run()
            self.assertTrue(app.success)
        self.assertTrue(any(button.key == 'ex1_check_order' for button in app.button))
        self.assertEqual(self.tick_count(app), 4)
        app.selectbox(key='ex1_count').select('capacity').run()
        self.assertFalse(any(button.key == 'ex1_check_order' for button in app.button))
        self.assertEqual(self.tick_count(app), 3)
        app.selectbox(key='ex1_count').select('num_resources').run()
        self.assertTrue(any(button.key == 'ex1_check_order' for button in app.button))
        self.assertEqual(self.tick_count(app), 4)
        self.assertFalse(app.exception)
        app.button(key='ex1_check_order').click().run()
        self.assertTrue(app.warning)
        app.session_state['ex1_setup_0'] = ['env', 'logger', 'store']
        app.button(key='ex1_check_order').click().run()
        self.assertTrue(app.success)
        self.assertFalse(app.exception)

    def test_pathway_feedback_and_reversible_moves(self):
        app = AppTest.from_file('../streamlit_app.py', default_timeout=20).run()
        self.assertFalse(app.exception)
        self.assertFalse(any(button.key == 'ex1_check_path' for button in app.button))
        for key, value in [('entity', 'patient.id'), ('start', 'being_seen_by_nurse'),
                           ('end', 'nurse_treatment_ends')]:
            app.selectbox(key='ex1_' + key).select(value)
        app.run()
        self.assertFalse(any(button.key == 'ex1_check_path' for button in app.button))
        for key in ('entity', 'start', 'end'):
            app.button(key='ex1_check_' + key).click().run()
            self.assertTrue(app.success)
        self.assertEqual(self.tick_count(app), 3)
        self.assertTrue(any(button.key == 'ex1_check_path' for button in app.button))
        app.selectbox(key='ex1_entity').select('self.replication_id').run()
        self.assertFalse(any(button.key == 'ex1_check_path' for button in app.button))
        self.assertEqual(self.tick_count(app), 2)
        app.selectbox(key='ex1_entity').select('patient.id').run()
        self.assertTrue(any(button.key == 'ex1_check_path' for button in app.button))
        self.assertEqual(self.tick_count(app), 3)
        names = ['ex1_path_0', 'ex1_path_1']
        lists = {name: list(app.session_state[name]) for name in names}
        ordered_starter = ['startq', 'old', 'yield', 'endq', 'sample', 'timeout']
        self.assertCountEqual(lists[names[0]], ordered_starter)
        self.assertNotEqual(lists[names[0]], ordered_starter)
        # Move the old request out, then back, using actual component index semantics.
        original = list(lists[names[0]])
        old_index = original.index('old')
        apply_move(DropEvent(names[0], names[1], None, old_index, 0), lists)
        apply_move(DropEvent(names[1], names[0], None, 0, old_index), lists)
        self.assertEqual(lists[names[0]], original)
        correct = ['arrival', 'startq', 'queue', 'request', 'yield', 'endq',
                   'sample', 'timeout', 'departure']
        app.session_state[names[0]] = correct
        app.session_state[names[1]] = ['manual', 'placeholder']
        app.session_state['ex1_path_2'] = ['old']
        app.button(key='ex1_check_path').click().run()
        self.assertTrue(app.success)
        self.assertEqual(set(app.session_state[names[1]]), {'manual', 'placeholder', 'old'})
        # The queue timer may precede arrival at the same simulation time.
        app.session_state[names[0]] = ['startq', 'arrival'] + correct[2:]
        app.button(key='ex1_check_path').click().run()
        self.assertTrue(app.success)
        app.session_state[names[0]] = correct[:-2] + ['departure', 'timeout']
        app.button(key='ex1_check_path').click().run()
        self.assertTrue(app.warning)
        self.assertFalse(app.success)
        app.button(key='ex1_reset_path').click().run()
        self.assertCountEqual(app.session_state[names[0]], ordered_starter)
        self.assertNotEqual(app.session_state[names[0]], ordered_starter)
        self.assertFalse(app.exception)

    def test_automatic_logging_pairs_resources_without_duplicates(self):
        # Exercise every resource pool, with enough capacity to complete visits.
        model = Model(Param(sim_duration=300, specialist_prob=1,
                            num_receptionists=2, num_nurses=2, num_specialists=20), 1)
        model.run_model()
        log = model.logger.to_dataframe()
        self.assertFalse(log.duplicated(['entity_id', 'event']).any())
        for role, end in [('receptionist', 'receptionist_visit_ends'),
                          ('nurse', 'nurse_treatment_ends'),
                          ('specialist', 'specialist_treatment_ends')]:
            starts = log[log.event == 'being_seen_by_' + role].set_index('entity_id')
            ends = log[log.event == end].set_index('entity_id')
            self.assertGreater(len(ends), 0)
            self.assertTrue((ends.resource_id == starts.loc[ends.index].resource_id).all())
            self.assertTrue((ends.time > starts.loc[ends.index].time).all())
            self.assertIs(getattr(model, role).logger, model.logger)
        for entity_id in log.loc[log.event == 'depart', 'entity_id']:
            events = log.loc[log.entity_id == entity_id, 'event'].tolist()
            self.assertEqual(events[0], 'arrival')
            self.assertEqual(events[-1], 'depart')
            self.assertEqual(len(events), 11)


if __name__ == '__main__':
    unittest.main()

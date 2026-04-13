import importlib
import sys
import unittest
from unittest.mock import Mock, patch

from config import Config
from turniere import TurniereRequestError


def load_main_module():
    sys.modules.pop('main', None)
    fake_config = Config(
        username='operator@example.com',
        password='secret',
        tournament_code='1',
        main_instance_url='http://127.0.0.1:3000',
        remote_instance_url='',
    )
    with patch('config.read_config', return_value=fake_config):
        return importlib.import_module('main')


class MainRoutesTest(unittest.TestCase):
    def setUp(self):
        self.main = load_main_module()
        self.client = self.main.app.test_client()
        self.main.app.config['TESTING'] = True
        self.main.main_instance = Mock()
        self.main.enqueue_remote_action = Mock()

    def tearDown(self):
        sys.modules.pop('main', None)

    def test_submit_decider_result_uses_hidden_points_score_field(self):
        response = self.client.post('/m/17/submit', data={
            'match_score1': '31',
            'match_score2': '32',
            'score1': '4',
            'score2': '6',
            'score_field': 'hidden_points',
        })

        self.assertEqual(response.status_code, 302)
        submitted_match = self.main.main_instance.submit_results.call_args.args[0]
        self.assertEqual(submitted_match.score_field, 'hidden_points')
        self.main.enqueue_remote_action.assert_called_once()

    def test_create_decider_match_calls_backend_and_enqueues_remote_action(self):
        self.main.main_instance.create_decider_match.return_value = {'id': 88}

        response = self.client.post('/groups/7/matches', data={
            'team_id_1': '12',
            'team_id_2': '13',
        })

        self.assertEqual(response.status_code, 302)
        self.main.main_instance.create_decider_match.assert_called_once_with('7', [12, 13])
        action = self.main.enqueue_remote_action.call_args.args[0]
        self.assertEqual(action.type, 'create_decider_match')
        self.assertEqual(action.data, ('7', [12, 13]))

    def test_stop_group_stage_redirects_to_decider_error_on_blocking_ties(self):
        self.main.main_instance.stop_group_stage.side_effect = TurniereRequestError(
            'PATCH',
            '/stages/5',
            FakeErrorResponse(422, {
                'error': 'Playoffs cannot be generated yet because a decider match is required for an advancing place',
                'blocking_ties': [{'group_id': 7}],
            }),
        )

        response = self.client.post('/m/5/stop')

        self.assertEqual(response.status_code, 302)
        self.assertIn('/?error=decider_required', response.location)
        self.main.enqueue_remote_action.assert_not_called()


class FakeErrorResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body
        self.text = str(body)

    def json(self):
        return self._body

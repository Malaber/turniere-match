import unittest
from unittest.mock import patch

from turniere import Turniere, TurniereRequestError
from worker import Action, Match, Worker


class FakeResponse:
    def __init__(self, ok=True, status_code=200, json_body=None, text=''):
        self.ok = ok
        self.status_code = status_code
        self._json_body = json_body if json_body is not None else {}
        self.text = text

    def __bool__(self):
        return self.ok

    def json(self):
        return self._json_body


class TurniereClientTest(unittest.TestCase):
    def test_submit_results_uses_hidden_points_for_deciders(self):
        instance = Turniere('http://example.test', '1', 'user@example.com', 'secret')
        match = Match('7', '11', '12', '5', '3', False, 'hidden_points')

        with patch.object(instance, '_request', return_value=FakeResponse()) as request_mock:
            instance.submit_results(match)

        calls = request_mock.call_args_list
        self.assertEqual(calls[0].args[0], '/match_scores/11')
        self.assertEqual(calls[0].kwargs['json'], {'hidden_points': '5'})
        self.assertEqual(calls[1].args[0], '/match_scores/12')
        self.assertEqual(calls[1].kwargs['json'], {'hidden_points': '3'})
        self.assertEqual(calls[2].args[0], '/matches/7')
        self.assertEqual(calls[2].kwargs['json'], {'state': 'finished'})

    def test_submit_results_uses_points_for_normal_matches(self):
        instance = Turniere('http://example.test', '1', 'user@example.com', 'secret')
        match = Match('8', '21', '22', '10', '9', True, 'points')

        with patch.object(instance, '_request', return_value=FakeResponse()) as request_mock:
            instance.submit_results(match)

        calls = request_mock.call_args_list
        self.assertEqual(calls[0].kwargs['json'], {'points': '10'})
        self.assertEqual(calls[1].kwargs['json'], {'points': '9'})
        self.assertEqual(len(calls), 2)

    def test_create_decider_match_posts_team_ids(self):
        instance = Turniere('http://example.test', '1', 'user@example.com', 'secret')

        with patch.object(
            instance,
            '_request',
            return_value=FakeResponse(json_body={'id': 99, 'decider': True}),
        ) as request_mock:
            result = instance.create_decider_match('4', [12, 13])

        self.assertEqual(result['id'], 99)
        self.assertEqual(
            request_mock.call_args.kwargs['json'],
            {'team_ids': [12, 13]},
        )

    def test_request_raises_structured_error_for_failure_responses(self):
        instance = Turniere('http://example.test', '1', 'user@example.com', 'secret')
        response = FakeResponse(ok=False, status_code=422, json_body={'error': 'boom'})

        with patch('turniere.requests.Session.send', return_value=response):
            with self.assertRaises(TurniereRequestError) as error:
                instance._request('/stages/1', method='PATCH', json={'state': 'finished'})

        self.assertEqual(error.exception.status_code, 422)
        self.assertEqual(error.exception.body, {'error': 'boom'})


class WorkerTest(unittest.TestCase):
    def test_worker_replays_create_decider_action(self):
        instance = patch('worker.time.sleep').start()
        self.addCleanup(patch.stopall)

        remote = unittest.mock.Mock()
        worker = Worker(remote)
        worker.queue.put_nowait(Action('create_decider_match', ('4', [12, 13])))
        worker.queue.put_nowait(Action('set_timer_end', '2099-01-01T12:00:00'))

        def stop_after_second_action(*args, **kwargs):
            if remote.create_decider_match.called and remote.set_timer_end.called:
                worker.done = True

        remote.login.side_effect = stop_after_second_action
        remote.create_decider_match.side_effect = stop_after_second_action
        remote.set_timer_end.side_effect = stop_after_second_action

        worker.run()

        remote.create_decider_match.assert_called_once_with('4', [12, 13])
        remote.set_timer_end.assert_called_once_with('2099-01-01T12:00:00')

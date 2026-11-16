import unittest
from unittest.mock import patch
from src.lambda_handler import lambda_handler
from src.rag import retrieve


def event(name, slots=None, attrs=None, text=''):
    return {'inputTranscript': text, 'sessionState': {'intent': {'name': name, 'slots': slots or {}}, 'sessionAttributes': attrs or {}}}


def slot(value):
    return {'value': {'interpretedValue': value}}


class AssistantTests(unittest.TestCase):
    def test_missing_service(self):
        result = lambda_handler(event('SolicitarSoporte'))
        self.assertEqual(result['sessionState']['dialogAction']['slotToElicit'], 'Servicio')

    def test_invalid_service(self):
        result = lambda_handler(event('SolicitarSoporte', {'Servicio': slot('fax')}))
        self.assertIsNone(result['sessionState']['intent']['slots']['Servicio'])

    def test_missing_category(self):
        result = lambda_handler(event('SolicitarSoporte', {'Servicio': slot('web')}))
        self.assertEqual(result['sessionState']['dialogAction']['slotToElicit'], 'Categoria')

    def test_complete_support(self):
        result = lambda_handler(event('SolicitarSoporte', {'Servicio': slot('app'), 'Categoria': slot('error')}))
        self.assertEqual(result['sessionState']['intent']['state'], 'Fulfilled')
        self.assertIn('no crea un ticket', result['messages'][0]['content'])

    def test_two_fallbacks(self):
        first = lambda_handler(event('FallbackIntent'))
        second = lambda_handler(event('FallbackIntent', attrs=first['sessionState']['sessionAttributes']))
        self.assertEqual(second['sessionState']['sessionAttributes']['handoffRequested'], 'true')

    def test_fallback_reset(self):
        result = lambda_handler(event('ConsultarHorario', attrs={'fallbackCount': '1', 'handoffRequested': 'true'}))
        self.assertEqual(result['sessionState']['sessionAttributes'], {'fallbackCount': '0', 'handoffRequested': 'false'})

    def test_malformed_counter(self):
        result = lambda_handler(event('FallbackIntent', attrs={'fallbackCount': 'oops'}))
        self.assertEqual(result['sessionState']['sessionAttributes']['fallbackCount'], '1')

    def test_agent_request(self):
        result = lambda_handler(event('HablarConAgente'))
        self.assertEqual(result['sessionState']['sessionAttributes']['handoffRequested'], 'true')

    def test_citation(self):
        self.assertIn('[Fuente: horarios.md]', retrieve('¿Cuál es el horario?'))

    def test_unknown_answer(self):
        self.assertIn('No encuentro', retrieve('¿Cuánto cuesta?'))

    def test_ambiguous_query(self):
        self.assertIn('varios temas', retrieve('horarios y servicios'))

    def test_document_failure(self):
        with patch('src.lambda_handler.retrieve', side_effect=OSError('private details')):
            result = lambda_handler(event('ConsultarFAQ', text='horario'))
        self.assertNotIn('private details', result['messages'][0]['content'])
        self.assertIn('No puedo consultar', result['messages'][0]['content'])

    def test_does_not_mutate_event(self):
        original = event('FallbackIntent')
        lambda_handler(original)
        self.assertEqual(original['sessionState']['sessionAttributes'], {})


if __name__ == '__main__':
    unittest.main()

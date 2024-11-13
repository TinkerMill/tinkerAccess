import unittest
from datetime import datetime
from mock import patch, MagicMock
from freezegun import freeze_time
import sys
import os

# Add the parent directory to the path so we can import server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import app, toolSummaryInterface

class TestToolSummaryInterface(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    @freeze_time("2023-07-15")
    @patch('server.genToolSummary')
    @patch('server.render_template')
    def test_default_dates(self, mock_render, mock_gen_summary):
        # Mock the current date to a known value
        test_date = datetime(2023, 7, 15)
        expected_start = datetime(2023, 6, 1)
        expected_end = datetime(2023, 7, 1)
        
        mock_gen_summary.return_value = {}
        mock_render.return_value = ''
            
        toolSummaryInterface()
        
        # Verify genToolSummary was called with correct dates
        mock_gen_summary.assert_called_once_with(expected_start, expected_end)
        
        # Verify template was rendered with correct dates
        mock_render.assert_called_once()
        template_args = mock_render.call_args[1]
        self.assertEqual(template_args['start'], '2023-06-01')
        self.assertEqual(template_args['end'], '2023-07-01')

    @patch('server.genToolSummary')
    @patch('server.render_template')
    def test_custom_start_date(self, mock_render, mock_gen_summary):
        mock_gen_summary.return_value = {}
        mock_render.return_value = ''
        
        start_date = '2023-06-15'
        expected_start = datetime(2023, 6, 15)
        expected_end = datetime(2023, 7, 15)
        
        toolSummaryInterface(start_date)
        
        # Verify genToolSummary was called with correct dates
        mock_gen_summary.assert_called_once_with(expected_start, expected_end)
        
        # Verify template was rendered with correct dates
        mock_render.assert_called_once()
        template_args = mock_render.call_args[1]
        self.assertEqual(template_args['start'], '2023-06-15')
        self.assertEqual(template_args['end'], '2023-07-15')

    @patch('server.genToolSummary')
    @patch('server.render_template')
    def test_custom_start_and_end_date(self, mock_render, mock_gen_summary):
        mock_gen_summary.return_value = {}
        mock_render.return_value = ''
        
        start_date = '2023-06-15'
        end_date = '2023-07-20'
        expected_start = datetime(2023, 6, 15)
        expected_end = datetime(2023, 7, 20)
        
        toolSummaryInterface(start_date, end_date)
        
        # Verify genToolSummary was called with correct dates
        mock_gen_summary.assert_called_once_with(expected_start, expected_end)
        
        # Verify template was rendered with correct dates
        mock_render.assert_called_once()
        template_args = mock_render.call_args[1]
        self.assertEqual(template_args['start'], '2023-06-15')
        self.assertEqual(template_args['end'], '2023-07-20')

    @freeze_time("2023-12-15")
    @patch('server.genToolSummary')
    @patch('server.render_template')
    def test_december_transition(self, mock_render, mock_gen_summary):
        test_date = datetime(2023, 12, 15)
        expected_start = datetime(2023, 11, 1)
        expected_end = datetime(2023, 12, 1)
        
        mock_gen_summary.return_value = {}
        mock_render.return_value = ''
        
        toolSummaryInterface()
        
        mock_gen_summary.assert_called_once_with(expected_start, expected_end)

    @freeze_time("2024-01-15")
    @patch('server.genToolSummary')
    @patch('server.render_template')
    def test_january_transition(self, mock_render, mock_gen_summary):
        test_date = datetime(2024, 1, 15)
        expected_start = datetime(2023, 12, 1)
        expected_end = datetime(2024, 1, 1)
        
        mock_gen_summary.return_value = {}
        mock_render.return_value = ''
        
        toolSummaryInterface()
        
        mock_gen_summary.assert_called_once_with(expected_start, expected_end)

    @patch('server.genToolSummary')
    @patch('server.render_template')
    def test_month_length_transition(self, mock_render, mock_gen_summary):
        # Test transition from a month with 31 days to one with 30
        start_date = '2023-07-31'
        expected_start = datetime(2023, 7, 31)
        expected_end = datetime(2023, 8, 31)
        
        mock_gen_summary.return_value = {}
        mock_render.return_value = ''
        
        toolSummaryInterface(start_date)
        
        mock_gen_summary.assert_called_once_with(expected_start, expected_end)

    def create_mock_tool_summary(self):
        return {
            '1': {
                'name': 'Test Tool',
                'logins': 10,
                'logouts': 10,
                'total': 3600,
                'leaderboard': [('User 1', 1800), ('User 2', 1200)]
            }
        }

    @patch('server.genToolSummary')
    @patch('server.render_template')
    def test_tool_summary_data(self, mock_render, mock_gen_summary):
        mock_summary = self.create_mock_tool_summary()
        mock_gen_summary.return_value = mock_summary
        mock_render.return_value = ''
        
        toolSummaryInterface()
        
        # Verify template was rendered with correct tool summary data
        mock_render.assert_called_once()
        template_args = mock_render.call_args[1]
        self.assertEqual(template_args['tools'], mock_summary)

if __name__ == '__main__':
    unittest.main()

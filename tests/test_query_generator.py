import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*SwigPyPacked.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*SwigPyObject.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*swigvarlink.*")

import unittest
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
import compress_pickle

from pytgrep2 import TgrepQueryGenerator, TgrepOrchestrator

class TestTgrepQueryGenerator(unittest.TestCase):
    def setUp(self):
        # Create a workspace-relative temp cache path for testing
        self.test_dir = Path("temp_test_query_generator")
        self.test_dir.mkdir(exist_ok=True)
        self.cache_path = self.test_dir / "test_cache.pkl.gz"
        
        # Ensure clean state
        if self.cache_path.exists():
            self.cache_path.unlink()

        # Mock the google-genai Client
        self.patcher = patch("pytgrep2.query_generator.genai.Client")
        self.mock_client_class = self.patcher.start()
        
        self.mock_client = MagicMock()
        self.mock_client_class.return_value = self.mock_client
        
        # Set up a default mock response
        self.mock_response = MagicMock()
        self.mock_response.text = "NP < JJ"
        self.mock_client.models.generate_content.return_value = self.mock_response

    def tearDown(self):
        self.patcher.stop()
        if self.cache_path.exists():
            self.cache_path.unlink()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_cache_loading_and_saving(self):
        # Initialize query generator
        generator = TgrepQueryGenerator(cache_path=self.cache_path, api_key="fake_key")
        self.assertEqual(generator.cache, {})
        
        # Add item to cache and save manually
        generator.cache["NP dominating JJ"] = "NP < JJ"
        generator._save_cache()
        
        self.assertTrue(self.cache_path.exists())
        
        # Re-initialize generator with same path and verify loaded cache
        new_generator = TgrepQueryGenerator(cache_path=self.cache_path, api_key="fake_key")
        self.assertEqual(new_generator.cache, {"NP dominating JJ": "NP < JJ"})

    def test_cache_hit_returns_immediately(self):
        # Populate cache
        initial_cache = {"NP dominating JJ": "NP < JJ"}
        compress_pickle.dump(initial_cache, self.cache_path, compression="gzip")
        
        generator = TgrepQueryGenerator(cache_path=self.cache_path, api_key="fake_key")
        
        # Execute query
        pattern = generator.generate_pattern("NP dominating JJ")
        
        # Verify cached value is returned and API is NOT called
        self.assertEqual(pattern, "NP < JJ")
        self.mock_client.models.generate_content.assert_not_called()

    def test_generate_pattern_success(self):
        generator = TgrepQueryGenerator(cache_path=self.cache_path, api_key="fake_key")
        
        # Mock validation to pass
        generator.validate_pattern = MagicMock(return_value=True)
        
        pattern = generator.generate_pattern("NP dominating JJ")
        
        self.assertEqual(pattern, "NP < JJ")
        self.assertEqual(generator.cache["NP dominating JJ"], "NP < JJ")
        self.mock_client.models.generate_content.assert_called_once()

    def test_generate_pattern_self_correction_feedback_loop(self):
        generator = TgrepQueryGenerator(cache_path=self.cache_path, api_key="fake_key")
        
        # Mock validation to fail on first attempt, then pass on second
        generator.validate_pattern = MagicMock(side_effect=[False, True])
        generator._get_pattern_error = MagicMock(return_value="tgrep2 compile syntax error")
        
        # We need to return different mock text for the calls
        response1 = MagicMock()
        response1.text = "invalid(pattern)"
        response2 = MagicMock()
        response2.text = "NP < JJ"
        
        self.mock_client.models.generate_content.side_effect = [response1, response2]
        
        pattern = generator.generate_pattern("NP dominating JJ")
        
        # Check we got the corrected pattern
        self.assertEqual(pattern, "NP < JJ")
        self.assertEqual(generator.client.models.generate_content.call_count, 2)
        
        # Verify the second prompt contained the feedback error
        call_args_list = generator.client.models.generate_content.call_args_list
        second_call_prompt = call_args_list[1][1]['contents']
        self.assertIn("invalid(pattern)", second_call_prompt)
        self.assertIn("tgrep2 compile syntax error", second_call_prompt)

    def test_generate_pattern_failure_after_retries(self):
        generator = TgrepQueryGenerator(cache_path=self.cache_path, api_key="fake_key")
        
        # Mock validation to always fail
        generator.validate_pattern = MagicMock(return_value=False)
        generator._get_pattern_error = MagicMock(return_value="syntax error")
        
        with self.assertRaises(RuntimeError):
            generator.generate_pattern("NP dominating JJ", max_retries=3)
            
        self.assertEqual(generator.client.models.generate_content.call_count, 3)

    def test_validate_pattern_with_real_orchestrator(self):
        # Test validation function using the real C-engine with sample patterns
        generator = TgrepQueryGenerator(cache_path=self.cache_path, api_key="fake_key")
        
        # Real syntax checking via orchestrator
        self.assertTrue(generator.validate_pattern("NP < JJ"))
        self.assertFalse(generator.validate_pattern("NP < (JJ")) # malformed parenthesis

if __name__ == '__main__':
    unittest.main(warnings='ignore')

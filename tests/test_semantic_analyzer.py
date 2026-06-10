import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*SwigPyPacked.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*SwigPyObject.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*swigvarlink.*")

import unittest
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

from pytgrep2 import TgrepSemanticAnalyzer, TgrepOrchestrator

class TestTgrepSemanticAnalyzer(unittest.TestCase):
    def setUp(self):
        # Create a workspace-relative temp test dir
        self.test_dir = Path("temp_test_semantic_analyzer")
        self.test_dir.mkdir(exist_ok=True)
        
        self.mrg_file = self.test_dir / "test.mrg"
        self.t2c_file = self.test_dir / "test.t2c"
        
        # Write a small sample PTB corpus
        with self.mrg_file.open("w", encoding="utf-8") as f:
            # Sentence 1: John loves Mary. (NP, VP)
            f.write("(S (NP (NNP John)) (VP (VBZ loves) (NP (NNP Mary))) (. .))\n")
            # Sentence 2: The dog might bark. (Hedging verb might)
            f.write("(S (NP (DT The) (NN dog)) (VP (MD might) (VP (VB bark))) (. .))\n")
            # Sentence 3: Although it is late, they will go. (Concession SBAR)
            f.write("(S (SBAR (IN Although) (S (NP (PRP it)) (VP (VBZ is) (ADJP (JJ late))))) (, ,) (NP (PRP they)) (VP (MD will) (VP (VB go))) (. .))\n")

        # Compile index using the default orchestrator
        self.orchestrator = TgrepOrchestrator()
        self.orchestrator.index_corpus(self.mrg_file, self.t2c_file)

        # Mock the google-genai Client in semantic_analyzer
        self.patcher = patch("pytgrep2.semantic_analyzer.genai.Client")
        self.mock_client_class = self.patcher.start()
        self.mock_client = MagicMock()
        self.mock_client_class.return_value = self.mock_client
        
        # Default mock GenAI response
        self.mock_response = MagicMock()
        self.mock_response.text = "Mocked Semantic Analysis Response"
        self.mock_client.models.generate_content.return_value = self.mock_response

    def tearDown(self):
        self.patcher.stop()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_analyze_corpus_with_pattern_from_index(self):
        analyzer = TgrepSemanticAnalyzer(api_key="fake_key", orchestrator=self.orchestrator)
        
        results = analyzer.analyze_corpus(
            corpus=self.t2c_file,
            pattern_or_desc="VP < (MD < might)",
            semantic_task="Explain what the modal verb suggests about certainty.",
            is_pattern=True
        )
        
        # Verify result size (Sentence 2 matches)
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertEqual(res["sentence_index"], 1) # Sentence 2 is index 1
        self.assertIn("might", res["sentence"])
        self.assertEqual(res["analysis"], "Mocked Semantic Analysis Response")
        self.assertEqual(res["pattern"], "VP < (MD < might)")
        
        # Verify client calls
        self.mock_client.models.generate_content.assert_called_once()

    def test_analyze_corpus_with_raw_texts(self):
        analyzer = TgrepSemanticAnalyzer(api_key="fake_key", orchestrator=self.orchestrator)
        texts = [
            "John loves Mary.",
            "The dog might bark."
        ]
        
        results = analyzer.analyze_corpus(
            corpus=texts,
            pattern_or_desc="VP < MD",
            semantic_task="Explain certainty.",
            is_pattern=True
        )
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["sentence_index"], 1)
        self.assertIn("might", results[0]["sentence"])

    def test_analyze_corpus_with_nl_description(self):
        # We need to mock TgrepQueryGenerator inside semantic_analyzer
        with patch("pytgrep2.semantic_analyzer.TgrepQueryGenerator") as mock_qgen_class:
            mock_qgen = MagicMock()
            mock_qgen_class.return_value = mock_qgen
            mock_qgen.generate_pattern.return_value = "VP < (MD < might)"
            
            analyzer = TgrepSemanticAnalyzer(api_key="fake_key", orchestrator=self.orchestrator, query_generator=mock_qgen)
            
            results = analyzer.analyze_corpus(
                corpus=self.t2c_file,
                pattern_or_desc="sentences containing a modal verb",
                semantic_task="Explain certainty.",
                is_pattern=False
            )
            
            mock_qgen.generate_pattern.assert_called_once_with("sentences containing a modal verb")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["pattern"], "VP < (MD < might)")

    def test_metadata_alignment_list(self):
        analyzer = TgrepSemanticAnalyzer(api_key="fake_key", orchestrator=self.orchestrator)
        metadata = ["Meta John", "Meta Dog", "Meta Late"]
        
        results = analyzer.analyze_corpus(
            corpus=self.t2c_file,
            pattern_or_desc="VP < (MD < might)",
            semantic_task="Explain certainty.",
            metadata=metadata
        )
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["metadata"], "Meta Dog")

    def test_metadata_alignment_dict(self):
        analyzer = TgrepSemanticAnalyzer(api_key="fake_key", orchestrator=self.orchestrator)
        # Testing both int key and string key mapping
        metadata = {
            1: "Meta Dog Int",
            "2": "Meta Late Str"
        }
        
        results = analyzer.analyze_corpus(
            corpus=self.t2c_file,
            pattern_or_desc="VP < (MD < might)",
            semantic_task="Explain certainty.",
            metadata=metadata
        )
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["metadata"], "Meta Dog Int")

    def test_grouping_multiple_subtrees(self):
        analyzer = TgrepSemanticAnalyzer(api_key="fake_key", orchestrator=self.orchestrator)
        
        # Search for NNP - John and Mary both match in sentence 0
        results = analyzer.analyze_corpus(
            corpus=self.t2c_file,
            pattern_or_desc="NNP",
            semantic_task="Classify entities."
        )
        
        # Only 1 unique sentence should be sent to Gemini
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["sentence_index"], 0)
        self.assertEqual(len(results[0]["subtrees"]), 2)
        self.assertIn("(NNP John)", results[0]["subtrees"])
        self.assertIn("(NNP Mary)", results[0]["subtrees"])
        
        # Assert Gemini called only once
        self.mock_client.models.generate_content.assert_called_once()

    def test_custom_prompt_formatter(self):
        analyzer = TgrepSemanticAnalyzer(api_key="fake_key", orchestrator=self.orchestrator)
        
        def custom_formatter(sentence, subtrees, metadata, task):
            return f"CustomPrompt: {sentence} | Sub: {subtrees[0]} | Task: {task}"
            
        results = analyzer.analyze_corpus(
            corpus=self.t2c_file,
            pattern_or_desc="VP < (MD < might)",
            semantic_task="Explain certainty.",
            custom_prompt_formatter=custom_formatter
        )
        
        # Verify prompt structure passed to models.generate_content
        call_args = self.mock_client.models.generate_content.call_args[1]
        self.assertIn("CustomPrompt: The dog might bark", call_args["contents"])
        self.assertIn("Sub: (VP (MD might) (VP (VB bark)))", call_args["contents"])
        self.assertIn("Task: Explain certainty.", call_args["contents"])

if __name__ == "__main__":
    unittest.main(warnings='ignore')

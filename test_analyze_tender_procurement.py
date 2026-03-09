"""
Test cases for analyze_tender_procurement.py
"""

import unittest
import json
import tempfile
import os
from unittest.mock import patch
from analyze_tender_procurement import (
    analyze_procurement_score,
    analyze_tenders_file,
    print_summary
)


class TestAnalyzeTenderProcurement(unittest.TestCase):
    """Test cases for tender procurement analysis functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_tender = {
            "number": "TEST-001",
            "description": "Licitación Pública para servicios",
            "type": "Licitación Pública",
            "date": "09/03/2026 08:00 Hrs.",
            "status": "Publicado",
            "full_text": "proceso de compra con términos de referencia"
        }

        self.sample_tender_no_triggers = {
            "number": "TEST-002",
            "description": "Venta de productos varios",
            "type": "Venta Directa",
            "date": "09/03/2026 08:00 Hrs.",
            "status": "Publicado",
            "full_text": "simple sale without any formal process terms"
        }

        self.sample_tender_mixed = {
            "number": "TEST-003",
            "description": "Proceso de Contratación de equipos",
            "type": "Contratación Directa",
            "date": "09/03/2026 08:00 Hrs.",
            "status": "Publicado",
            "full_text": "licitación internacional con solicitud de propuesta"
        }

    def test_analyze_procurement_score_with_strong_trigger(self):
        """Test analysis with strong procurement triggers"""
        result = analyze_procurement_score(self.sample_tender)
        
        self.assertEqual(result["tender_number"], "TEST-001")
        self.assertEqual(result["procurement_score"], 4)  # +4 for strong trigger
        self.assertTrue(result["has_strong_trigger"])
        self.assertEqual(len(result["detected_triggers"]), 1)
        self.assertEqual(result["detected_triggers"][0]["trigger"], "Licitación")
        self.assertEqual(result["detected_triggers"][0]["language"], "spanish")

    def test_analyze_procurement_score_no_triggers(self):
        """Test analysis with no procurement triggers"""
        result = analyze_procurement_score(self.sample_tender_no_triggers)
        
        self.assertEqual(result["tender_number"], "TEST-002")
        self.assertEqual(result["procurement_score"], 0)
        self.assertFalse(result["has_strong_trigger"])
        self.assertEqual(len(result["detected_triggers"]), 0)

    def test_analyze_procurement_score_multiple_triggers(self):
        """Test analysis with multiple triggers (should only count one per language)"""
        result = analyze_procurement_score(self.sample_tender_mixed)
        
        self.assertEqual(result["tender_number"], "TEST-003")
        self.assertEqual(result["procurement_score"], 4)  # Only +4 (one per language max)
        self.assertTrue(result["has_strong_trigger"])
        self.assertEqual(len(result["detected_triggers"]), 1)

    def test_analyze_procurement_score_missing_fields(self):
        """Test analysis with missing fields"""
        minimal_tender = {"number": "TEST-004"}
        result = analyze_procurement_score(minimal_tender)
        
        self.assertEqual(result["tender_number"], "TEST-004")
        self.assertEqual(result["procurement_score"], 0)
        self.assertFalse(result["has_strong_trigger"])

    def test_analyze_procurement_score_english_triggers(self):
        """Test analysis with English procurement triggers"""
        english_tender = {
            "number": "TEST-005",
            "description": "RFP for consulting services",
            "type": "Tender",
            "full_text": "Request for Proposal with Terms of Reference"
        }
        
        result = analyze_procurement_score(english_tender)
        
        self.assertEqual(result["procurement_score"], 4)
        self.assertTrue(result["has_strong_trigger"])
        self.assertEqual(result["detected_triggers"][0]["language"], "english")

    def test_analyze_procurement_score_portuguese_triggers(self):
        """Test analysis with Portuguese procurement triggers"""
        portuguese_tender = {
            "number": "TEST-006",
            "description": "Licitação Pública",
            "type": "Edital",
            "full_text": "processo licitatório com carta convite"
        }
        
        result = analyze_procurement_score(portuguese_tender)
        
        self.assertEqual(result["procurement_score"], 4)
        self.assertTrue(result["has_strong_trigger"])
        self.assertEqual(result["detected_triggers"][0]["language"], "portuguese")

    def test_analyze_procurement_score_word_boundary_matching(self):
        """Test that triggers match whole words only, not substrings"""
        # This should NOT match "licitación" as it's part of "autorización"
        substring_tender = {
            "number": "TEST-007",
            "description": "autorizacion del pliego",
            "type": "proceso",
            "full_text": "autorizacion del llamado sin licitacion explicita"
        }
        
        result = analyze_procurement_score(substring_tender)
        
        # Should not match "licitación" as substring
        self.assertEqual(result["procurement_score"], 0)
        self.assertFalse(result["has_strong_trigger"])

    def test_analyze_procurement_score_case_insensitive(self):
        """Test case insensitive matching"""
        case_tender = {
            "number": "TEST-008",
            "description": "LICITACIÓN PÚBLICA",
            "type": "licitación privada",
            "full_text": "Proceso de Compra"
        }
        
        result = analyze_procurement_score(case_tender)
        
        self.assertEqual(result["procurement_score"], 4)
        self.assertTrue(result["has_strong_trigger"])

    def test_analyze_tenders_file_valid_input(self):
        """Test analyzing tenders from a valid file"""
        test_data = [
            self.sample_tender,
            self.sample_tender_no_triggers,
            self.sample_tender_mixed
        ]
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False) as f:
            for tender in test_data:
                f.write(json.dumps(tender) + '\n')
            temp_file = f.name
        
        try:
            results = analyze_tenders_file(temp_file)
            
            self.assertEqual(len(results), 3)
            self.assertEqual(results[0]["tender_number"], "TEST-001")
            self.assertEqual(results[0]["procurement_score"], 4)
            self.assertEqual(results[1]["tender_number"], "TEST-002")
            self.assertEqual(results[1]["procurement_score"], 0)
            self.assertEqual(results[2]["tender_number"], "TEST-003")
            self.assertEqual(results[2]["procurement_score"], 4)
            
        finally:
            os.unlink(temp_file)

    def test_analyze_tenders_file_with_output(self):
        """Test analyzing tenders with output file"""
        test_data = [self.sample_tender]
        
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False) as input_f:
            for tender in test_data:
                input_f.write(json.dumps(tender) + '\n')
            input_file = input_f.name
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False) as output_f:
            output_file = output_f.name
        
        try:
            results = analyze_tenders_file(input_file, output_file)
            
            # Check results
            self.assertEqual(len(results), 1)
            
            # Check output file was created and contains data
            self.assertTrue(os.path.exists(output_file))
            with open(output_file, 'r', encoding='utf-8') as f:
                output_data = f.read().strip()
                self.assertTrue(output_data)
                
                # Parse and verify output
                result_json = json.loads(output_data)
                self.assertEqual(result_json["tender_number"], "TEST-001")
                self.assertEqual(result_json["procurement_score"], 4)
            
        finally:
            os.unlink(input_file)
            os.unlink(output_file)

    def test_analyze_tenders_file_not_found(self):
        """Test handling of non-existent input file"""
        results = analyze_tenders_file("non_existent_file.ndjson")
        self.assertEqual(results, [])

    def test_analyze_tenders_file_invalid_json(self):
        """Test handling of invalid JSON in input file"""
        # Create temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False) as f:
            f.write('{"invalid": json}\n')
            f.write('{"number": "valid", "description": "test tender"}\n')
            temp_file = f.name
        
        try:
            with patch('builtins.print') as mock_print:
                results = analyze_tenders_file(temp_file)
                
                # Should process the valid line and skip the invalid one
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0]["tender_number"], "valid")
                
                # Should have printed error message
                mock_print.assert_called()
                error_call_args = [call[0][0] for call in mock_print.call_args_list]
                self.assertTrue(any("Error parsing JSON" in arg for arg in error_call_args))
                
        finally:
            os.unlink(temp_file)

    def test_analyze_tenders_file_empty_lines(self):
        """Test handling of empty lines in input file"""
        # Create temporary file with empty lines
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False) as f:
            f.write('\n')
            f.write('   \n')
            f.write(json.dumps(self.sample_tender) + '\n')
            f.write('\n')
            temp_file = f.name
        
        try:
            results = analyze_tenders_file(temp_file)
            
            # Should only process the valid line
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["tender_number"], "TEST-001")
            
        finally:
            os.unlink(temp_file)

    @patch('builtins.print')
    def test_print_summary(self, mock_print):
        """Test print summary functionality"""
        test_results = [
            {"tender_number": "TEST-001", "procurement_score": 4, "detected_triggers": [{"trigger": "Licitación"}], "has_strong_trigger": True},
            {"tender_number": "TEST-002", "procurement_score": 0, "detected_triggers": [], "has_strong_trigger": False},
            {"tender_number": "TEST-003", "procurement_score": 4, "detected_triggers": [{"trigger": "RFP"}], "has_strong_trigger": True}
        ]
        
        print_summary(test_results)
        
        # Verify print was called
        self.assertTrue(mock_print.called)
        
        # Check some of the printed content
        print_calls = [str(call) for call in mock_print.call_args_list]
        printed_text = ' '.join(print_calls)
        
        self.assertIn("Total tenders analyzed: 3", printed_text)
        self.assertIn("Tenders with strong procurement triggers: 2", printed_text)
        self.assertIn("Percentage with strong triggers: 66.7%", printed_text)
        self.assertIn("TEST-001: 4 points", printed_text)

    @patch('builtins.print')
    def test_print_summary_empty_results(self, mock_print):
        """Test print summary with empty results"""
        print_summary([])
        
        # Should handle empty results gracefully
        self.assertTrue(mock_print.called)
        
        print_calls = [str(call) for call in mock_print.call_args_list]
        printed_text = ' '.join(print_calls)
        
        self.assertIn("Total tenders analyzed: 0", printed_text)
        self.assertIn("Tenders with strong procurement triggers: 0", printed_text)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow"""

    def test_full_workflow(self):
        """Test the complete analysis workflow"""
        # Create test data with various scenarios
        test_tenders = [
            {
                "number": "INT-001",
                "description": "Licitación para servicios de TI",
                "type": "Licitación Pública",
                "full_text": "proceso completo con términos de referencia"
            },
            {
                "number": "INT-002", 
                "description": "Simple sale",
                "type": "Venta Directa",
                "full_text": "no formal process language here"
            },
            {
                "number": "INT-003",
                "description": "RFP for consulting",
                "type": "Tender",
                "full_text": "Request for Proposal with evaluation criteria"
            }
        ]
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False) as input_f:
            for tender in test_tenders:
                input_f.write(json.dumps(tender) + '\n')
            input_file = input_f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False) as output_f:
            output_file = output_f.name
        
        try:
            # Run full analysis
            results = analyze_tenders_file(input_file, output_file)
            
            # Verify results
            self.assertEqual(len(results), 3)
            
            # Check individual results
            self.assertEqual(results[0]["procurement_score"], 4)  # Spanish trigger
            self.assertEqual(results[1]["procurement_score"], 0)  # No triggers
            self.assertEqual(results[2]["procurement_score"], 4)  # English trigger
            
            # Verify output file
            self.assertTrue(os.path.exists(output_file))
            with open(output_file, 'r', encoding='utf-8') as f:
                output_lines = f.readlines()
                self.assertEqual(len(output_lines), 3)
                
                # Verify each line is valid JSON
                for line in output_lines:
                    result = json.loads(line.strip())
                    self.assertIn("tender_number", result)
                    self.assertIn("procurement_score", result)
            
        finally:
            os.unlink(input_file)
            os.unlink(output_file)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)

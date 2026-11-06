"""Offline checks: no AWS profile, network calls or real face images."""

import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch


class RekognitionWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        spec = importlib.util.spec_from_file_location(
            "poc_under_test", Path(__file__).resolve().parents[1] / "run.py"
        )
        self.poc = importlib.util.module_from_spec(spec)
        with patch("boto3.Session") as session:
            session.return_value.client.return_value = self.client
            spec.loader.exec_module(self.poc)
            session.assert_called_once_with(profile_name="default")
            session.return_value.client.assert_called_once_with("rekognition")
        self.stdout = io.StringIO()
        self.output = contextlib.redirect_stdout(self.stdout)
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def result(self, **overrides):
        response = {
            "Status": "SUCCEEDED",
            "Confidence": 98.5,
            "ReferenceImage": {"Bytes": b"fabricated-reference-image"},
            "ResponseMetadata": {"RequestId": "fabricated-private-metadata"},
        }
        response.update(overrides)
        self.client.get_face_liveness_session_results.return_value = response

    def test_create_session_returns_service_identifier(self):
        self.client.create_face_liveness_session.return_value = {
            "SessionId": "fabricated-session-id"
        }
        self.assertEqual(self.poc.create_session(), "fabricated-session-id")
        self.client.create_face_liveness_session.assert_called_once_with()

    def test_completed_capture_is_displayed_and_compared(self):
        self.result()
        with patch.object(self.poc, "show_image_from_bytes") as display:
            with patch.object(self.poc, "compare_faces") as compare:
                status = self.poc.get_session_results("fabricated-session-id")
        self.assertEqual(status, "SUCCEEDED")
        self.client.get_face_liveness_session_results.assert_called_once_with(
            SessionId="fabricated-session-id"
        )
        display.assert_called_once_with(b"fabricated-reference-image")
        compare.assert_called_once_with(b"fabricated-reference-image")
        self.assertIn("Confidence: 98.50%", self.stdout.getvalue())

    def test_liveness_only_skips_comparison(self):
        self.result()
        with patch.object(self.poc, "show_image_from_bytes") as display:
            with patch.object(self.poc, "compare_faces") as compare:
                self.poc.get_session_results("fabricated-session-id", False)
        display.assert_called_once()
        compare.assert_not_called()

    def test_missing_reference_does_not_open_or_compare_images(self):
        self.result(ReferenceImage=None)
        with patch.object(self.poc, "show_image_from_bytes") as display:
            with patch.object(self.poc, "compare_faces") as compare:
                self.assertEqual(
                    self.poc.get_session_results("fabricated-session-id"),
                    "SUCCEEDED",
                )
        display.assert_not_called()
        compare.assert_not_called()

    def test_raw_image_bytes_and_response_metadata_are_not_logged(self):
        self.result()
        with patch.object(self.poc, "show_image_from_bytes"):
            self.poc.get_session_results("fabricated-session-id", False)
        output = self.stdout.getvalue()
        self.assertNotIn("fabricated-reference-image", output)
        self.assertNotIn("fabricated-private-metadata", output)
        self.assertNotIn("ReferenceImage", output)

    def test_comparison_sends_bytes_and_experimental_threshold(self):
        self.client.compare_faces.return_value = {
            "FaceMatches": [
                {
                    "Face": {"BoundingBox": {"Left": 0.2, "Top": 0.1}},
                    "Similarity": 92.5,
                }
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            portrait = Path(directory) / "fabricated-portrait.jpg"
            portrait.write_bytes(b"fabricated-source-image")
            count = self.poc.compare_faces(b"fabricated-target-image", portrait)
        self.assertEqual(count, 1)
        self.client.compare_faces.assert_called_once_with(
            SimilarityThreshold=80,
            SourceImage={"Bytes": b"fabricated-source-image"},
            TargetImage={"Bytes": b"fabricated-target-image"},
        )

    def test_no_matches_returns_zero(self):
        self.client.compare_faces.return_value = {"FaceMatches": []}
        with tempfile.TemporaryDirectory() as directory:
            portrait = Path(directory) / "fabricated-portrait.jpg"
            portrait.write_bytes(b"fabricated-source-image")
            self.assertEqual(self.poc.compare_faces(b"fabricated-target", portrait), 0)


if __name__ == "__main__":
    unittest.main()

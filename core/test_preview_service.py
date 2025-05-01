
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

from preview_service import PreviewService
from core import VideoCutter
from gpt_service import GPTServiceOllama

class DummyCutter(VideoCutter):
    def __init__(self, output_dir: Path):
        super().__init__(output_dir=str(output_dir), download_dir=str(output_dir))
        self.calls = []

    def create_short(self, input_path, output_name, start_time, end_time):
        # Instead of actually cutting, record the parameters and create an empty file
        out_path = Path(self.output_dir) / output_name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(f"dummy clip from {start_time} to {end_time}")
        self.calls.append((input_path, output_name, start_time, end_time))
        return out_path

class DummyGPT(GPTServiceOllama):
    def __init__(self, candidates):
        self.candidates = candidates
        self.events = []

    def extract_timecodes(self, text: str):
        # ignore text, return predefined candidates
        return self.candidates

class TestPreviewService(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory and dummy video file
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.video_file = self.tmp_dir / "test_video.mp4"
        # create a dummy "video" file
        self.video_file.write_text("dummy video content")

        # Dummy cutter writes into tmp_dir/shorts
        self.output_dir = self.tmp_dir / "shorts"
        self.cutter = DummyCutter(output_dir=self.output_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_static_preview(self):
        """When use_gpt=False, service should cut first N seconds."""
        gpt = DummyGPT(candidates=[])
        service = PreviewService(
            cutter=self.cutter,
            gpt_service=gpt,
            use_gpt=False,
            max_duration=30
        )
        clip_path = service.create_preview(self.video_file, video_id="dummy")
        # check that a file was created
        self.assertTrue(clip_path.exists())
        # check that cutter was called with start=0, end=30
        self.assertEqual(len(self.cutter.calls), 1)
        _, name, start, end = self.cutter.calls[0]
        self.assertEqual(start, 0.0)
        self.assertEqual(end, 30.0)
        self.assertEqual(name, "preview_start.mp4")

    def test_gpt_preview_with_candidates(self):
        """When use_gpt=True and GPT returns candidates, select shortest ≤ max_duration."""
        # define several overlapping candidates; only ones ≤30 should be considered
        candidates = [
            {"start": "0", "end": "10", "text": "hook1"},
            {"start": "5", "end": "40", "text": "too long"},
            {"start": "20", "end": "45", "text": "too long"},
            {"start": "15", "end": "25", "text": "hook2"},
        ]
        gpt = DummyGPT(candidates=candidates)
        service = PreviewService(
            cutter=self.cutter,
            gpt_service=gpt,
            use_gpt=True,
            max_duration=30
        )
        clip_path = service.create_preview(self.video_file, video_id="dummy")
        # ensure a clip was created
        self.assertTrue(clip_path.exists())
        # the shortest candidate ≤30 sec is from 0 to 10
        self.assertEqual(len(self.cutter.calls), 1)
        _, name, start, end = self.cutter.calls[0]
        self.assertEqual(start, 0.0)
        self.assertEqual(end, 10.0)
        # filename should reflect the times
        self.assertEqual(name, "preview_0-10.mp4")

    def test_gpt_preview_fallback_on_empty(self):
        """When GPT returns no candidates, fallback to start-of-video cut."""
        gpt = DummyGPT(candidates=[])
        service = PreviewService(
            cutter=self.cutter,
            gpt_service=gpt,
            use_gpt=True,
            max_duration=30
        )
        clip_path = service.create_preview(self.video_file, video_id="dummy")
        self.assertTrue(clip_path.exists())
        # fallback uses preview_start.mp4
        _, name, start, end = self.cutter.calls[0]
        self.assertEqual(name, "preview_start.mp4")
        self.assertEqual(start, 0.0)
        self.assertEqual(end, 30.0)

if __name__ == "__main__":
    unittest.main()

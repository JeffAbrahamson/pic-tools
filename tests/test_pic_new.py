#!/usr/bin/python3

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import bin.pic_new as pic_new


class RenameFilesTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_rename_with_orientation_and_raw(self):
        jpg = self.tmpdir / "img_1234.JPG"
        jpg.touch()
        (self.tmpdir / "img_1234.JPG.xmp").touch()
        raw = self.tmpdir / "img_1234.CR2"
        raw.touch()
        (self.tmpdir / "img_1234.CR2.xmp").touch()
        dt = datetime(2020, 1, 2, 3, 4, 5)
        moves = []

        def fake_move(src, dest, backup, rotate, dryrun):
            moves.append((src, dest, rotate, dryrun))

        with patch.object(
            pic_new, "read_exif_datetime", return_value=dt
        ), patch.object(
            pic_new, "check_orientation", return_value=True
        ), patch.object(
            pic_new, "do_move", side_effect=fake_move
        ):
            result = pic_new.rename_files([str(jpg)], dryrun=True)

        base = f"{dt:%Y%m%d-%H%M%S}-1234"
        expect_jpg = str(self.tmpdir / f"{base}.jpg")
        expect_jpg_xmp = expect_jpg + ".xmp"
        expect_raw = str(self.tmpdir / f"{base}.cr2")
        expect_raw_xmp = expect_raw + ".xmp"

        self.assertEqual(
            result,
            [expect_jpg, expect_jpg_xmp, expect_raw, expect_raw_xmp],
        )
        self.assertEqual(moves[0][1], Path(expect_jpg))
        self.assertTrue(moves[0][2])
        self.assertEqual(moves[1][1], Path(expect_jpg_xmp))
        self.assertFalse(moves[1][2])
        self.assertEqual(moves[2][1], Path(expect_raw))
        self.assertFalse(moves[2][2])
        self.assertEqual(moves[3][1], Path(expect_raw_xmp))
        self.assertFalse(moves[3][2])

    def test_fallback_to_file_time_no_orientation(self):
        jpg = self.tmpdir / "pict1001.jpg"
        jpg.touch()
        (self.tmpdir / "pict1001.jpg.xmp").touch()
        mtime = datetime(2021, 6, 7, 8, 9, 10).timestamp()
        os.utime(jpg, (mtime, mtime))
        moves = []

        def fake_move(src, dest, backup, rotate, dryrun):
            moves.append((src, dest, rotate, dryrun))

        with patch.object(
            pic_new, "read_exif_datetime", return_value=None
        ), patch.object(
            pic_new, "check_orientation", return_value=False
        ), patch.object(
            pic_new, "do_move", side_effect=fake_move
        ):
            result = pic_new.rename_files(
                [str(jpg)], offset_hours=1, dryrun=True
            )

        expected_time = datetime.fromtimestamp(mtime) + timedelta(hours=1)
        base = f"{expected_time:%Y%m%d-%H%M%S}-1001"
        expect_jpg = str(self.tmpdir / f"{base}.jpg")
        expect_jpg_xmp = expect_jpg + ".xmp"
        self.assertEqual(result, [expect_jpg, expect_jpg_xmp])
        self.assertFalse(moves[0][2])
        self.assertFalse(moves[1][2])

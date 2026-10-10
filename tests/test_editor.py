"""Unit tests for logic that does not require a running game."""

import struct
import unittest

from evenicle2_live_editor import find_aligned_int32, parse_int32


class ParseInt32Tests(unittest.TestCase):
    def test_accepts_bounds(self):
        self.assertEqual(parse_int32("-2147483648"), -(2**31))
        self.assertEqual(parse_int32("2147483647"), 2**31 - 1)

    def test_rejects_non_decimal_or_out_of_range_values(self):
        for value in ("", "1.5", "0x10", "2147483648", "-2147483649"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_int32(value)


class ScanTests(unittest.TestCase):
    def test_finds_only_aligned_little_endian_values(self):
        target = struct.pack("<i", 123456)
        data = target + b"x" + target + b"xxx" + target
        self.assertEqual(find_aligned_int32(data, 123456), [0, 12])

    def test_alignment_accounts_for_base_address(self):
        data = b"x" + struct.pack("<i", -42)
        self.assertEqual(find_aligned_int32(data, -42, base_address=3), [4])

    def test_does_not_mutate_input(self):
        data = bytearray(struct.pack("<i", 77))
        original = data[:]
        find_aligned_int32(data, 77)
        self.assertEqual(data, original)


if __name__ == "__main__":
    unittest.main()

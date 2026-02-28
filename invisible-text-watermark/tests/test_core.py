import unittest

from invisible_text_watermark import (
    PackedMetadata,
    Watermarker,
    pack_payload,
    unpack_payload,
)
from invisible_text_watermark.config import TagConfig
from invisible_text_watermark.zero_width import (
    decode_tags_from_text,
    encode_payload_to_tag,
)


class PayloadTests(unittest.TestCase):
    def test_roundtrip(self):
        meta = PackedMetadata(1, 123, 4567, 89, 7)
        raw = pack_payload(meta)
        back, valid = unpack_payload(raw)
        self.assertTrue(valid)
        self.assertEqual(back, meta)

    def test_corrupted_crc(self):
        meta = PackedMetadata(1, 1, 0, 0, 1)
        raw = pack_payload(meta)
        corrupted = raw ^ 0x01
        _, valid = unpack_payload(corrupted)
        self.assertFalse(valid)


class ZeroWidthTests(unittest.TestCase):
    def test_encode_decode(self):
        cfg = TagConfig()
        payload = 0x1234567890ABCDEF
        tag = encode_payload_to_tag(payload, cfg)
        got = decode_tags_from_text(f"a{tag}b", cfg)
        self.assertEqual(got, [payload])

    def test_no_tags(self):
        cfg = TagConfig()
        got = decode_tags_from_text("plain text no watermark", cfg)
        self.assertEqual(got, [])


class WatermarkerTests(unittest.TestCase):
    def test_apply_and_detect(self):
        wm = Watermarker(issuer_id=42, model_id=100, key_id=3)
        original = "Hello, this is a test sentence."
        tagged = wm.apply(original)
        self.assertNotEqual(tagged, original)

        result = wm.detect(tagged)
        self.assertTrue(result.watermarked)
        self.assertGreater(result.valid_count, 0)
        self.assertEqual(result.payloads[0]["issuer_id"], 42)
        self.assertEqual(result.payloads[0]["model_id"], 100)
        self.assertEqual(result.payloads[0]["key_id"], 3)

    def test_detect_clean_text(self):
        wm = Watermarker()
        result = wm.detect("no watermark here")
        self.assertFalse(result.watermarked)
        self.assertEqual(result.tag_count, 0)

    def test_strip(self):
        wm = Watermarker()
        tagged = wm.apply("strip me.")
        stripped = Watermarker.strip(tagged)
        self.assertEqual(stripped, "strip me.")

    def test_visible_text_unchanged(self):
        wm = Watermarker()
        original = "The quick brown fox jumps over the lazy dog."
        tagged = wm.apply(original)
        stripped = Watermarker.strip(tagged)
        self.assertEqual(stripped, original)

    def test_multiple_tags_long_text(self):
        wm = Watermarker(repeat_interval_tokens=10)
        text = " ".join(f"word{i}" for i in range(100))
        tagged = wm.apply(text)
        result = wm.detect(tagged)
        self.assertGreater(result.tag_count, 1)


if __name__ == "__main__":
    unittest.main()

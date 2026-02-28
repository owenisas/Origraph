# invisible-text-watermark

Zero-dependency invisible text watermarking using zero-width Unicode characters. Embeds structured metadata (issuer, model, version, key) with CRC8 integrity checking into any text string -- including LLM API responses from OpenAI, Anthropic, and Google Gemini.

## Install

```bash
pip install -e .                    # core only
pip install -e ".[openai]"          # + OpenAI SDK wrapper
pip install -e ".[anthropic]"       # + Anthropic SDK wrapper
pip install -e ".[google]"          # + Gemini SDK wrapper
pip install -e ".[all]"             # everything
```

## Quick start

```python
from invisible_text_watermark import Watermarker

wm = Watermarker(issuer_id=1, model_id=42, key_id=1)

# Embed
tagged = wm.apply("The quick brown fox jumps over the lazy dog.")

# Detect
result = wm.detect(tagged)
print(result.watermarked)   # True
print(result.payloads)      # [{'schema_version': 1, 'issuer_id': 1, ...}]

# Strip
clean = Watermarker.strip(tagged)
print(clean)                # original text, no watermark
```

## SDK integrations

### OpenAI

```python
from openai import OpenAI
from invisible_text_watermark import Watermarker
from invisible_text_watermark.integrations.openai_wrapper import watermark_openai

client = watermark_openai(OpenAI(), Watermarker(issuer_id=1, model_id=100))

resp = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "hello"}],
)
# resp.choices[0].message.content now contains invisible watermark
```

### Anthropic

```python
from anthropic import Anthropic
from invisible_text_watermark import Watermarker
from invisible_text_watermark.integrations.anthropic_wrapper import watermark_anthropic

client = watermark_anthropic(Anthropic(), Watermarker(issuer_id=1, model_id=200))

resp = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=512,
    messages=[{"role": "user", "content": "hello"}],
)
# resp.content[0].text now contains invisible watermark
```

### Google Gemini

```python
import google.generativeai as genai
from invisible_text_watermark import Watermarker
from invisible_text_watermark.integrations.google_wrapper import watermark_gemini

genai.configure(api_key="...")
model = watermark_gemini(
    genai.GenerativeModel("gemini-2.0-flash"),
    Watermarker(issuer_id=1, model_id=300),
)

resp = model.generate_content("hello")
# resp.text now contains invisible watermark
```

---

## Where exactly is the watermark placed in the text?

The watermark is a sequence of **66 invisible Unicode characters** inserted directly into the visible text string:

### Character mapping

| Role | Unicode | Codepoint | Visible? |
|------|---------|-----------|----------|
| Start delimiter | INVISIBLE SEPARATOR | U+2063 | No |
| Bit = 0 | ZERO WIDTH SPACE | U+200B | No |
| Bit = 1 | ZERO WIDTH NON-JOINER | U+200C | No |
| End delimiter | INVISIBLE PLUS | U+2064 | No |

### Tag structure

```
[U+2063] [64 × (U+200B | U+200C)] [U+2064]
 start         payload bits           end
```

Total: 1 start + 64 body + 1 end = **66 characters**, all invisible in rendering.

### Payload bit layout (64 bits)

```
Bits 63-60  (4 bits)  schema_version
Bits 59-48  (12 bits) issuer_id        (0-4095)
Bits 47-32  (16 bits) model_id         (0-65535)
Bits 31-16  (16 bits) model_version_id (0-65535)
Bits 15-8   (8 bits)  key_id           (0-255)
Bits 7-0    (8 bits)  CRC8 checksum    (poly 0x07)
```

### Insertion location

The tag is placed at the **last safe text boundary** scanning backwards from the end of the text. A "safe boundary" is any character in:

```
whitespace  . , ; : ! ? ) ] } " '
```

**Example** (tag shown as `[WM]` for visibility):

```
Input:  "Hello, world! This is a test."
Output: "Hello, world! This is a test.[WM]"
                                      ^
                            inserted after the period
```

If no safe boundary exists, the tag is appended to the end.

### Repeat interval

For long text, the tag is inserted **multiple times** at regular intervals (default: every ~160 whitespace-delimited tokens). This provides redundancy -- if part of the text is truncated or corrupted, remaining tags can still be detected.

```
"...first section of text.[WM] ...middle section of text.[WM] ...final section.[WM]"
```

On finalize, at least one tag is always guaranteed.

---

## Limitations

- **Fragile across channels**: platforms that normalize/strip Unicode (some social media, messaging apps, rich text editors) may remove zero-width characters.
- **Not cryptographic authentication**: CRC8 checks integrity, not authenticity. An adversary who knows the format can forge tags.
- **Detection requires the text**: there is no out-of-band record; if the characters are stripped, the watermark is gone.

## Tests

```bash
PYTHONPATH=src python -m pytest tests/ -v
```

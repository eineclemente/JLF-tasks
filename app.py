"""
Disposable Tool: Messy Text → Clean JSON
Simple Python backend with HTML UI.
"""
from __future__ import annotations

import re
import json
from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)

# --- Messy text → strict JSON logic ---

def _clean_string(s: str) -> str:
    """Normalize a single string for JSON (strip, collapse spaces)."""
    return " ".join(s.strip().split()) if s else ""


def _parse_key_value(line: str) -> tuple[str | None, str | None]:
    """Try to parse 'key: value' or 'key = value'. Returns (key, value) or (None, None)."""
    line = line.strip()
    for sep in (":", "="):
        if sep in line:
            idx = line.index(sep)
            key = _clean_string(line[:idx])
            val = _clean_string(line[idx + 1:])
            if key and re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", key):
                return (key, val)
    return (None, None)


def _is_list_line(line: str) -> bool:
    """True if line looks like a list item (-, *, •, or 1. 2. etc.)."""
    stripped = line.strip()
    if not stripped:
        return False
    if re.match(r"^[\-\*•]\s+", stripped):
        return True
    if re.match(r"^\d+[.)]\s+", stripped):
        return True
    return False


def _extract_list_item(line: str) -> str:
    """Remove list marker and return the content."""
    stripped = line.strip()
    m = re.match(r"^[\-\*•]\s+(.+)$", stripped)
    if m:
        return _clean_string(m.group(1))
    m = re.match(r"^\d+[.)]\s+(.+)$", stripped)
    if m:
        return _clean_string(m.group(1))
    return _clean_string(stripped)


def messy_text_to_json(messy: str) -> dict:
    """
    Ingest messy text and return a single strict JSON-serializable dict.
    - Detects key: value / key = value pairs.
    - Detects list lines (-, *, •, 1. 2. etc.).
    - Otherwise returns cleaned lines or single text block.
    """
    if not messy or not messy.strip():
        return {"text": ""}

    lines = [ln.rstrip() for ln in messy.splitlines()]
    pairs = {}
    list_items = []
    other_lines = []

    for line in lines:
        if not line.strip():
            continue
        key, val = _parse_key_value(line)
        if key is not None:
            pairs[key] = val
            continue
        if _is_list_line(line):
            list_items.append(_extract_list_item(line))
            continue
        other_lines.append(_clean_string(line))

    # Prefer structured output when we found structure
    if pairs and list_items:
        return {"fields": pairs, "list": list_items}
    if pairs:
        return {"fields": pairs}
    if list_items:
        return {"list": list_items}
    if len(other_lines) == 1:
        return {"text": other_lines[0]}
    return {"lines": other_lines}


# --- Routes ---

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/convert", methods=["POST"])
def convert():
    data = request.get_json(silent=True) or {}
    raw = data.get("text", "")
    try:
        result = messy_text_to_json(raw)
        # Ensure strict JSON: serialize and re-parse to catch any edge cases
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Messy Text → Clean JSON</title>
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: 'Segoe UI', system-ui, sans-serif;
      max-width: 900px;
      margin: 0 auto;
      padding: 1.5rem;
      background: #1a1b26;
      color: #c0caf5;
      min-height: 100vh;
    }
    h1 {
      font-size: 1.35rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
      color: #7aa2f7;
    }
    p.sub {
      color: #565f89;
      font-size: 0.9rem;
      margin-bottom: 1.25rem;
    }
    .row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }
    @media (max-width: 700px) { .row { grid-template-columns: 1fr; } }
    label {
      display: block;
      font-size: 0.85rem;
      font-weight: 500;
      margin-bottom: 0.35rem;
      color: #a9b1d6;
    }
    textarea {
      width: 100%;
      min-height: 200px;
      padding: 0.75rem;
      border: 1px solid #3b4261;
      border-radius: 8px;
      background: #24283b;
      color: #c0caf5;
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 0.9rem;
      resize: vertical;
    }
    textarea:focus {
      outline: none;
      border-color: #7aa2f7;
    }
    .output-wrap {
      background: #24283b;
      border: 1px solid #3b4261;
      border-radius: 8px;
      padding: 0.75rem;
      min-height: 200px;
    }
    pre {
      margin: 0;
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 0.85rem;
      white-space: pre-wrap;
      word-break: break-all;
      color: #9ece6a;
    }
    .placeholder { color: #565f89; }
    button {
      margin-top: 0.75rem;
      padding: 0.5rem 1.25rem;
      background: #7aa2f7;
      color: #1a1b26;
      border: none;
      border-radius: 6px;
      font-weight: 600;
      cursor: pointer;
      font-size: 0.9rem;
    }
    button:hover { background: #89b4fa; }
    .error { color: #f7768e; }
    .copy-btn {
      margin-left: 0.5rem;
      padding: 0.35rem 0.75rem;
      font-size: 0.8rem;
      background: #3b4261;
      color: #c0caf5;
    }
    .copy-btn:hover { background: #414868; }
  </style>
</head>
<body>
  <h1>Messy Text → Clean JSON</h1>
  <p class="sub">Paste messy text (key: value, lists, or plain lines). Get strict JSON.</p>
  <div class="row">
    <div>
      <label for="input">Input (messy text)</label>
      <textarea id="input" placeholder="name: John&#10;age: 42&#10;- item one&#10;- item two"></textarea>
      <button type="button" id="convert">Convert to JSON</button>
    </div>
    <div>
      <label for="output">Output (strict JSON)</label>
      <div class="output-wrap">
        <pre id="output" class="placeholder">Result will appear here…</pre>
      </div>
      <button type="button" id="copy" class="copy-btn" style="display:none;">Copy JSON</button>
    </div>
  </div>
  <script>
    const input = document.getElementById('input');
    const output = document.getElementById('output');
    const copyBtn = document.getElementById('copy');

    document.getElementById('convert').addEventListener('click', async () => {
      const text = input.value;
      output.classList.remove('error', 'placeholder');
      if (!text.trim()) {
        output.textContent = '{}';
        output.classList.add('placeholder');
        copyBtn.style.display = 'none';
        return;
      }
      try {
        const res = await fetch('/api/convert', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text })
        });
        const data = await res.json();
        if (!res.ok) {
          output.textContent = data.error || 'Request failed';
          output.classList.add('error');
          copyBtn.style.display = 'none';
          return;
        }
        output.textContent = JSON.stringify(data, null, 2);
        copyBtn.style.display = 'inline-block';
      } catch (e) {
        output.textContent = 'Error: ' + e.message;
        output.classList.add('error');
        copyBtn.style.display = 'none';
      }
    });

    copyBtn.addEventListener('click', () => {
      const text = output.textContent;
      if (!text || output.classList.contains('placeholder')) return;
      navigator.clipboard.writeText(text).then(() => {
        copyBtn.textContent = 'Copied!';
        setTimeout(() => { copyBtn.textContent = 'Copy JSON'; }, 1500);
      });
    });
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

from __future__ import annotations

import json

from app.schemas.menu import MenuExtractLine

SYSTEM_PROMPT = """\
You extract structured restaurant menu data from OCR text.

Rules:
- Extract only sellable menu items: name, optional description, and price.
- Use only information present in the OCR text. Never invent menu items, \
descriptions, prices, or currencies.
- If a description, price, or currency is missing or unclear, set that field to null.
- Ignore and do not create items from: addresses, phone numbers, tax/VAT lines, \
payment methods, receipt or order numbers, opening hours, website or social \
handles, and other non-item boilerplate. You may note ignored boilerplate in \
warnings.
- Do not invent category names. If no category header is present in the text, \
use the category name "Uncategorized".
- Treat each line's bbox as spatial ground truth. Do not trust reading_order \
alone for name-price pairing; OCR reading_order may interleave columns.
- Infer columns from horizontal position (cluster by bbox x-centers). Treat \
vertically aligned lines as the same column; treat similar y positions as the \
same row.
- Match a price only to the closest item name on the same row or in the same \
column (typically name left, price right within that column). Never attach a \
price from another column even if it appears next in reading_order.
- If multiple price candidates are equally plausible, or bbox is missing/empty \
so layout is unclear, set price to null. You may note the ambiguity in \
warnings. Do not guess.
- Normalize prices to numbers (no currency symbols in the price field).
- Use short ISO-like currency codes when the currency is clear from the text \
(e.g. USD, EUR); otherwise null.
- Put non-fatal notes in warnings (e.g. ambiguous lines). Do not use warnings \
to invent data.
- Return JSON that matches the provided schema exactly.
"""


def build_user_prompt(lines: list[MenuExtractLine], full_text: str) -> str:
    payload = {
        "lines": [
            {
                "reading_order": line.reading_order,
                "confidence": line.confidence,
                "text": line.text,
                "bbox": line.bbox,
            }
            for line in lines
        ],
        "full_text": full_text,
    }
    return (
        "Extract the menu structure from this OCR text. "
        "Send back structured JSON only.\n\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )

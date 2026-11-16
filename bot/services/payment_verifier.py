import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from data import database

logger = logging.getLogger(__name__)

def parse_bank_sms(text: str) -> Dict[str, Any]:
    """Parse raw Ethiopian bank SMS (CBE, Telebirr, CBEBirr, BoA) to extract transaction metadata."""
    if not text:
        return {"success": False, "error": "Empty SMS text"}

    clean_text = " ".join(text.strip().split())
    bank = "Unknown"

    # 1. Detect Bank
    if "cbebirr" in clean_text.lower():
        bank = "CBEBirr"
    elif "cbe" in clean_text.lower() or "commercial bank" in clean_text.lower() or re.search(r"\bFT[0-9A-Za-z]{8,}\b", clean_text):
        bank = "CBE"
    elif "telebirr" in clean_text.lower():
        bank = "Telebirr"
    elif "abyssinia" in clean_text.lower() or "boa" in clean_text.lower():
        bank = "BoA"

    # 2. Extract Amount (handles ETB 500.00, 500.00 ETB, ETB 1,250.00, 500 Birr, etc.)
    amt_match = re.search(r"(?:ETB|Birr)\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)", clean_text, re.IGNORECASE)
    if not amt_match:
        amt_match = re.search(r"([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)\s*(?:ETB|Birr)", clean_text, re.IGNORECASE)

    amount = None
    if amt_match:
        try:
            amt_str = amt_match.group(1).replace(",", "")
            amount = float(amt_str)
        except Exception:
            pass

    # 3. Transaction ID / Reference:
    # Handles: 'Ref: FT...', 'Txn Ref: FT...', 'Transaction ID: 1048...', 'Transaction number is 987...'
    txn_id = None
    ft_match = re.search(r"\b(FT[0-9A-Za-z]{8,})\b", clean_text)
    if ft_match:
        txn_id = ft_match.group(1).strip()
    else:
        ref_match = re.search(r"(?:transaction\s*(?:id|number|no)?|txn\s*id|trans\s*id|ref(?:\s*no)?)(?:\s+is|[\s:=]+)+([A-Za-z0-9_-]+)", clean_text, re.IGNORECASE)
        if ref_match:
            candidate = ref_match.group(1).strip()
            if candidate.lower() != "is":
                txn_id = candidate

    # 4. Sender Name:
    # Handles 'from ABEBE KEBEDE', 'from 251911223344 - Meron Desta', 'from Abebe Kebede 251911...'
    sender_name = None
    from_match = re.search(r"from\s+(?:(?:\+?251\d{9}|09\d{8}|07\d{8})\s*[-:]?\s*)?([A-Za-z][A-Za-z\s]+?)(?=(?:\s+\(?\+?251\d|\s+09\d|\s+07\d|\s+on\s+\d|\s*\.|\s*\(|\s+Ref|\s+Txn|\s+Transaction|\s+Current|\s+Your|\s*$))", clean_text, re.IGNORECASE)
    if from_match:
        cand = from_match.group(1).strip()
        cand = re.sub(r"\s+(?:on|with|to|at)$", "", cand, flags=re.IGNORECASE).strip()
        if len(cand) > 2 and cand.lower() not in ("account", "your", "etb", "birr", "current balance"):
            sender_name = cand

    # 5. Phone:
    phone_match = re.search(r"(?:\+?2519\d{8}|\+?2517\d{8}|09\d{8}|07\d{8})", clean_text)
    sender_phone = phone_match.group(0) if phone_match else None

    is_valid = bool(amount and (txn_id or bank != "Unknown"))

    return {
        "success": is_valid,
        "bank": bank,
        "amount": amount,
        "txn_id": txn_id,
        "sender_name": sender_name,
        "sender_phone": sender_phone,
        "raw_text": clean_text
    }

def match_payment_to_order(sms_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Match parsed SMS data against pending orders requiring deposit verification."""
    amount = sms_data.get("amount")
    txn_id = sms_data.get("txn_id")
    sender_name = (sms_data.get("sender_name") or "").lower()
    sender_phone = sms_data.get("sender_phone") or ""

    if not amount and not txn_id:
        return []

    pending_orders = database.get_pending_verification_orders()
    matches = []

    for o in pending_orders:
        order_code = o.get("order_code")
        expected_deposit = float(o.get("deposit_amount") or 0)
        total_price = float(o.get("total_price") or 0)
        cust_name = (o.get("recipient_name") or o.get("full_name") or "").lower()
        cust_phone = (o.get("phone") or "").replace("+", "").replace(" ", "")
        order_ref = (o.get("transaction_ref") or "").strip()

        # Check in notes as well for references: Ref: FT...
        notes = o.get("notes") or ""
        ref_in_notes_match = re.search(r"Ref:\s*([A-Za-z0-9_-]+)", notes, re.IGNORECASE)
        ref_in_notes = ref_in_notes_match.group(1) if ref_in_notes_match else ""

        score = 0
        reasons = []

        # 1. Exact Reference Match
        if txn_id and (txn_id.lower() == order_ref.lower() or txn_id.lower() == ref_in_notes.lower()):
            score += 100
            reasons.append("Exact Transaction Reference match")

        # 2. Amount Match (Exact deposit or full payment within 1 ETB tolerance)
        if amount:
            if abs(amount - expected_deposit) < 1.0:
                score += 50
                reasons.append(f"Deposit amount matched exactly ({amount} ETB)")
            elif abs(amount - total_price) < 1.0:
                score += 50
                reasons.append(f"Full price matched exactly ({amount} ETB)")

        # 3. Customer Name Match (Fuzzy substring)
        if sender_name and cust_name:
            name_parts = [p for p in sender_name.split() if len(p) > 2]
            if any(p in cust_name for p in name_parts):
                score += 30
                reasons.append("Payer name matches customer name")

        # 4. Customer Phone Match
        if sender_phone and cust_phone:
            clean_s_phone = sender_phone.replace("+", "").replace(" ", "")
            if clean_s_phone[-8:] == cust_phone[-8:]:
                score += 40
                reasons.append("Payer phone matches customer phone")

        if score >= 50:
            confidence = "high" if score >= 80 else "medium"
            matches.append({
                "order_code": order_code,
                "customer_name": o.get("recipient_name") or o.get("full_name"),
                "phone": o.get("phone"),
                "items": o.get("items"),
                "expected_deposit": expected_deposit,
                "total_price": total_price,
                "score": score,
                "confidence": confidence,
                "match_reasons": reasons,
                "order": o
            })

    # Sort descending by match score
    matches.sort(key=lambda m: m["score"], reverse=True)
    return matches

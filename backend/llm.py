import requests
import json
import re
import os
import threading
from groq import Groq

_groq_client = None

def get_groq_client():
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _groq_client


_cancel_event = threading.Event()

def cancel_processing():
    _cancel_event.set()
    print("Cancellation requested")

def reset_cancel():
    _cancel_event.clear()

def is_cancelled() -> bool:
    return _cancel_event.is_set()

EXAMPLE = '[{"term": "Facility Amount", "value": "GBP 50,000,000"}, {"term": "Margin", "value": "3.00% per annum"}]'

PROMPT_BASE = (
    "You are a precise financial document analyst. Your job is to extract ONLY terms "
    "that are EXPLICITLY stated in the document text below.\n\n"
    "CRITICAL: Extract values ONLY from the document text provided. "
    "Do NOT use any prior knowledge or examples. Read ONLY what is written.\n\n"
    "STRICT RULES:\n"
    "1. ONLY extract terms you can see word-for-word in the document\n"
    "2. NEVER invent, guess, or calculate values\n"
    "3. NEVER extract a term if its value is not clearly stated\n"
    "4. Copy values EXACTLY as they appear in the document\n"
    "5. If a term is not in this section, do not include it\n"
    "6. NEVER return null, N/A, empty, or placeholder values\n\n"
    "TERMS TO LOOK FOR (only extract if explicitly present):\n"
    "- Borrower: the company defined as the Borrower — copy exact legal name\n"
    "- Lender: the company defined as the Lender — copy exact legal name\n"
    "- Lender / Agent: if lender and agent are the same entity\n"
    "- Agent: the company defined as the Agent — copy exact legal name\n"
    "- Guarantor: the full legal name of the guarantor\n"
    "- Sponsor: the private equity sponsor\n"
    "- Facility Amount: the total loan amount in numbers and currency\n"
    "- Facility Type: the type of credit facility\n"
    "- Term Loan: the term loan amount\n"
    "- Revolver: revolving credit facility amount\n"
    "- DDTL: delayed draw term loan amount\n"
    "- Total Commitments: total facility size\n"
    "- Enterprise Value: total transaction value\n"
    "- Equity Contribution: sponsor equity amount\n"
    "- Leverage at Close: net debt to EBITDA at closing\n"
    "- Reference Rate: SOFR, SONIA, LIBOR or similar benchmark\n"
    "- Spread: basis points over reference rate\n"
    "- All-In Rate: total interest rate at close\n"
    "- PIK Option: payment in kind option if available\n"
    "- PIK Rate: PIK interest rate if applicable\n"
    "- OID: original issue discount\n"
    "- Upfront Fee: fee at closing\n"
    "- Unused Fee: fee on undrawn amounts\n"
    "- Commitment Fee: fee on undrawn amounts with rate\n"
    "- Arrangement Fee: upfront arrangement fee with amount\n"
    "- Prepayment Premium: early repayment penalty schedule\n"
    "- Exit Fee: fee on exit if applicable\n"
    "- Tenor: the loan duration in years\n"
    "- Maturity Date: the final repayment date\n"
    "- Final Maturity Date: the date the loan must be fully repaid\n"
    "- Closing Date: the date at the top of the agreement\n"
    "- Amortization: annual principal repayment percentage\n"
    "- Revolver Maturity: revolving facility maturity\n"
    "- Margin: the percentage margin over benchmark rate\n"
    "- Interest Rate: the full interest rate\n"
    "- Default Rate: interest rate on overdue amounts\n"
    "- Break Costs: prepayment cost description\n"
    "- Availability Period: the drawdown period with dates\n"
    "- Repayment Date: how often repayments occur\n"
    "- Repayment Instalment: the amount of each repayment\n"
    "- Minimum Utilisation: minimum drawdown amount\n"
    "- Loan to Value Ratio: LTV covenant percentage\n"
    "- Maximum Total Net Leverage: maximum net leverage covenant\n"
    "- Minimum Interest Coverage Ratio: ICR covenant multiple\n"
    "- Interest Coverage Ratio: ICR covenant multiple\n"
    "- Minimum Fixed Charge Coverage Ratio: FCCR covenant\n"
    "- Debt Service Coverage Ratio: DSCR covenant multiple\n"
    "- Minimum Liquidity: minimum cash requirement\n"
    "- Add-back cap in aggregate: EBITDA add-back cap\n"
    "- Indebtedness: permitted indebtedness basket\n"
    "- Asset Sales: permitted asset sale threshold\n"
    "- Investments / Acquisitions threshold: acquisition limit\n"
    "- Events of Default: list of trigger conditions\n"
    "- Purpose: the stated purpose of the facility\n"
    "- Security: collateral description\n"
    "- Governing Law: the jurisdiction governing the agreement\n"
    "- Jurisdiction: courts with exclusive jurisdiction\n\n"
    "OUTPUT FORMAT:\n"
    "Return ONLY a valid JSON array. No explanation. No markdown. No code blocks.\n"
    "Start with [ and end with ].\n\n"
    "Example:\n"
)

def build_prompt(chunk: str) -> str:
    return PROMPT_BASE + EXAMPLE + "\n\nDOCUMENT SECTION:\n" + chunk

def extract_terms_from_chunk(chunk: str, retries: int = 2) -> list[dict]:
    prompt = build_prompt(chunk)

    for attempt in range(retries + 1):
        try:
            response = get_groq_client().chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=2000,
            )

            raw = response.choices[0].message.content.strip()

            if "```json" in raw:
                aw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start != -1 and end != 0:
                raw = raw[start:end]
            else:
                start = raw.find("[")
                if start != -1:
                    last_complete = raw.rfind("},")
                    if last_complete != -1:
                        raw = raw[start:last_complete + 1] + "]"
                    else:
                        return []
                else:
                    return []

            terms = json.loads(raw)

            cleaned = []
            for t in terms:
                if isinstance(t, dict) and "term" in t and "value" in t:
                    clean_val = clean_value(str(t.get("value", "")))
                    if clean_val and is_valid_term_name(str(t["term"]).strip()):
                        cleaned.append({
                            "term": str(t["term"]).strip(),
                            "value": clean_val
                        })

            return cleaned

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries:
                print("Retrying chunk...")
                continue
            return []

def clean_value(value: str) -> str:
    value = value.strip()
    invalid = {
        "", "null", "none", "n/a", "—", "-",
        "unknown", "not stated", "not specified",
        "not applicable", "not explicitly stated",
        "not provided", "not mentioned",
        "tbd", "to be determined", "to be confirmed",
        "please refer to annexure",
        "as the case may be"
    }
    if value.lower() in invalid:
        return ""
    if re.match(r'^[ivxlcdmIVXLCDM]{1,4}-$', value):
        return ""
    if re.match(r'^\d{1,3}-$', value):
        return ""
    return value

def normalize_term_name(term: str) -> str:
    term = term.lower().strip()
    term = re.sub(r'\s*\(.*?\)', '', term)
    term = " ".join(term.split())
    return term

def normalize_value(value: str) -> str:
    return " ".join(value.lower().strip().split())

def deduplicate_terms(terms: list[dict]) -> list[dict]:
    seen = {}

    def is_similar_term(key1: str, key2: str) -> bool:
        return key1 in key2 or key2 in key1

    for term in terms:
        key = normalize_term_name(term["term"])
        value = term["value"]

        matched_key = None
        for existing_key in seen:
            if is_similar_term(key, existing_key):
                matched_key = existing_key
                break

        if matched_key:
            # always overwrite with latest value
            # since pre_extracted comes last it always wins
            seen[matched_key] = term
        else:
            seen[key] = term

    return list(seen.values())

def extract_facility_amount(text: str) -> list[dict]:
    # more specific patterns — must be near facility/commitment keywords
    patterns = [
        # "Total Commitments: $425,000,000"
        r'[Tt]otal\s+[Cc]ommitments?[:\s]+(\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion))?)',
        # "aggregate amount of GBP 120,000,000"
        r'aggregate\s+amount\s+(?:of\s+|equal\s+to\s+)?([A-Z]{2,3}\s+[\d,]+(?:\.\d+)?)',
        # "Facility: $425,000,000" or "Facility Amount: $425,000,000"
        r'[Ff]acility\s+(?:[Aa]mount)?[:\s]+(\$[\d,]+(?:\.\d+)?)',
        # "term loan facility in an aggregate amount equal to GBP X"
        r'term\s+loan\s+facility[^$£€]{0,50}([A-Z]{2,3}\s+[\d,]+(?:\.\d+)?)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text[:8000], re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if value and len(value) > 3:
                print(f"Facility amount pre-extracted: {value}")
                return [{"term": "Facility Amount", "value": value}]

    return []


def extract_document_date(text: str) -> list[dict]:
    dates = []
    pattern = r'[Dd]ated?:?\s+(\d{1,2}\s+\w+\s+\d{4})'
    match = re.search(pattern, text[:500])
    if match:
        dates.append({
            "term": "Closing Date",
            "value": match.group(1).strip()
        })
        print(f"Closing date pre-extracted: {match.group(1)}")
    return dates

def extract_parties_regex(text: str) -> list[dict]:
    parties = []
    seen_roles = set()

    valid_roles = {
        "borrower", "lender", "agent", "guarantor",
        "arranger", "facility agent", "security agent",
        "administrative agent", "trustee", "sponsor",
        "lender / agent", "lender/agent"
    }

    # company name suffixes that indicate a real company
    company_suffixes = (
        "LIMITED", "LLP", "PLC", "LLC", "LP",
        "INC", "CORP", "FUND", "BANK", "PARTNERS",
        "HOLDINGS", "CAPITAL", "TRUST", "CORPORATION"
    )

    role_pattern = r'\((?:the\s*)?"([^"]{2,40})"\)'

    matches = re.finditer(role_pattern, text[:6000])

    for match in matches:
        role = match.group(1).strip()
        if role.lower() not in valid_roles:
            continue
        if role.lower() in seen_roles:
            continue

        # look backwards 600 chars from role label
        before_text = text[max(0, match.start() - 600):match.start()]

        # find ALL CAPS sequences
        caps_pattern = r'([A-Z][A-Z\s,\.]+)'
        caps_matches = list(re.finditer(caps_pattern, before_text))

        # find the last caps match that ends with a company suffix
        name = None
        for caps_match in reversed(caps_matches):
            candidate = caps_match.group(1).strip().rstrip(',. ')
            if any(candidate.upper().endswith(suffix) for suffix in company_suffixes):
                name = candidate
                break

        # fallback — just take the last caps match
        if not name and caps_matches:
            name = caps_matches[-1].group(1).strip().rstrip(',. ')

        if name and len(name) > 3:
            seen_roles.add(role.lower())
            parties.append({
                "term": role.title(),
                "value": name
            })
            print(f"Party pre-extracted: {role} → {name}")

    return parties

# filter out rows where term looks like a value
def is_valid_term_name(term: str) -> bool:
    # term names should not start with currency, numbers, or symbols
    invalid_starts = (
        '$', '£', '€', 'GBP', 'USD', 'EUR',
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
        '(', '•', '-', '+'
    )
    return not any(term.startswith(s) for s in invalid_starts)


def _process_chunks(chunks: list[str]) -> list[dict] | None:
    all_terms = []
    for i, chunk in enumerate(chunks):

        if is_cancelled():
            print(f"Cancelled at chunk {i + 1}")
            return None

        print(f"Processing chunk {i + 1}/{len(chunks)}...")
        terms = extract_terms_from_chunk(chunk)

        if is_cancelled():
            print(f"Cancelled after chunk {i + 1}")
            return None

        if len(terms) == 0 and i == 0:
            print("First chunk failed — retrying with 3 smaller chunks...")
            third = len(chunk) // 3
            mini_chunks = [
                chunk[:third],
                chunk[third:third * 2],
                chunk[third * 2:]
            ]
            for j, mini in enumerate(mini_chunks):
                if is_cancelled():
                    return None
                print(f"Retrying mini chunk {j + 1}/3...")
                mini_terms = extract_terms_from_chunk(mini)
                print(f"Found {len(mini_terms)} terms in mini chunk {j + 1}")
                all_terms.extend(mini_terms)
        else:
            print(f"Found {len(terms)} terms in chunk {i + 1}")
            all_terms.extend(terms)

    return all_terms

def extract_table_style_terms(text: str) -> list[dict]:
    terms = []
    valid_term_starts = {
        "borrower", "lender", "agent", "sponsor", "guarantor",
        "facility", "term loan", "revolver", "ddtl", "total",
        "reference rate", "spread", "all-in",
        "pik option",
        "pik rate",
        "oid",
        "upfront fee", "unused fee", "prepayment premium", "exit fee",
        "tenor", "amortization", "maturity", "governing",
        "jurisdiction", "enterprise", "equity contribution",
        "equity cure",
        "leverage", "minimum", "maximum", "indebtedness", "asset sales",
        "intercreditor", "transaction", "security",
        "maximum total net leverage",
        "minimum interest coverage", "minimum fixed charge",
        "minimum liquidity", "add-back cap",
        "restricted payments", "liens", "investments"
    }

    lines = text.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        line = line.lstrip('•·-– ').strip()

        if ':' not in line:
            i += 1
            continue

        colon_pos = line.find(':')
        if colon_pos < 2 or colon_pos > 60:
            i += 1
            continue

        term = line[:colon_pos].strip()
        value = line[colon_pos + 1:].strip()
        value = value.lstrip('| ').strip()

        if not any(term.lower().startswith(s) for s in valid_term_starts):
            i += 1
            continue

        # if value is empty — look at next line
        if not value and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line and len(next_line) > 2:
                next_colon = next_line.find(':')
                next_term = next_line[:next_colon].strip().lower() \
                    if next_colon > 0 else ""

                # only skip if next line is an exact known term label
                is_new_term = next_term in valid_term_starts if next_term else False

                if not is_new_term:
                    value = next_line.lstrip('| ').strip()
                    i += 1

        # clean role labels from values
        value = re.sub(r'\s*\((?:the\s*)?"[^"]+"\)', '', value).strip()
        value = re.sub(r'\(".*?"\s+and\s+".*?"\)', '', value).strip()
        value = value.rstrip(' ,')

        if not value or len(value) < 2 or len(value) > 500:
            i += 1
            continue

        terms.append({"term": term, "value": value})
        print(f"Table-style extracted: {term} → {value[:50]}")

        i += 1

    return terms

def _build_chunks(text: str) -> tuple[list[str], str]:
    lower_text = text.lower()

    markers = [
        "1. definitions", "1.definitions",
        "definitions and interpretation",
        "article 1", "section 1.", "clause 1.",
        "1. parties", "parties", "deal summary", "credit facility"
    ]

    end_markers = [
        "2. the facility", "2.the facility",
        "article 2", "section 2.",
        "clause 2.", "3. utilisation",
    ]

    start_pos = 0
    for marker in markers:
        pos = lower_text.find(marker)
        if pos != -1:
            start_pos = max(0, pos - 200)
            print(f"Found start section at position {pos}")
            break

    end_pos = min(start_pos + 25000, len(text))
    for marker in end_markers:
        pos = lower_text.find(marker, start_pos + 100)
        if pos != -1 and pos < end_pos:
            end_pos = min(pos + 5000, len(text))
            break

    extracted = text[start_pos:end_pos]
    print(f"Processing {len(extracted)} characters")

    chunk_size = 2000
    overlap = 200
    chunks = []

    start = 0
    while start < len(extracted):
        end = start + chunk_size
        chunks.append(extracted[start:end])
        start = end - overlap

    print(f"Processing {len(chunks)} chunks...")
    return chunks, extracted

def _process_chunks(chunks: list[str]) -> list[dict] | None:
    all_terms = []
    for i, chunk in enumerate(chunks):

        if is_cancelled():
            print(f"Cancelled at chunk {i + 1}")
            return None

        print(f"Processing chunk {i + 1}/{len(chunks)}...")
        terms = extract_terms_from_chunk(chunk)

        if is_cancelled():
            print(f"Cancelled after chunk {i + 1}")
            return None

        if len(terms) == 0:  # ← removed "and i == 0"
            print(f"Chunk {i + 1} returned 0 terms — retrying with 3 smaller chunks...")
            third = len(chunk) // 3
            mini_chunks = [
                chunk[:third],
                chunk[third:third * 2],
                chunk[third * 2:]
            ]
            for j, mini in enumerate(mini_chunks):
                if is_cancelled():
                    return None
                print(f"Retrying mini chunk {j + 1}/3...")
                mini_terms = extract_terms_from_chunk(mini)
                print(f"Found {len(mini_terms)} terms in mini chunk {j + 1}")
                all_terms.extend(mini_terms)
        else:
            print(f"Found {len(terms)} terms in chunk {i + 1}")
            all_terms.extend(terms)

    return all_terms

def extract_terms_with_ollama(text: str) -> list[dict]:
    pre_extracted = extract_document_date(text) + extract_parties_regex(text) + extract_facility_amount(text)

    chunks, _ = _build_chunks(text)
    all_terms = []

    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i + 1}/{len(chunks)}...")
        terms = extract_terms_from_chunk(chunk)
        print(f"Found {len(terms)} terms in chunk {i + 1}")
        all_terms.extend(terms)

    all_terms = all_terms + pre_extracted
    unique_terms = deduplicate_terms(all_terms)
    print(f"Total unique terms: {len(unique_terms)}")
    return unique_terms

def extract_covenant_terms(text: str) -> list[dict]:
    terms = []

    patterns = {
        "Loan to Value Ratio": [
            r'[Ll]oan\s+to\s+[Vv]alue\s+[Rr]atio[^.]*?(\d+(?:\.\d+)?%)',
        ],
        "Interest Coverage Ratio": [
            r'[Ii]nterest\s+[Cc]overage\s+[Rr]atio[^.]*?(\d+(?:\.\d+)?x)',
        ],
        "Debt Service Coverage Ratio": [
            r'[Dd]ebt\s+[Ss]ervice\s+[Cc]overage\s+[Rr]atio[^.]*?(\d+(?:\.\d+)?x)',
        ],
        "Minimum Utilisation": [
            r'minimum\s+amount\s+of\s+each\s+[Uu]tilisation\s+is\s+([A-Z]{2,3}\s+[\d,]+)',
        ],
        "Jurisdiction": [
            r'courts?\s+of\s+(England[^.\n]*?)\s+shall\s+have',
            r'submit\s+to\s+the\s+exclusive\s+jurisdiction\s+of\s+the\s+courts?\s+of\s+([^.\n]+?)\s+for',
            r'irrevocably\s+agree\s+that\s+the\s+courts?\s+of\s+([^.\n]{5,50}?)\s+shall',
        ],
        "Governing Law": [
            r'governed\s+by\s+and\s+construed\s+in\s+accordance\s+with\s+(?:the\s+)?(?:existing\s+)?laws?\s+of\s+(England[^.\n]*)',
            r'governed\s+by\s+and\s+construed\s+in\s+accordance\s+with\s+(?:the\s+)?(?:existing\s+)?laws?\s+of\s+(?:the\s+)?(?:State\s+of\s+)?([^.\n]{3,30})',
        ],
        "Purpose": [
            r'[Pp]urpose\s+(?:of\s+the\s+[Ff]acility\s+)?is\s+to\s+([^.]+\.)',
        ],
        "Security": [
            r'secured\s+by[:\s]+([^.]+(?:charge|debenture|mortgage|assignment)[^.]+\.)',
        ],
        "Base Rate / Benchmark": [
            r'"([Ss][Oo][Nn][Ii][Aa]|[Ss][Oo][Ff][Rr]|[Ll][Ii][Bb][Oo][Rr])"\s+means',
            r'means\s+the\s+aggregate\s+of\s+(SONIA|SOFR|LIBOR)',
        ],
        "Repayment Instalment": [
            r'equal\s+quarterly\s+instalments\s+of\s+([A-Z]{2,3}\s+[\d,]+)',
        ],
        "Events of Default": [
            r'[Ee]vents?\s+of\s+[Dd]efault[:\s]+([^.]+(?:non-payment|insolvency|breach)[^.]+\.)',
        ],
        "Add-back cap in aggregate": [
            r'[Aa]dd-back\s+cap\s+in\s+aggregate[:\s]+(\d+%[^.\n]+)',
            r'[Aa]dd-back\s+cap\s+in\s+aggregate[:\s]+([^.\n]+)',
        ],
        "Net Debt to EBITDA Ratio": [
            r'[Nn]et\s+[Dd]ebt\s+to\s+[Ee][Bb][Ii][Tt][Dd][Aa]\s+[Rr]atio[^.]*?(\d+(?:\.\d+)?x)',
        ],
        "Current Ratio": [
            r'[Cc]urrent\s+[Rr]atio[^.]*?(\d+(?:\.\d+)?x)',
        ],
    }

    for term_name, term_patterns in patterns.items():
        for pattern in term_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                value = " ".join(value.split())
                if value and len(value) > 1:
                    terms.append({"term": term_name, "value": value})
                    print(f"Covenant extracted: {term_name} → {value[:50]}")
                    break

    return terms

TERM_NAME_MAP = {
    "facility": "Facility Type",
    "the facility": "Facility Type",
    "interest rate": "Interest Rate",
    "base rate": "Base Rate / Benchmark",
    "reference rate": "Reference Rate",
}

def parse_definitions_section(text: str) -> list[dict]:
    terms = []
    lower = text.lower()

    start = 0
    for marker in ["1. definitions", "definitions and interpretation"]:
        pos = lower.find(marker)
        if pos != -1:
            start = pos
            break

    end = min(start + 10000, len(text))
    for marker in ["2. the facility", "2. facility", "2.the facility"]:
        pos = lower.find(marker, start + 100)
        if pos != -1:
            end = pos
            break

    definitions_text = text[start:end]

    pattern = r'"([^"]{2,60})"\s+means\s+([^"]{5,400}?)(?=\n\s*"|\n\n|$)'
    matches = re.finditer(pattern, definitions_text, re.DOTALL)

    for match in matches:
        term = match.group(1).strip()
        value = " ".join(match.group(2).strip().split())

        # remove trailing period
        value = value.rstrip('.')

        # map to proper term names
        mapped_term = TERM_NAME_MAP.get(term.lower(), term)

        if len(value) > 3:
            terms.append({"term": mapped_term, "value": value})
            print(f"Definition extracted: {mapped_term} → {value[:50]}")

    return terms

def extract_terms_with_cancellation(text: str) -> list[dict] | None:
    reset_cancel()

    pre_extracted = (
        extract_document_date(text) +
        extract_parties_regex(text) +
        extract_facility_amount(text) +
        parse_definitions_section(text) +  # ← add this
        extract_covenant_terms(text) +
        extract_table_style_terms(text)
    )

    print("Pre-extracted terms:")
    for t in pre_extracted:
        print(f"  {t['term']} → {t['value'][:50]}")

    chunks, _ = _build_chunks(text)
    all_terms = _process_chunks(chunks)

    if all_terms is None:
        return None

    # LLM first, regex last — regex always wins
    all_terms = all_terms + pre_extracted
    unique_terms = deduplicate_terms(all_terms)
    print(f"Total unique terms: {len(unique_terms)}")
    return unique_terms
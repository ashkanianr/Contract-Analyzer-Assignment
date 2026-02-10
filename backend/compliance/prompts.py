"""Compliance and chat prompt text and builders. Table 1 requirements + instructions."""

# Table 1: Exact requirement text for each of the 5 compliance questions (from assignment).
COMPLIANCE_REQUIREMENTS = [
    {
        "number": 1,
        "label": "Password Management",
        "requirement": (
            "Password Management. The contract must require a documented password standard "
            "covering password length/strength, prohibition of default and known-compromised passwords, "
            "secure storage (no plaintext; salted hashing if stored), brute-force protections "
            "(lockout/rate limiting), prohibition on password sharing, vaulting of privileged "
            "credentials/recovery codes, and time-based rotation for break-glass credentials. "
            "Based on the contract language and exhibits, what is the compliance state for Password Management?"
        ),
    },
    {
        "number": 2,
        "label": "IT Asset Management",
        "requirement": (
            "IT Asset Management. The contract must require an in-scope asset inventory "
            "(including cloud accounts/subscriptions, workloads, databases, security tooling), "
            "define minimum inventory fields, require at least quarterly reconciliation/review, "
            "and require secure configuration baselines with drift remediation and prohibition of "
            "insecure defaults. Based on the contract language and exhibits, what is the compliance "
            "state for IT Asset Management?"
        ),
    },
    {
        "number": 3,
        "label": "Security Training & Background Checks",
        "requirement": (
            "Security Training & Background Checks. The contract must require security awareness "
            "training on hire and at least annually, and background screening for personnel with "
            "access to Company Data to the extent permitted by law, including maintaining a "
            "screening policy and attestation/evidence. Based on the contract language and exhibits, "
            "what is the compliance state for Security Training and Background Checks?"
        ),
    },
    {
        "number": 4,
        "label": "Data in Transit Encryption",
        "requirement": (
            "Data in Transit Encryption. The contract must require encryption of Company Data "
            "in transit using TLS 1.2+ (preferably TLS 1.3 where feasible) for Company-to-Service "
            "traffic, administrative access pathways, and applicable Service-to-Subprocessor "
            "transfers, with certificate management and avoidance of insecure cipher suites. "
            "Based on the contract language and exhibits, what is the compliance state for "
            "Data in Transit Encryption?"
        ),
    },
    {
        "number": 5,
        "label": "Network Authentication & Authorization Protocols",
        "requirement": (
            "Network Authentication & Authorization Protocols. The contract must specify the "
            "authentication mechanisms (e.g., SAML SSO for users, OAuth/token-based for APIs), "
            "require MFA for privileged/production access, require secure admin pathways "
            "(bastion/secure gateway) with session logging, and require RBAC authorization. "
            "Based on the contract language and exhibits, what is the compliance state for "
            "Network Authentication and Authorization Protocols?"
        ),
    },
]

COMPLIANCE_SYSTEM_PROMPT = """You are a contract compliance analyst. Compare the contract text to each of the following requirements and output only valid JSON.

Rules:
- Compliance State for each question must be exactly one of: Fully Compliant, Partially Compliant, Non-Compliant.
- Cite contract language and exhibits in Relevant Quotes (e.g. "Section 6.6", "Exhibit G (PASS-01)").
- Output a JSON array of exactly 5 objects, one per requirement in order (1 to 5).
- Each object must have: compliance_question (short label), compliance_state, relevant_quotes (string or array of strings), rationale, and optionally confidence (0-100).
- Do not include any text outside the JSON array."""


def build_compliance_user_prompt(contract_text: str) -> str:
    """Build the user prompt for compliance analysis: contract text + requirement list + output instruction."""
    requirements_block = "\n\n".join(
        f"**Question {r['number']} – {r['label']}**\n{r['requirement']}"
        for r in COMPLIANCE_REQUIREMENTS
    )
    return f"""## Contract text

{contract_text}

---

## Requirements (Table 1)

{requirements_block}

---

## Your task

Return a JSON array of exactly 5 objects, one per requirement above, in the same order. Each object must have:
- compliance_question: short label (e.g. "Password Management")
- compliance_state: exactly one of "Fully Compliant", "Partially Compliant", "Non-Compliant"
- relevant_quotes: string or array of strings citing contract sections/exhibits
- rationale: your reasoning for the compliance state
- confidence: optional number 0-100

Output only the JSON array, no other text."""


# Chat (bonus): informational only; compliance decisions come from structured analyzer.
CHAT_SYSTEM_TEMPLATE = """Answer only based on the following contract. If the answer is not in the contract, say so. Do not make compliance judgments; those come from the structured analyzer. Be concise and cite sections or exhibits when relevant."""

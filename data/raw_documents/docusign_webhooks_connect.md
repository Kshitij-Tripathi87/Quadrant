# DocuSign Connect: Webhooks & HMAC Signature Verification

DocuSign Connect is an enterprise webhook notification service that publishes real-time envelope status transitions to external endpoints, eliminating polling.

## 1. Webhook Architecture & Event Triggers

DocuSign Connect publishes JSON (SIM) or XML payloads containing:
- Envelope metadata: `envelopeId`, `status`, `createdDateTime`, `completedDateTime`
- Recipient status: `deliveredDateTime`, `signedDateTime`, `declinedReason`
- Document and custom field metadata

### Recommended Event Triggers
- `envelope-sent`: Envelope queued and routed.
- `envelope-delivered`: Signer opened and viewed the documents.
- `envelope-completed`: All recipients signed; documents are legally closed.
- `envelope-declined`: Signer rejected signature terms.
- `envelope-voided`: Sender canceled the envelope.

---

## 2. Validating HMAC SHA-256 Webhook Signatures

To ensure payloads originate from DocuSign and have not been tampered with in transit, DocuSign signs the raw request payload with a secret key using HMAC SHA-256 and sends up to 100 signatures in headers `X-DocuSign-Signature-1` through `X-DocuSign-Signature-100`.

### Python / FastAPI Verification Implementation

```python
import hmac
import hashlib
import base64
from fastapi import FastAPI, Request, HTTPException, status

app = FastAPI()
DOCUSIGN_HMAC_SECRET = b"your_configured_hmac_secret_key"

def verify_docusign_hmac(payload_bytes: bytes, received_signature: str, secret: bytes) -> bool:
    """
    Computes HMAC-SHA256 hash of payload bytes and compares with DocuSign header.
    """
    computed_digest = hmac.new(
        key=secret,
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(computed_digest).decode("utf-8")
    return hmac.compare_digest(expected_signature, received_signature)

@app.post("/api/v1/docusign/webhook")
async def handle_docusign_webhook(request: Request):
    # 1. Read raw body bytes
    body_bytes = await request.body()

    # 2. Extract signature header
    signature = request.headers.get("x-docusign-signature-1")
    if not signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing signature header")

    # 3. Verify authenticity
    is_valid = verify_docusign_hmac(body_bytes, signature, DOCUSIGN_HMAC_SECRET)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid HMAC signature")

    # 4. Parse payload and process idempotently
    payload = await request.json()
    envelope_id = payload.get("data", {}).get("envelopeId")
    status_event = payload.get("event")

    print(f"Verified webhook for envelope {envelope_id}: status={status_event}")
    return {"status": "success", "envelope_id": envelope_id}
```

---

## 3. Idempotency and Retry Logic

- **Retry Schedule**: DocuSign retries delivery up to 15 times over several days if your server responds with non-2xx status or times out.
- **Idempotency Guard**: Always store the latest processed status timestamp for each `envelopeId` to prevent duplicate processing on retries.

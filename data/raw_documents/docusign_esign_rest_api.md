# DocuSign eSignature REST API: Envelope Lifecycle & Python SDK Integration

The DocuSign eSignature REST API enables developers to programmatically upload documents, configure signers, place tabs (signature, initial, date fields), and send envelopes for legally binding electronic signatures.

## 1. Envelope Lifecycle and State Transitions

An **Envelope** is the primary container in DocuSign representing a transaction. It contains one or more documents, one or more recipients, and tabs assigned to each recipient.

### Envelope Statuses
1. `created`: The envelope is saved as a draft on the server but has not yet been routed to recipients.
2. `sent`: The envelope has been dispatched to recipients via email or SMS notifications.
3. `delivered`: At least one recipient has opened and viewed the envelope.
4. `completed`: All recipients have completed their required actions (signed, approved, acknowledged).
5. `declined`: A recipient explicitly refused to sign the envelope.
6. `voided`: The sender canceled the envelope before all actions were completed.

---

## 2. Python SDK: Sending an Envelope

To send an envelope using the official `docusign-esign` Python SDK, construct `Document`, `Signer`, `SignHere` tab, and `EnvelopeDefinition` objects.

```python
import base64
from docusign_esign import (
    ApiClient,
    EnvelopesApi,
    EnvelopeDefinition,
    Document,
    Signer,
    SignHere,
    Tabs,
    Recipients,
)

def send_signature_request(
    api_client: ApiClient,
    account_id: str,
    pdf_bytes: bytes,
    signer_name: str,
    signer_email: str,
) -> str:
    """
    Creates and sends a DocuSign envelope with a single PDF document
    and a pre-positioned SignHere tab.
    """
    envelopes_api = EnvelopesApi(api_client)

    # 1. Base64 encode the document
    doc_b64 = base64.b64encode(pdf_bytes).decode("ascii")
    document = Document(
        document_base64=doc_b64,
        name="Master Service Agreement",
        file_extension="pdf",
        document_id="1",
    )

    # 2. Define the Signer Recipient
    signer = Signer(
        email=signer_email,
        name=signer_name,
        recipient_id="1",
        routing_order="1",
    )

    # 3. Position the Signature Tab
    sign_here = SignHere(
        document_id="1",
        page_number="1",
        recipient_id="1",
        x_position="150",
        y_position="500",
        tab_label="SignHereAnchor",
    )
    signer.tabs = Tabs(sign_here_tabs=[sign_here])

    # 4. Assemble Envelope Definition
    envelope_definition = EnvelopeDefinition(
        email_subject="Please sign: Master Service Agreement",
        documents=[document],
        recipients=Recipients(signers=[signer]),
        status="sent",  # 'sent' triggers immediate delivery
    )

    # 5. Dispatch via REST API
    results = envelopes_api.create_envelope(
        account_id=account_id,
        envelope_definition=envelope_definition,
    )
    return results.envelope_id
```

---

## 3. Voiding an In-Flight Envelope

Senders can cancel an envelope at any time before completion by updating its status to `voided`.

```python
from docusign_esign import Envelope

def void_active_envelope(
    envelopes_api: EnvelopesApi,
    account_id: str,
    envelope_id: str,
    reason: str,
):
    env_update = Envelope(status="voided", voided_reason=reason)
    envelopes_api.update(
        account_id=account_id,
        envelope_id=envelope_id,
        envelope=env_update,
    )
```

### Common Error Codes
- `ENVELOPE_DOES_NOT_EXIST`: Specified envelopeId is invalid or belongs to another account.
- `ENVELOPE_CANNOT_BE_VOIDED`: Envelope has already reached `completed` or `declined` terminal status.

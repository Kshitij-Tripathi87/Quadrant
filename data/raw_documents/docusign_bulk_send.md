# DocuSign Bulk Send API: High-Volume Automated Dispatch

The Bulk Send API enables organizations to send individualized copies of a standardized document or template to hundreds or thousands of recipients simultaneously.

## 1. Bulk Send Architecture

1. **Create Bulk Send List**: Submit a list of recipient rows with individual names, emails, and custom tab values (`BulkEnvelopesApi.create_bulk_send_list`).
2. **Create Draft Envelope**: Define an envelope with a placeholder recipient assigned to the bulk list.
3. **Send Bulk Batch**: Dispatch the batch associating the draft envelope with the bulk list (`BulkEnvelopesApi.send_bulk_send_batch`).
4. **Monitor Batch Progress**: Poll or receive webhooks for batch delivery statistics (`BulkEnvelopesApi.get_bulk_send_batch_status`).

---

## 2. Python Implementation: Bulk Send Batch

```python
from docusign_esign import (
    BulkEnvelopesApi,
    BulkSendingList,
    BulkSendingCopy,
    BulkSendingCopyRecipient,
    BulkSendRequest,
)

def dispatch_bulk_envelopes(
    bulk_api: BulkEnvelopesApi,
    account_id: str,
    envelope_id: str,
    recipient_entries: list,
) -> str:
    """
    Creates a bulk sending list and dispatches a batch of envelopes.
    """
    # 1. Build recipient list copies
    copies = []
    for entry in recipient_entries:
        recipient = BulkSendingCopyRecipient(
            email=entry["email"],
            name=entry["name"],
            role_name="Signer",
        )
        copies.append(BulkSendingCopy(recipients=[recipient]))

    bulk_list = BulkSendingList(
        name="Quarterly Policy Acknowledgement",
        bulk_copies=copies,
    )

    # 2. Register the list
    list_result = bulk_api.create_bulk_send_list(
        account_id=account_id,
        bulk_sending_list=bulk_list,
    )
    list_id = list_result.list_id

    # 3. Associate and dispatch batch
    send_request = BulkSendRequest(envelope_or_template_id=envelope_id)
    batch_result = bulk_api.send_bulk_send_batch(
        account_id=account_id,
        bulk_send_list_id=list_id,
        bulk_send_request=send_request,
    )

    return batch_result.batch_id
```

### Batch Status & Rate Limits
- Bulk send operations are asynchronous and batched.
- Status values include: `Queued`, `Processing`, `Sent`, `Failed`.
- DocuSign enforces hourly burst rate limits; use bulk send rather than loop-calling `create_envelope` for volume over 50 documents.

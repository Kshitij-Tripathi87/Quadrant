# DocuSign Embedded Signing: In-App Signing Ceremony & Recipient Views

Embedded Signing allows users to sign documents directly within your web or mobile portal without switching to their email inbox.

## 1. How Embedded Signing Works

1. **Client User ID**: When defining a `Signer` in an envelope, assign a unique non-null `client_user_id` (e.g. your application's user ID). This instructs DocuSign to suppress email dispatch and wait for an in-app signing view request.
2. **Recipient View Request**: Your backend calls `EnvelopesApi.create_recipient_view` passing the envelope ID, recipient details, and a return URL.
3. **Short-Lived Signing URL**: DocuSign returns a secure URL (valid for 5 minutes).
4. **iFrame / Redirect**: The user is redirected to or embedded in an iframe with the signing URL.
5. **Return Redirect**: Upon signing or canceling, DocuSign redirects the user back to your `returnUrl` with event parameters.

---

## 2. Python Implementation: Generating the Recipient View

```python
from docusign_esign import EnvelopesApi, RecipientViewRequest

def generate_embedded_signing_url(
    envelopes_api: EnvelopesApi,
    account_id: str,
    envelope_id: str,
    signer_name: str,
    signer_email: str,
    client_user_id: str,
    return_url: str = "https://myapp.com/docusign/callback",
) -> str:
    """
    Generates a secure 5-minute embedded signing URL for an in-app signer.
    """
    view_request = RecipientViewRequest(
        authentication_method="Password",
        client_user_id=client_user_id,
        recipient_id="1",
        return_url=return_url,
        user_name=signer_name,
        email=signer_email,
    )

    results = envelopes_api.create_recipient_view(
        account_id=account_id,
        envelope_id=envelope_id,
        recipient_view_request=view_request,
    )

    return results.url
```

---

## 3. Handling Callback Events on Return URL

When DocuSign redirects back to `return_url`, it appends query parameter `event`:
- `event=signing_complete`: The recipient signed all required tabs.
- `event=decline`: The recipient clicked Decline to Sign.
- `event=cancel`: The recipient clicked Finish Later or canceled.
- `event=exception`: A session timeout or internal error occurred.

> **Security Note**: Never assume a document is legally executed based purely on query string parameters on the client. Always verify status via a secure **DocuSign Connect webhook** or backend REST query `envelopes_api.get_envelope(account_id, envelope_id)`.

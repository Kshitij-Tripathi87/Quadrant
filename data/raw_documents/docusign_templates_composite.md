# DocuSign Templates and Composite Templates

Templates eliminate repetitive document preparation by standardizing recipient roles, signing fields, and email settings. **Composite Templates** provide the advanced capability to merge dynamic documents with predefined server templates and overlay custom metadata fields.

## 1. Core Concepts: Server Templates vs Inline Templates

- **Server Template**: A template created and saved in the DocuSign web console with fixed tabs and role names (e.g., `Customer`, `Approver`).
- **Inline Template**: A transient template structure embedded directly in the REST payload to override or supplement template properties (e.g. pre-filling dynamic customer names, account numbers, contract values).
- **Composite Template**: The parent object that stitches together a Server Template, dynamic documents, and Inline Templates into a single seamless signing request.

---

## 2. Python Code: Creating an Envelope from a Template with Custom Fields

```python
from docusign_esign import (
    EnvelopesApi,
    EnvelopeDefinition,
    CompositeTemplate,
    ServerTemplate,
    InlineTemplate,
    Recipients,
    Signer,
    Tabs,
    Text,
)

def send_envelope_from_template(
    envelopes_api: EnvelopesApi,
    account_id: str,
    template_id: str,
    signer_name: str,
    signer_email: str,
    account_number: str,
) -> str:
    """
    Creates an envelope by referencing a Server Template and dynamically
    populating text fields (e.g., account number) via an Inline Template.
    """
    # 1. Reference the saved Server Template
    server_template = ServerTemplate(
        sequence="1",
        template_id=template_id,
    )

    # 2. Prefill dynamic tab data
    account_tab = Text(
        tab_label="AccountNumberField",
        value=account_number,
    )

    signer = Signer(
        email=signer_email,
        name=signer_name,
        role_name="Customer",  # Matches role name defined in the Template
        recipient_id="1",
        tabs=Tabs(text_tabs=[account_tab]),
    )

    # 3. Create Inline Template to bind the recipient to the Server Template role
    inline_template = InlineTemplate(
        sequence="2",
        recipients=Recipients(signers=[signer]),
    )

    # 4. Combine into Composite Template
    composite_template = CompositeTemplate(
        server_templates=[server_template],
        inline_templates=[inline_template],
    )

    envelope_definition = EnvelopeDefinition(
        status="sent",
        composite_templates=[composite_template],
    )

    results = envelopes_api.create_envelope(
        account_id=account_id,
        envelope_definition=envelope_definition,
    )
    return results.envelope_id
```

---

## 3. Best Practices for Template Management

- **Use Unique Tab Labels**: Assign semantic labels like `signer_ssn`, `monthly_rent` to enable easy programmatic population via `text_tabs`.
- **Role-Based Mapping**: Do not hardcode recipient emails into server templates; always map emails dynamically using `role_name`.

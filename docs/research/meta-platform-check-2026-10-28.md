# External research checkpoint — Meta / WhatsApp platform (2026-10-28)

## Status and boundaries

This is a source checkpoint for planning, not legal advice and not evidence that a Meta feature is enabled for a particular Algerian account. Official terms/policy documents are distinguished from secondary pricing reports and account-level hypotheses.

## Findings that changed the plan

### 1. Current Platform Terms are effective 2026-09-23

The official English [WhatsApp Terms for WhatsApp Business Platform](https://www.whatsapp.com/legal/WhatsApp-Terms-for-WhatsApp-Business-Platform?lang=en) page lists **Effective September 23, 2026**, incorporates the WhatsApp Business Messaging Policy and separate Meta Terms for WhatsApp Business Platform, places legal compliance and required business notices on the company, and describes WhatsApp's own Platform Services data processing with possible global transfers. See also the [official Business Messaging Policy](https://whatsappbusiness.com/policy/).

This means the older *WhatsApp Business Solution Terms* preview and the October 2025 report about a January 2026 AI Providers change must not be treated as the sole current contract. A secondary review reports the AI Providers clause/provider terminology changed in the September 2026 Meta Terms, but the full incorporated Meta Terms text still requires retrieval and counsel review: [Mesej review](https://mesej.io/guides/whatsapp-ai-providers-clause/). The legal impact on this architecture remains OPEN.

**Implementation decision:** keep hosted LLM processing, external customer-data sharing, contact profiling and conversation-derived training DENY by default. Keep message sends and third-party operations approval-gated. The current terms for the platform provider do not by themselves establish our own lawful basis for transferring a customer's data.

### 2. Meta Business Agent availability must be tested, not inferred from a launch headline

The [official WhatsApp Help Center setup guidance](https://faq.whatsapp.com/1153795669452207/?cms_platform=web) says the customer-facing Business App feature is available only to selected businesses in limited countries, is rolling out gradually, may not be available even for waitlisted businesses, and does not support all languages. That guidance is specifically for the WhatsApp Business App feature; it does not prove the separate Business Agent Platform API availability for an Algerian developer account.

**Implementation decision:** keep A-04 OPEN. Use the provider-neutral runtime and synthetic labelled Darja/Arabizi benchmark as the fallback. Enable any Meta Business Agent integration only after account UI/API eligibility is evidenced and the language quality test meets a predeclared threshold.

### 3. Algeria API message rates: useful secondary estimate, official account confirmation still needed

Three current secondary sources agree on the headline rates for a +213 recipient under Rest of Africa from 2026-10-01:

| Category | Reported USD per delivered message |
|---|---:|
| Marketing | $0.0225 |
| Utility | $0.0040 |
| Authentication | $0.0040 |
| Service (after the reported free allowance) | $0.0040 |

Sources: [Nonito — Algeria](https://www.nonito.io/whatsapp-business-api-pricing/algeria), [WhatsApp pricing change table](https://whautomate.com/whatsapp-pricing-updates), [Alibaba Cloud billing-change summary](https://www.alibabacloud.com/help/en/chatapp/whatsapp-message-rate-adjustments-and-service-conversation-message-billing). Secondary sources also report 1,000 free service messages per business phone number/month and that utility templates can be billable even within the 24-hour customer-service window. A provider source reports eligible CTWA entry points may open a free-entry window up to 7 days: [WATI pricing update](https://support.wati.io/en/articles/16954666-whatsapp-business-platform-api-pricing-changes-service-messages-and-click-to-message-ads).

**Evidence grade: SUPPORTED, not PROVEN from an official rate card.** The official [Meta pricing/rate-card page](https://developers.facebook.com/docs/whatsapp/pricing#rate-cards) could not be retrieved successfully in this review. Do not budget from an unqualified claim: confirm the official rate card and billing currency/recipient basis, provider surcharges, any relevant tier, the actual entry point and first invoice. Cost per order remains OPEN.

**Action in the repo:** C0 includes the secondary price estimate and explicit open evidence for official/current account-level billing. A-13 stays OPEN. V-01 now asks for official rate-card/account confirmation and per-order modelling.

### 4. Older billing pages are stale for the October 2026 change

The [historical billing mirror](https://support.chatarchitect.com/books/whatsapp-business-platform/page/about-billing-for-your-whatsapp-business-account) describes the pre-October 2026 pricing model. It is retained as historical documentation and must not be used to claim utility templates inside the 24-hour window are free after 2026-10-01.

## Open gates (not waived)

1. Retrieve and assess the exact current Meta Terms for WhatsApp Business Platform, including AI-provider/provider definitions; record counsel's written decision for A-05, A-08, A-09, A-10, A-11, A-12 and X1.
2. Verify the actual Algerian WABA, business verification, allowed API/feature access, payment method and billing currency.
3. Confirm the active rate card and initial invoice; calculate actual messaging cost per accepted order, including utility templates, eligible entry-point windows, service allowance, BSP/provider fees and failed/undelivered messages.
4. Run one signed test-number webhook delivery and one test message under approved test credentials; then prove ctwa_clid preservation on a real eligible CTWA flow before any CAPI test.
5. Require explicit policy and account approvals before any live outbound message, CAPI event, courier/PSP data transfer or hosted-model processing.

## Source integrity note

Reviewed on 2026-10-28 unless a prior date is stated in the generated documentation map. The official English Platform Terms page was directly opened and displays the September 23, 2026 effective date. Help Center Business Agent content was found in the official search result but did not render as a full page. Secondary pricing pages are cross-checks only; the official rate-card URL returned a retrieval error, and no real account or invoice was accessed.

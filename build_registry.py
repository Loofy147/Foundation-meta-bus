#!/usr/bin/env python3
"""
build_registry.py -- builds registry.json (single source of truth) from:
  1. artefact A's capability array (extracted from the compiled bundle -> A_data.json)
  2. re-assessments made on 2026-10-18 for the capabilities that were actually checked
  3. capabilities that neither artefact models but that the research surfaced
  4. artefact B's shapes / rows, expressed as dependency lists over capability ids

Evidence grades (the only four that exist):
  PROVEN        primary source retrieved (vendor docs / paper) or reproduced by script
  SUPPORTED     several independent secondary sources agree; primary not retrieved
  OPEN          unverified, single weak source, or sources conflict
  CONTRADICTED  evidence found against the artefact's claim

A capability that was not examined keeps A's label and is flagged checked=False.
Nothing is upgraded without an evidence entry.
"""
import json, sys, pathlib

HERE = pathlib.Path(__file__).parent
A = json.load(open(sys.argv[1] if len(sys.argv) > 1 else HERE / "A_data.json"))
GENERATED_ON = "2026-10-28"
VERIFIED_ON = "2026-10-18"

LAYER = {"A": "acquisition", "B": "conversation", "C": "creative",
         "D": "commerce", "E": "community", "F": "signal"}

# ---- sources actually retrieved in this study -------------------------------
S = {
 "meta_capi_bm": "https://developers.facebook.com/docs/marketing-api/conversions-api/business-messaging",
 "zernio_capi": "https://docs.zernio.com/whatsapp/send-whatsapp-conversion",
 "infobip_pay": "https://infobip.com/blog/whatsapp-payments",
 "sleekflow_pay": "https://sleekflow.io/en-gb/blog/whatsapp-pay",
 "pickyassist_pay": "https://pickyassist.com/blog/?p=9698",
 "ba_techwyse": "https://www.techwyse.com/news/platform-updates/meta-business-agent-global-launch-whatsapp-instagram",
 "ba_itdaily": "https://itdaily.com/news/software/meta-business-agent-available-worldwide/",
 "ba_fonearena": "https://www.fonearena.com/blog/484218/meta-business-agent-platform-features.html/amp",
 "offline_adadvisor": "https://adadvisor.ai/docs/learn/offline-conversions",
 "offline_devto": "https://dev.to/simul_sarker_51af2d373b1b/the-ghost-in-the-machine-why-your-offline-conversion-uploads-are-failing-and-what-to-do-about-it-b47",
 "adbilling_algtech": "https://algeriatech.news/?p=2915",
 "adbilling_grey": "https://grey.co/blog/acheter-en-ligne-algerie",
 "law_gide": "https://www.gide.com/en/news-insights/protection-of-personal-data-focus-on-algerian-regulations/",
 "law_algtech": "https://algeriatech.news/?p=21081",
 "yalidine_dzbuild": "https://dzbuild.com/docs/couriers/yalidine",
 "yalidine_wp": "https://wordpress.org/plugins/?p=347054",
 "couriers_unified": "https://freeship.dzbuild.com/",
 "slickpay_dzbuild": "https://dzbuild.com/docs/payments/cib-edahabia",
 "shops_help": "https://help.instagram.com/ipad-app/1627591223954487",
 "dziribert": "https://arxiv.org/abs/2109.12346v3",
 "dzair_hf": "https://huggingface.co/algerian-nlp/DZAIR",
 "artefact_A": "uploaded:dz_meta_foundation_blueprint.html",
 "artefact_B": "uploaded:meta_advanced_stack_algerian.html",
}
# Sources added by the 2026-10-24 documentation review. The source URLs are retained
# separately from claims so the evidence ledger remains reviewable.
# Keep artefact references last, matching the registry source-map ordering.
_ARTIFACT_SOURCES = {
 "artefact_A": "uploaded:dz_meta_foundation_blueprint.html",
 "artefact_B": "uploaded:meta_advanced_stack_algerian.html",
}
S.pop("artefact_A", None)
S.pop("artefact_B", None)
S.update(json.loads(r'''{
 "meta_webhook_text": "https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/messages/text",
 "hookdeck_wa": "https://hookdeck.com/webhooks/platforms/guide-to-whatsapp-webhooks-features-and-best-practices",
 "devto_wa_webhooks": "https://dev.to/wapgrowai_org/handling-whatsapp-cloud-api-webhooks-in-nodejs-signatures-retries-and-duplicate-events-4dci",
 "evolution_issue": "https://github.com/evolution-foundation/evolution-api/issues/2645",
 "whapi_ctwa": "https://whapi.cloud/blog/tr/track-click-to-whatsapp-ctwa-clid",
 "wa_solution_overview": "https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/overview/",
 "wa_tech_provider": "https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/get-started-for-tech-providers",
 "wa_embedded_overview": "https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/overview/",
 "wa_app_review": "https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/app-review",
 "wa_terms": "https://whatsapp.com/legal/business-solution-terms/preview?amp=&lang=en",
 "wa_policy": "https://business.whatsapp.com/policy",
 "wa_optin": "https://developers.facebook.com/documentation/business-messaging/whatsapp/getting-opt-in.md",
 "wa_webhooks_create": "https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/create-webhook-endpoint",
 "wa_webhooks_overview": "https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks",
 "wa_get_started": "https://developers.facebook.com/docs/whatsapp/cloud-api/get-started/",
 "mba_overview": "https://developers.facebook.com/documentation/meta-business-agent/overview",
 "wa_billing_help": "https://support.chatarchitect.com/books/whatsapp-business-platform/page/about-billing-for-your-whatsapp-business-account",
 "rate_card_2026": "https://www.salesforce.com/en-us/wp-content/uploads/sites/4/documents/PDF/WhatsApp-Business-Messaging-1000.pdf",
 "mba_price_sleek": "https://sleekflow.io/en-sg/blog/meta-business-agent-vs-ai-agents.md",
 "ai_terms_techcrunch": "https://techcrunch.com/2025/10/18/whatssapp-changes-its-terms-to-bar-general-purpose-chatbots-from-its-platform",
 "testnumber_pypi": "https://pypi.org/project/whatsappcloud/0.0.4",
 "wa_terms_current": "https://www.whatsapp.com/legal/WhatsApp-Terms-for-WhatsApp-Business-Platform?lang=en",
 "wa_business_agent_help": "https://faq.whatsapp.com/1153795669452207/?cms_platform=web",
 "wa_rate_algeria_nonito": "https://www.nonito.io/whatsapp-business-api-pricing/algeria",
 "wa_rate_oct2026": "https://whautomate.com/whatsapp-pricing-updates",
 "wa_rate_service_rules": "https://www.alibabacloud.com/help/en/chatapp/whatsapp-message-rate-adjustments-and-service-conversation-message-billing",
 "wa_rate_ctwa_rules": "https://support.wati.io/en/articles/16954666-whatsapp-business-platform-api-pricing-changes-service-messages-and-click-to-message-ads",
 "wa_ai_terms_current": "https://mesej.io/guides/whatsapp-ai-providers-clause/",
 "wa_pricing_official": "https://developers.facebook.com/docs/whatsapp/pricing#rate-cards"
}'''))
S.update(_ARTIFACT_SOURCES)

def ev(grade, claim, *srcs, note=""):
    return {"grade": grade, "claim": claim, "sources": [S[s] for s in srcs], "note": note}

# ---- re-assessments of A capabilities that were actually checked ------------
OVERRIDE = {
 "B2": dict(
    status="CONFIG",
    notes="A labelled this 'business_agent_beta'. Reported global launch 2026-06-03 plus a 'Business Agent Platform' for connecting external systems. "
          "Algeria-specific availability and Darja quality are NOT confirmed. Pricing: free to activate initially, paid tiers announced -> budget risk.",
    evidence=[
      ev("SUPPORTED", "Meta Business Agent announced as globally available (2026-06-03) on WhatsApp, Messenger, Instagram; handoff to human supported.", "ba_techwyse", "ba_itdaily", note="Several outlets repeating Meta/TechCrunch; Meta newsroom page itself not retrieved."),
      ev("SUPPORTED", "Business Agent Platform lets businesses link agents to external systems (e.g. Shopify, Zendesk).", "ba_itdaily", "ba_fonearena"),
      ev("SUPPORTED", "Free to activate initially; later bundled into WhatsApp Business Premium tiers, token-based pricing for large businesses.", "ba_techwyse", "ba_fonearena"),
      ev("OPEN", "Algeria eligibility and Darja/Arabizi quality: 'local languages' is the only statement found; no dialect-specific evidence.")],
    checked=True),
 "B4": dict(
    name="Darja NLU layer (provider-neutral)",
    status="CONFIG",
    meta_ref="NONE (not a Meta product) -- own router: encoder classifier + LLM API",
    desc="A framed this as 'Llama for Darja = BLOCKED'. The block is specific to a Meta-supplied fine-tune; Algerian-dialect NLP assets exist outside Meta. Re-scoped as a routable NLU capability to be benchmarked, not assumed.",
    notes="Accuracy on our intents is OPEN until benchmarked on our own labelled conversations. This sandbox cannot reach Hugging Face, so no model was executed in this study.",
    evidence=[
      ev("PROVEN", "DziriBERT: peer-reviewed pretrained model for Algerian dialect, outperforming multilingual baselines on classification, esp. Roman script.", "dziribert"),
      ev("SUPPORTED", "Newer encoders for Darja/Arabizi/French code-switching exist (DZAIR).", "dzair_hf", note="Model card claims; not independently reproduced."),
      ev("OPEN", "No evidence on how general-purpose LLMs perform on Algerian Darja intent parsing for our domain.")],
    checked=True),
 "D4": dict(
    status="BLOCKED",
    notes="Native in-chat payments reported only for India, Brazil, Singapore (one source adds Mexico). Algeria not listed; no cross-border P2P. Payment must run on external rails (see P2) or COD.",
    evidence=[
      ev("SUPPORTED", "Native WhatsApp in-chat payments: India, Brazil, Singapore only; experience varies by market and partner.", "infobip_pay", "sleekflow_pay", "pickyassist_pay", note="All secondary; Meta help-centre list not retrieved."),
      ev("SUPPORTED", "WhatsApp does not support cross-border P2P transfers.", "pickyassist_pay")],
    checked=True),
 "E5": dict(
    status="UNVERIFIED",
    notes="A says READY. Meta's own help page makes a supported-country Page a requirement; no list found that includes Algeria. Treat as unavailable until confirmed in Commerce Manager for the actual Page.",
    evidence=[
      ev("PROVEN", "Facebook/Instagram commerce surfaces require the Page/account to be located in a supported country; native checkout was US-only on that page.", "shops_help", note="Page is older than 2026; re-check current list."),
      ev("OPEN", "Algeria's presence/absence in the current supported-country list was not confirmed either way.")],
    checked=True),
 "F1": dict(
    status="CONFIG",
    notes="For click-to-WhatsApp, attribution key is ctwa_clid delivered on the FIRST inbound message. If it is not persisted at that moment it is lost. Event set reported: LeadSubmitted (not Lead), Purchase, AddToCart, InitiateCheckout, ViewContent; action_source=business_messaging. Reported 7-day attribution window.",
    evidence=[
      ev("PROVEN", "CAPI for Business Messaging exists; needs dataset + WABA id + ctwa_clid; ctwa_clid is per-click and exposed when the user arrives from a CTWA ad.", "meta_capi_bm"),
      ev("SUPPORTED", "Accepted event names and the 7-day attribution caveat.", "zernio_capi", note="Third-party API docs claiming live verification against Graph v25.0.")],
    checked=True),
 "F2": dict(
    status="CONFIG",
    notes="A's '+15-25% match lift' is unsourced and describes the web Pixel/CAPI path. The messaging path attributes by ctwa_clid, so hashing PII adds little there and creates transfer exposure (see K1).",
    evidence=[
      ev("PROVEN", "Messaging-path attribution is keyed on ctwa_clid.", "meta_capi_bm"),
      ev("OPEN", "'+15-25%' lift: no source in the artefact, none found.")],
    checked=True),
 "F3": dict(
    name="Delivery-outcome -> CAPI purchase pipeline",
    status="CONFIG",
    meta_ref="CAPI business_messaging / system_generated (replaces offline_dataset)",
    desc="A's 'Offline Conversions' product was discontinued May 2025; offline events now go through the unified Conversions API. Re-scoped: courier delivery/COD-collected status -> Purchase event carrying the original ctwa_clid.",
    notes="Feasibility of the API leg is documented; whether Meta optimisation benefits from late (post-delivery) COD signals is OPEN. Window limits: post-delivery events may exceed the reported 7-day attribution window -> measure lag from our own data.",
    evidence=[
      ev("SUPPORTED", "Offline Conversions API discontinued May 2025; replaced by Conversions API (action_source physical_store / system_generated).", "offline_adadvisor", "offline_devto"),
      ev("PROVEN", "CAPI business-messaging Purchase event with ctwa_clid is the supported path for chat-originated sales.", "meta_capi_bm"),
      ev("OPEN", "Optimisation uplift from COD-delivered purchase signals; courier-lag vs attribution window.")],
    checked=True),
}

# ---- capabilities neither artefact models, surfaced by the research ---------
NEW = [
 dict(id="P1", name="Ad billing instrument", layer="payments", artefact_origin="new", status="CONFIG", checked=True,
      desc="A payment method Meta Ads Manager will accept for an Algerian advertiser.",
      notes="Algerian CIB/Edahabia cards are reported as generally rejected for Meta billing; virtual USD cards are the common workaround. FX/regulatory treatment of paying a foreign platform is OPEN -> counsel/bank.",
      depends_on=[],
      evidence=[ev("SUPPORTED", "CIB/Edahabia cards generally rejected by Meta/Google/TikTok billing; convertible-currency cards required.", "adbilling_algtech", "adbilling_grey", note="Trade site + a virtual-card vendor (commercial interest)."),
                ev("OPEN", "Legal/FX position on funding a foreign ad account from Algeria.")]),
 dict(id="P2", name="Local payment rails (CIB/Edahabia via PSP link)", layer="payments", artefact_origin="new", status="CONFIG", checked=True,
      desc="External checkout for DOMESTIC cards (SlickPay-class PSPs, SATIM network) triggered from chat as a link; COD remains default. Serves Algerian cardholders only -- NOT a replacement for diaspora payments (see P3).",
      notes="Vendor doc claims ~30-50% lower conversion than COD-only on cold traffic -- single commercial source, treat as hypothesis to measure.",
      depends_on=[],
      evidence=[ev("SUPPORTED", "PSP gateways for CIB/Edahabia exist with API credentials and webhooks.", "slickpay_dzbuild"),
                ev("OPEN", "Conversion trade-off vs COD.")]),
 dict(id="L1", name="Courier adapter layer", layer="logistics", artefact_origin="new", status="CONFIG", checked=True,
      desc="Provider-neutral shipping port: fees by wilaya/commune, parcel create, status, return fee. Adapters: Yalidine family (API ID+token), Ecotrack family, Maystro, ZR Express (UUID territories), Noest.",
      notes="Yalidine API needs a verified business account; commune name mismatch (Arabic vs French spelling) is a known create-time failure. Couriers differ in COD semantics (Yalidine bills delivery fee separately).",
      depends_on=[],
      evidence=[ev("SUPPORTED", "Yalidine Express API (api.yalidine.app/v1): localities, fees, parcel creation, stop-desks; access via API ID+token.", "yalidine_dzbuild", "yalidine_wp"),
                ev("SUPPORTED", "Many Algerian courier APIs are inconsistent or undocumented; unified wrappers exist.", "couriers_unified", note="Vendor of such a wrapper.")]),
 dict(id="K1", name="Data-transfer & residency gate", layer="compliance", artefact_origin="new", status="CONFIG", checked=True,
      desc="Design-time and run-time check that personal data only reaches providers/regions permitted by a policy table owned by counsel.",
      notes="Law 18-07 as amended by Law 25-11 (2025): express consent; transfers abroad subject to ANPDP rules/authorization. Trade sources disagree on specifics (default local hosting, processing times) -> OPEN; needs Algerian counsel. This is a gate in the architecture, not a legal conclusion.",
      depends_on=[],
      evidence=[ev("SUPPORTED", "Law 18-07 (amended by 25-11, July 2025): consent principle; cross-border transfers regulated and tied to ANPDP authorization.", "law_gide", note="Law-firm summary; statute text not retrieved."),
                ev("OPEN", "Local-hosting default and authorization timelines (single trade-site claims, conflicting wording).", "law_algtech")]),
 dict(id="K2", name="Consent & purpose ledger", layer="compliance", artefact_origin="new", status="CONFIG", checked=True,
      desc="Per-contact record of consent, purpose and channel, consulted before any outbound event (CAPI, courier, LLM).",
      notes="Follows from the consent principle; implementation is ours.", depends_on=["K1"],
      evidence=[ev("SUPPORTED", "Express prior consent is the core principle of the Algerian regime.", "law_gide")]),
 dict(id="S1", name="Canonical event backbone", layer="signal", artefact_origin="new", status="CONFIG", checked=True,
      desc="Provider-neutral event model (conversation_started[ctwa_clid], lead_qualified, order_created, confirmed, shipped, delivered, returned, paid). CAPI/analytics/CRM are subscribers.",
      notes="Invariant: persist ctwa_clid at the first inbound webhook, idempotently. Everything in the signal layer depends on this.",
      depends_on=["K2"],
      evidence=[ev("PROVEN", "ctwa_clid is delivered with the first inbound message and is required for attribution.", "meta_capi_bm")]),

 dict(id="P3", name="Cross-border collection rail", layer="payments", artefact_origin="new", status="UNVERIFIED", checked=False,
      desc="Accepting payment from buyers abroad (e.g. diaspora with EU cards) and settling to an Algerian business. Needed by artefact B's Diaspora Bridge once native WhatsApp payments (D4) are ruled out.",
      notes="NOT examined. Settlement, FX and foreign-currency regulation for an Algerian merchant are OPEN and potentially restrictive; may require a foreign merchant-of-record structure. Counsel/bank question before any design work.",
      depends_on=["K1"],
      evidence=[ev("OPEN", "No source examined for foreign-card acceptance and settlement into Algeria.", "artefact_B")]),
 dict(id="D6", name="Order confirmation / OTP step", layer="commerce", artefact_origin="B", status="CONFIG", checked=False,
      desc="B's 'OTP confirm' inside the COD flow. Not examined: which Meta/BSP feature provides it and its per-message cost in Algeria are unknown.",
      notes="Inherited from B, unverified.", depends_on=[],
      evidence=[ev("OPEN", "Mechanism, availability and cost not examined.", "artefact_B")]),
]

# Reconciliation from the 2026-10-28 Dropbox snapshot:
# The ZIP contains generated registry records but omits their original authoring block.
# These six records and five record revisions are therefore retained here as explicit
# source definitions (with provenance in their evidence entries), not patched into output JSON.
REVISED_FIELDS = json.loads(r'''{
 "B2": {
  "notes": "Primary overview read 2026-10-24: acts as primary responder, managed through Business Agent Platform APIs, can call our own APIs and subscribe to webhooks, excluded for Finance, Government, Health, Alcohol, Gambling, OTC drugs and matrimony, and requires the business to be based in a country authorized for it. Priced separately from other messages (reported US$2.00 per million tokens since 2026-08-01, secondary). Algeria authorization and Darja quality are NOT confirmed.",
  "evidence": [
   {
    "grade": "PROVEN",
    "claim": "Business Agent acts as the primary responder on WhatsApp, is managed through the Business Agent Platform APIs, can connect our own APIs and webhooks, and hands off to our app.",
    "sources": [
     "https://developers.facebook.com/documentation/meta-business-agent/overview"
    ],
    "note": ""
   },
   {
    "grade": "PROVEN",
    "claim": "Excluded verticals; the business must be based in a country authorized for Meta Business Agent; the phone number must be eligible.",
    "sources": [
     "https://developers.facebook.com/documentation/meta-business-agent/overview"
    ],
    "note": ""
   },
   {
    "grade": "SUPPORTED",
    "claim": "Announced as globally available (2026-06-03) on WhatsApp, Messenger and Instagram.",
    "sources": [
     "https://www.techwyse.com/news/platform-updates/meta-business-agent-global-launch-whatsapp-instagram",
     "https://itdaily.com/news/software/meta-business-agent-available-worldwide/"
    ],
    "note": ""
   },
   {
    "grade": "SUPPORTED",
    "claim": "Priced per token for non-template messages (reported US$2.00 per million tokens from 2026-08-01).",
    "sources": [
     "https://sleekflow.io/en-sg/blog/meta-business-agent-vs-ai-agents.md",
     "https://www.techwyse.com/news/platform-updates/meta-business-agent-global-launch-whatsapp-instagram"
    ],
    "note": ""
   },
   {
    "grade": "OPEN",
    "claim": "Whether Algeria is an authorized country: the press says global, the overview requires an authorized country.",
    "sources": [
     "https://developers.facebook.com/documentation/meta-business-agent/overview"
    ],
    "note": ""
   },
   {
    "grade": "OPEN",
    "claim": "Darja/Arabizi quality: 'local languages' is the only statement found.",
    "sources": [],
    "note": ""
   }
  ],
  "verified_on": "2026-10-24"
 },
 "B4": {
  "notes": "Accuracy on our intents is OPEN until benchmarked. This sandbox cannot reach Hugging Face, so no model was executed. CONSTRAINT (see X1): WhatsApp Business Solution Data may not be used to train or improve AI models, except fine-tuning a model for our exclusive use; datasets derived from WhatsApp conversations may not be shared, and a vendor may not train on them."
 },
 "F1": {
  "notes": "Primary source read in full 2026-10-18. Attribution key is ctwa_clid (a personal identifier, unique PER CLICK) from the messages-webhook referral object; store it with the conversation. Meta does not deduplicate these events: the sender must. The guide is addressed to Business Messaging Partners, but the App Review page says direct developers need no Advanced access for their own assets; explicit confirmation for this endpoint needs a test event.",
  "evidence": [
   {
    "grade": "PROVEN",
    "claim": "Endpoint POST /{dataset_id}/events (Graph v26.0 in the page); event carries event_name, event_time, action_source=business_messaging, messaging_channel=whatsapp, user_data{whatsapp_business_account_id, ctwa_clid}, custom_data{currency,value}, partner_agent.",
    "sources": [
     "https://developers.facebook.com/docs/marketing-api/conversions-api/business-messaging"
    ],
    "note": ""
   },
   {
    "grade": "PROVEN",
    "claim": "ctwa_clid is a personal identifier, unique per click, exposed in the messages-webhook referral object; store it with the conversation and send the corresponding clid when a conversion happens.",
    "sources": [
     "https://developers.facebook.com/docs/marketing-api/conversions-api/business-messaging"
    ],
    "note": ""
   },
   {
    "grade": "PROVEN",
    "claim": "ctwa_clid is omitted entirely for messages from WhatsApp Status ad placements (referral present, no clid).",
    "sources": [
     "https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/reference/messages/text"
    ],
    "note": ""
   },
   {
    "grade": "PROVEN",
    "claim": "Supported messaging event names: Purchase, LeadSubmitted, InitiateCheckout, AddToCart, ViewContent, OrderCreated, OrderShipped, OrderDelivered, OrderCanceled, OrderReturned, CartAbandoned, QualifiedLead, RatingProvided, ReviewProvided.",
    "sources": [
     "https://developers.facebook.com/docs/marketing-api/conversions-api/business-messaging"
    ],
    "note": ""
   },
   {
    "grade": "PROVEN",
    "claim": "Meta does not assist with deduplication for CAPI business messaging; senders should deduplicate first.",
    "sources": [
     "https://developers.facebook.com/docs/marketing-api/conversions-api/business-messaging"
    ],
    "note": ""
   },
   {
    "grade": "PROVEN",
    "claim": "The 7-day attribution limit and the 'subset of countries' limit are stated for the hashed-customer-info path; the ctwa_clid path is stated as not subject to them. (Corrects an earlier note taken from a third-party doc.)",
    "sources": [
     "https://developers.facebook.com/docs/marketing-api/conversions-api/business-messaging"
    ],
    "note": ""
   },
   {
    "grade": "PROVEN",
    "claim": "Business apps get Standard Access automatically; a direct developer using only its own business assets needs neither Advanced access nor App Review. Advanced access is for apps used by other businesses.",
    "sources": [
     "https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/app-review"
    ],
    "note": ""
   },
   {
    "grade": "PROVEN",
    "claim": "Meta serves two versions of the CAPI-BM guide: an older one (Graph v16.0 samples, partner-addressed, 1,500-call Ads Management Standard Access prerequisite) at /docs/marketing-api/... and a newer one (v26.0, hashed fallback) at /documentation/ads-commerce/... Cite the final URL and fetch date.",
    "sources": [
     "https://developers.facebook.com/docs/marketing-api/conversions-api/business-messaging"
    ],
    "note": ""
   },
   {
    "grade": "OPEN",
    "claim": "Neither version states that a direct advertiser can send CAPI-BM events under Standard Access for its own WABA and dataset; that follows from the App Review page and needs a test event visible in Events Manager.",
    "sources": [],
    "note": ""
   },
   {
    "grade": "OPEN",
    "claim": "Whether Meta accepts DZD as custom_data.currency, or requires conversion.",
    "sources": [],
    "note": ""
   }
  ],
  "verified_on": "2026-10-24"
 },
 "F2": {
  "notes": "A's '+15-25% match lift' is unsourced. In business messaging there are two routes: ctwa_clid (direct, preferred) and hashed customer info (em, ph, fn, ln, ct, st, zp, country, ge, db; needs page_id; external_id is not used). The hashed route is the fallback for conversations without a clid; it is limited to 7-day attribution and a subset of countries, and it sends hashed PII abroad (see K1).",
  "evidence": [
   {
    "grade": "PROVEN",
    "claim": "Hashed-customer-info fallback exists for business messaging: needs page_id and at least one customer parameter, SHA-256 normalised; attribution limited to the past 7 days; available in a subset of countries.",
    "sources": [
     "https://developers.facebook.com/docs/marketing-api/conversions-api/business-messaging"
    ],
    "note": ""
   },
   {
    "grade": "OPEN",
    "claim": "Whether Algeria is in the 'subset of countries' for the hashed path.",
    "sources": [],
    "note": ""
   },
   {
    "grade": "OPEN",
    "claim": "'+15-25%' lift: no source in the artefact, none found.",
    "sources": [],
    "note": ""
   }
  ]
 },
 "F3": {
  "name": "Delivery-outcome -> CAPI pipeline",
  "meta_ref": "CAPI business_messaging (replaces offline_dataset)",
  "desc": "A's 'Offline Conversions' product was discontinued May 2025; events now go through the unified Conversions API. Re-scoped: courier status (delivered, returned, cancelled) -> messaging events carrying the stored ctwa_clid.",
  "notes": "Lifecycle events OrderCreated/OrderShipped/OrderDelivered/OrderCanceled/OrderReturned exist beside Purchase, and purchase optimisation is available for ads that click to WhatsApp (both PROVEN). Whether lifecycle events influence optimisation is OPEN. The clid path is documented as not subject to the 7-day limit, so courier lag is not documented to cause non-attribution; measure it anyway. Which event marks a COD 'purchase' (confirmed vs delivered) is an experiment, not a fact.",
  "evidence": [
   {
    "grade": "SUPPORTED",
    "claim": "Offline Conversions API discontinued May 2025; replaced by Conversions API.",
    "sources": [
     "https://adadvisor.ai/docs/learn/offline-conversions",
     "https://dev.to/simul_sarker_51af2d373b1b/the-ghost-in-the-machine-why-your-offline-conversion-uploads-are-failing-and-what-to-do-about-it-b47"
    ],
    "note": ""
   },
   {
    "grade": "PROVEN",
    "claim": "Messaging lifecycle event names exist (OrderCreated, OrderShipped, OrderDelivered, OrderCanceled, OrderReturned) in addition to Purchase.",
    "sources": [
     "https://developers.facebook.com/docs/marketing-api/conversions-api/business-messaging"
    ],
    "note": ""
   },
   {
    "grade": "PROVEN",
    "claim": "Conversions API enables purchase optimisation for ads that click to WhatsApp (and Messenger), not Instagram.",
    "sources": [
     "https://developers.facebook.com/docs/marketing-api/conversions-api/business-messaging"
    ],
    "note": ""
   },
   {
    "grade": "OPEN",
    "claim": "Optimisation uplift from late COD-delivered signals; effect of lifecycle events on optimisation.",
    "sources": [],
    "note": ""
   }
  ]
 }
}''')
EXTENDED_CAPABILITIES = json.loads(r'''[
 {
  "id": "M1",
  "name": "WhatsApp messaging channel (Cloud API or BSP)",
  "layer": "conversation",
  "artefact_origin": "A-checklist",
  "status": "CONFIG",
  "checked": false,
  "desc": "The WhatsApp Business API account itself: send/receive, templates, webhooks. Listed in A's identity checklist under 'Assets Matrix' (IN_PROGRESS) but absent from A's capability array; every messaging operation depends on it.",
  "notes": "Onboarding, availability for an Algerian business and BSP-versus-direct are NOT examined (hence checked=False). Webhook behaviour is PROVEN from Meta documentation; wrappers can strip the referral, so clid propagation must be tested per provider. One endpoint per app means separate apps per environment.",
  "depends_on": [
   "K2"
  ],
  "verified_on": "2026-10-24",
  "evidence": [
   {
    "grade": "PROVEN",
    "claim": "GET handshake must answer 200 with hub.challenge; POSTs carry X-Hub-Signature-256 (sha256 of the payload, compared after the prefix); non-200 deliveries are retried with decreasing frequency for up to 7 days; payloads up to 3 MB; one webhook endpoint per Meta app; unsupported message types arrive as an unknown-message webhook; mTLS is supported.",
    "sources": [
     "https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/create-webhook-endpoint",
     "https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks"
    ],
    "note": ""
   },
   {
    "grade": "SUPPORTED",
    "claim": "Signature is HMAC-SHA256 keyed with the app secret over the raw body; the scheme has no timestamp, so replays validate forever; wamid is the per-message id.",
    "sources": [
     "https://hookdeck.com/webhooks/platforms/guide-to-whatsapp-webhooks-features-and-best-practices",
     "https://dev.to/wapgrowai_org/handling-whatsapp-cloud-api-webhooks-in-nodejs-signatures-retries-and-duplicate-events-4dci"
    ],
    "note": ""
   },
   {
    "grade": "SUPPORTED",
    "claim": "Some wrappers and BSP layers drop or relocate the referral object (an unofficial API dropped it entirely; another vendor exposes the clid at context.ad.ctwa), so clid propagation must be tested per provider.",
    "sources": [
     "https://github.com/evolution-foundation/evolution-api/issues/2645",
     "https://whapi.cloud/blog/tr/track-click-to-whatsapp-ctwa-clid"
    ],
    "note": ""
   },
   {
    "grade": "OPEN",
    "claim": "Channel availability, onboarding requirements and BSP choice for an Algerian business not examined.",
    "sources": [
     "uploaded:dz_meta_foundation_blueprint.html"
    ],
    "note": ""
   }
  ]
 },
 {
  "id": "T1",
  "name": "Cloud API test environment (test WABA and test number)",
  "layer": "conversation",
  "artefact_origin": "new",
  "status": "CONFIG",
  "checked": true,
  "desc": "The developer-app test setup: Meta creates a test WhatsApp Business Account and a test business number that can message up to 5 verified recipient numbers.",
  "notes": "Lets webhook delivery, signatures, message flow and status webhooks be tested without a business WhatsApp account. It cannot receive click-to-WhatsApp referrals (no ad), so ctwa_clid and CAPI stay untestable. Test-account tokens reportedly expire daily (secondary). Needs a Meta developer account, a public HTTPS endpoint and personal phone numbers as recipients.",
  "depends_on": [],
  "verified_on": "2026-10-24",
  "evidence": [
   {
    "grade": "PROVEN",
    "claim": "Cloud API setup creates a test WABA and a test business number; free messages to up to 5 recipient numbers, each verified by a code.",
    "sources": [
     "https://developers.facebook.com/docs/whatsapp/cloud-api/get-started/"
    ],
    "note": ""
   },
   {
    "grade": "SUPPORTED",
    "claim": "Test business account tokens expire every 24 hours.",
    "sources": [
     "https://pypi.org/project/whatsappcloud/0.0.4"
    ],
    "note": ""
   },
   {
    "grade": "OPEN",
    "claim": "Whether a developer account in Algeria needs a business portfolio or verification just to reach the test setup.",
    "sources": [],
    "note": ""
   }
  ]
 },
 {
  "id": "C0",
  "name": "Messaging cost model",
  "layer": "commerce",
  "artefact_origin": "new",
  "status": "CONFIG",
  "checked": true,
  "desc": "Per-delivered-message billing. Current secondary sources list Algeria (+213) under Rest of Africa from 2026-10-01 at USD 0.0225 per marketing message and USD 0.0040 per utility, authentication and service message. Secondary sources also report 1,000 free service messages per business phone number/month and an eligible free Click-to-WhatsApp entry-point window up to 7 days.",
  "notes": "Use the rates only as a planning estimate until the official Meta rate card and the chosen account's first invoice are checked. Utility templates can be billable inside the 24-hour customer-service window from 2026-10-01. Do not confuse the 24-hour service window with a free entry-point window; eligibility and duration depend on the source/entry point and require account confirmation. Add provider fees, taxes and actual billing currency before committing spend.",
  "depends_on": [],
  "verified_on": "2026-10-28",
  "evidence": [
   {
    "grade": "SUPPORTED",
    "claim": "Secondary pricing pages list +213 under Rest of Africa from 2026-10-01 at USD 0.0225 per delivered marketing message and USD 0.0040 per delivered utility, authentication or service message.",
    "sources": [
     "https://www.nonito.io/whatsapp-business-api-pricing/algeria",
     "https://whautomate.com/whatsapp-pricing-updates"
    ],
    "note": "Independent secondary cross-check; official Meta rate card did not load successfully during the 2026-10-28 review."
   },
   {
    "grade": "SUPPORTED",
    "claim": "Secondary provider documentation reports 1,000 free service messages per business phone number/month and billable utility templates inside the 24-hour service window from 2026-10-01; eligible CTWA entry points may have a free-entry window up to 7 days.",
    "sources": [
     "https://www.alibabacloud.com/help/en/chatapp/whatsapp-message-rate-adjustments-and-service-conversation-message-billing",
     "https://support.wati.io/en/articles/16954666-whatsapp-business-platform-api-pricing-changes-service-messages-and-click-to-message-ads",
     "https://www.nonito.io/whatsapp-business-api-pricing/algeria"
    ],
    "note": "Not an account-level test. Verify the exact Meta entry point, billing currency, service allowance and selected provider's additional fees."
   },
   {
    "grade": "OPEN",
    "claim": "Official current Meta rate card, exact account billing, provider surcharges/taxes, eligible free-entry windows, and realized cost per order.",
    "sources": [
     "https://developers.facebook.com/docs/whatsapp/pricing#rate-cards"
    ],
    "note": "Official pricing URL was attempted but its content could not be retrieved in this run; a current billing account/invoice has not been examined."
   }
  ]
 },
 {
  "id": "X1",
  "name": "WhatsApp Business Solution Terms constraints",
  "layer": "compliance",
  "artefact_origin": "new",
  "status": "CONFIG",
  "checked": true,
  "desc": "Contract constraints on how Business Solution Data may be used, independent of Algerian law.",
  "notes": "The earlier Business Solution Terms snapshot describes restrictions on training on Business Solution Data, external sharing and contact profiling, and historical reporting described an AI Providers clause. Current legal structure must not be inferred from the old snapshot alone: official WhatsApp Terms for WhatsApp Business Platform are effective 2026-09-23 and incorporate separate Meta Terms for WhatsApp Business Platform. A secondary review reports the AI-provider rule/provider terminology changed in the current text, but the full incorporated Meta Terms and its exact current definitions must be verified. Keep hosted LLM, external customer-data sharing, cross-message profiling and conversation-training operations disabled; counsel must decide whether our intended use and each vendor are permitted.",
  "depends_on": [
   "K1"
  ],
  "verified_on": "2026-10-28",
  "evidence": [
   {
    "grade": "SUPPORTED",
    "claim": "A prior official Business Solution Terms preview stated restrictions on use of business data for model training, third-party sharing and user-profile building; applicability of this earlier language to the full post-2026-09-23 contract set needs re-verification.",
    "sources": [
     "https://whatsapp.com/legal/business-solution-terms/preview?amp=&lang=en"
    ],
    "note": "Historical terms snapshot. Do not treat the old terminology as confirmed current wording."
   },
   {
    "grade": "PROVEN",
    "claim": "Official WhatsApp Terms for WhatsApp Business Platform state an effective date of 2026-09-23 and incorporate separate Meta Terms for WhatsApp Business Platform and the current Business Messaging Policy.",
    "sources": [
     "https://www.whatsapp.com/legal/WhatsApp-Terms-for-WhatsApp-Business-Platform?lang=en",
     "https://whatsappbusiness.com/policy/"
    ],
    "note": "Official English page retrieved. This proves the current terms architecture/date, not the exact contents of the incorporated Meta Terms."
   },
   {
    "grade": "SUPPORTED",
    "claim": "A current secondary legal review reports the AI Providers clause is located in the Meta Terms for WhatsApp Business Platform and discusses a change from Third Party Service Provider to Solution Provider terminology.",
    "sources": [
     "https://mesej.io/guides/whatsapp-ai-providers-clause/"
    ],
    "note": "Secondary interpretation only; retrieve and review the actual incorporated Meta Terms and obtain counsel's written applicability assessment."
   },
   {
    "grade": "OPEN",
    "claim": "Current exact legal text/definitions and whether our runtime, couriers, payment PSP, or LLM vendor are permitted in this architecture; lawful processing and transfer basis under Algerian law.",
    "sources": [
     "https://www.whatsapp.com/legal/WhatsApp-Terms-for-WhatsApp-Business-Platform?lang=en",
     "https://mesej.io/guides/whatsapp-ai-providers-clause/"
    ],
    "note": "Do not enable external data sharing, hosted LLMs or training until current contract text, country/account status and counsel decisions are recorded."
   }
  ]
 },
 {
  "id": "O1",
  "name": "Messaging policy and opt-in",
  "layer": "compliance",
  "artefact_origin": "new",
  "status": "CONFIG",
  "checked": true,
  "desc": "Opt-in is required before messaging; it may be general rather than WhatsApp-specific if local law is met; opt-in should be separable by message category; opt-outs must be honoured; businesses must secure all notices and consents and keep a published privacy policy; commerce experiences must follow the Commerce Policy.",
  "notes": "Meta may change the policy without notice, so registry entries about policy need a re-verification cycle. Whether a user-initiated click-to-WhatsApp conversation satisfies opt-in for service replies and utility updates is OPEN.",
  "depends_on": [
   "K2"
  ],
  "verified_on": "2026-10-24",
  "evidence": [
   {
    "grade": "PROVEN",
    "claim": "Opt-in required (may be general, per local law), recommended per category; opt-out must be honoured; user may stop marketing messages; businesses secure consents and publish a privacy policy; Commerce Policy governs catalogues and commerce; policy may change without notice.",
    "sources": [
     "https://business.whatsapp.com/policy",
     "https://developers.facebook.com/documentation/business-messaging/whatsapp/getting-opt-in.md"
    ],
    "note": ""
   },
   {
    "grade": "OPEN",
    "claim": "Sufficiency of a user-initiated conversation as opt-in for utility updates outside the 24-hour window.",
    "sources": [],
    "note": ""
   }
  ]
 },
 {
  "id": "TP1",
  "name": "Tech Provider multi-tenant onboarding",
  "layer": "conversation",
  "artefact_origin": "new",
  "status": "CONFIG",
  "checked": true,
  "desc": "Only if the system will onboard other businesses: Tech Provider status requires business verification and Advanced access through App Review, Embedded Signup (v2 was deprecated 2026-10-15; v4 required), business tokens, and each customer attaches a payment method unless a Solution Partner extends credit.",
  "notes": "Not needed while we operate only our own business assets as a direct developer. A multi-merchant product would also draw scrutiny under the AI Providers clause (see X1).",
  "depends_on": [
   "X1",
   "O1"
  ],
  "verified_on": "2026-10-24",
  "evidence": [
   {
    "grade": "PROVEN",
    "claim": "Partner types and requirements; Tech Provider needs business verification and Advanced access; Embedded Signup mandatory unless partnered with a Solution Partner; business tokens; customers add a payment method unless a Solution Partner shares credit; Embedded Signup v2 deprecation on 2026-10-15.",
    "sources": [
     "https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/overview/",
     "https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/get-started-for-tech-providers",
     "https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/overview/"
    ],
    "note": ""
   },
   {
    "grade": "OPEN",
    "claim": "Eligibility and timeline for an Algerian entity.",
    "sources": [],
    "note": ""
   }
  ]
 }
]''')

# ---- dependencies between capabilities (design judgement, auditable) ---------
DEPS = {
 "F1": ["S1", "K2"], "F2": ["K1"], "F3": ["S1", "L1", "K2"],
 "B2": ["K2"], "B4": ["K1"], "D2": ["L1"], "D5": ["K2"],
 "A1": ["D3", "F1"], "D1": ["F1"], "A3": ["F1"],
 "C4": [], "B1": [], "D3": ["F4"],
}

# ---- B's shapes and rows as dependency lists --------------------------------
SHAPES = [
 {"id": "A", "title": "Darja AI Sales Factory", "source": "B",
  "requires": ["B2", "B4", "A1", "D3", "D2", "C2", "D1", "L1", "F1", "D6", "P1"],
  "workarounds": {}},
 {"id": "B", "title": "Community-to-Cash Flywheel", "source": "B",
  "requires": ["E3", "E2", "B2", "A2", "F5", "F1", "P1"],
  "workarounds": {}},
 {"id": "C", "title": "Diaspora Bridge", "source": "B",
  "requires": ["C4", "D4", "A3", "L1", "P1"],
  "workarounds": {"D4": "P3"}},
]
ROWS = [
 {"id": "R1", "title": "Boost post -> Advantage+ incl. Threads + WA as conversion", "requires": ["A3", "D1", "F1", "P1"]},
 {"id": "R2", "title": "Night replies -> AI Business Agent 24/7", "requires": ["B2", "B4"]},
 {"id": "R3", "title": "Product photo -> generative video", "requires": ["C1", "C2", "C4"]},
 {"id": "R4", "title": "COD chaos -> Flow with wilaya + live courier estimate + OTP", "requires": ["D2", "L1", "D6"]},
]

# ---- assemble ---------------------------------------------------------------
caps = []
for g in A["Tl"]:
    for c in g["capabilities"]:
        # An inherited READY label without verification is not an effective readiness claim.
        effective_status = "UNVERIFIED" if c["status"] == "READY" else c["status"]
        inherited_notes = ("Original READY label downgraded to UNVERIFIED pending independent evidence."
                           if c["status"] == "READY" else "Inherited from artefact A; not examined in this study.")
        rec = {"id": c["id"], "name": c["name"], "code": c["code"], "layer": LAYER[g["id"]],
               "group": g["id"], "artefact_origin": "A", "a_status": c["status"], "status": effective_status,
               "complexity": c["complexity"], "meta_ref": c["meta_ref"], "desc": c["desc"],
               "checked": False, "notes": inherited_notes,
               "depends_on": DEPS.get(c["id"], []),
               "evidence": [ev("OPEN", "Taken from artefact A without independent verification.", "artefact_A")],
               "verified_on": None}
        if c["id"] in OVERRIDE:
            rec.update(OVERRIDE[c["id"]]); rec["verified_on"] = VERIFIED_ON
        caps.append(rec)
# Keep the original registry order from the reconciled snapshot: D6 follows
# the six capabilities first added in the 2026-10-24 review.
for n in NEW:
    if n["id"] == "D6":
        continue
    n.setdefault("verified_on", VERIFIED_ON if n.get("checked") else None)
    caps.append(n)
for n in EXTENDED_CAPABILITIES:
    caps.append(n)
_d6 = next(n for n in NEW if n["id"] == "D6")
_d6.setdefault("verified_on", VERIFIED_ON if _d6.get("checked") else None)
caps.append(_d6)
for c in caps:
    if c["id"] in REVISED_FIELDS:
        c.update(REVISED_FIELDS[c["id"]])

out = {"generated": GENERATED_ON, "grades": ["PROVEN", "SUPPORTED", "OPEN", "CONTRADICTED"],
       "capabilities": caps, "shapes": SHAPES, "rows": ROWS, "sources": S}
json.dump(out, open(HERE / "registry.json", "w"), indent=1, ensure_ascii=False)
print(f"registry.json written: {len(caps)} capabilities "
      f"({sum(1 for c in caps if c['artefact_origin']=='A')} from A, "
      f"{sum(1 for c in caps if c['artefact_origin']!='A')} added), "
      f"{len(SHAPES)} shapes, {len(ROWS)} rows")

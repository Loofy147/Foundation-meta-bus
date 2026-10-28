#!/usr/bin/env python3
"""
build_plan.py -- authors three linked datasets (all generated outputs are JSON, never hand-edited):

  meta_docs_map.json   what Meta documentation was read, how well, and what was NOT read
  assumptions.json     every load-bearing assumption: owner, falsification test, what breaks if false
  roadmap.json         work items (verify / decide / legal / build / test) and scenarios

Roadmap rules: no dates and no effort guesses. Items have dependencies and the resources they need.
Scenarios are switched by assumption outcomes (holds / fails) and change which items matter.

Grades follow the registry: PROVEN, SUPPORTED, OPEN, CONTRADICTED. Reading grades: PRIMARY (vendor page retrieved),
SECONDARY (third-party mirror or reporting), ATTEMPTED (tried, inconclusive), NOT_READ.
"""
import json, pathlib
HERE = pathlib.Path(__file__).parent
READ_ON = "2026-10-24"

# ---------------------------------------------------------------- documentation coverage map
def R(id, area, url, grade, facts, affects, note=""):
    return dict(id=id, area=area, url=url, grade=grade, read_on=READ_ON, facts=facts, affects=affects, note=note)
def N(id, area, priority, why, affects, tests=None):
    return dict(id=id, area=area, url=None, grade="NOT_READ", priority=priority, why=why, affects=affects, tests=tests or [])

DOCS = [
 R("D01", "WhatsApp solution providers overview", "https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/overview/", "PRIMARY",
   ["Partner types: Solution Partners, Tech Providers, Tech Partners.", "Solution Partners can extend a credit line; becoming one is lengthy; Tech Providers have Direct Support.",
    "Providers use business tokens exclusively."], ["TP1"]),
 R("D02", "Become a Tech Provider", "https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/get-started-for-tech-providers", "PRIMARY",
   ["Requires business verification and Advanced access through App Review.", "Independent Tech Provider or via a Solution Partner (only Solution Partner app ids are accepted)."], ["TP1"]),
 R("D03", "Embedded Signup overview and onboarding as a Tech Provider", "https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/overview/", "PRIMARY",
   ["Embedded Signup v2 was deprecated on 2026-10-15; v4 is required.", "Tech Provider customers must attach a payment method to their WABA unless a Solution Partner shares credit.",
    "A sandbox test account can simulate a customer completing the flow."], ["TP1", "T1"]),
 R("D04", "App Review and permissions (WhatsApp)", "https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/app-review", "PRIMARY",
   ["Business apps are auto-approved for Standard Access.", "A direct developer using only its own business assets needs neither Advanced access nor App Review.",
    "whatsapp_business_manage_events logs events such as purchase and leads; auto-approved if Advanced access to whatsapp_business_messaging exists."], ["F1", "TP1"]),
 R("D05", "Conversions API for Business Messaging (newer version)", "https://developers.facebook.com/documentation/ads-commerce/conversions-api/business-messaging", "PRIMARY",
   ["Graph v26.0 samples; ctwa_clid is a personal identifier, unique per click, stored with the conversation.", "Fourteen supported event names; Meta does not deduplicate; the 7-day limit and subset-of-countries limit apply to the hashed fallback only."],
   ["F1", "F2", "F3"], "Fetched with a redirect; this is the version to cite."),
 R("D06", "Conversions API for Business Messaging (older snapshot)", "https://developers.facebook.com/docs/marketing-api/conversions-api/business-messaging/", "PRIMARY",
   ["Graph v16.0 samples; partner-addressed; Ads Management Standard Access prerequisite (1,500 calls in 15 days).", "Same event list and the same deduplication note."], ["F1"],
   "Served at the old URL; differs from D05. Always record the final URL."),
 R("D07", "Webhooks: create endpoint and overview", "https://developers.facebook.com/documentation/business-messaging/whatsapp/webhooks/create-webhook-endpoint", "PRIMARY",
   ["GET handshake returns 200 with hub.challenge; POST carries X-Hub-Signature-256.", "Non-200 deliveries retried with decreasing frequency for up to 7 days; payloads up to 3 MB; one endpoint per Meta app; mTLS supported."], ["M1"]),
 R("D08", "Cloud API get started", "https://developers.facebook.com/docs/whatsapp/cloud-api/get-started/", "PRIMARY",
   ["Setup creates a test WABA and a test business number that can message up to 5 verified recipients."], ["T1"]),
 R("D09", "WhatsApp Business Solution Terms (preview URL)", "https://whatsapp.com/legal/business-solution-terms/preview?amp=&lang=en", "PRIMARY",
   ["No use of Business Solution Data, including derived forms, to train or improve AI models, except fine-tuning a model for exclusive use.",
    "No sharing with third parties except Third Party Service Providers; no building or augmenting profiles on individual users except message-thread content."], ["X1", "B4"],
   "Preview URL; the AI Providers clause was not on the retrieved page and is SUPPORTED by quotation only."),
 R("D10", "WhatsApp Business Messaging Policy and opt-in guidance", "https://business.whatsapp.com/policy", "PRIMARY",
   ["Opt-in required before messaging, may be general if local law is met, recommended per category; opt-outs honoured.", "Businesses secure consents and keep a published privacy policy; Commerce Policy governs commerce; policy may change without notice."], ["O1"],
   "Retrieved in fragments; full text not read."),
 R("D11", "Meta Business Agent overview", "https://developers.facebook.com/documentation/meta-business-agent/overview", "PRIMARY",
   ["Primary responder managed through Business Agent Platform APIs; can call our APIs and subscribe to webhooks.", "Excluded verticals; the business must be based in an authorized country; priced separately from other messages."], ["B2"]),
 R("D12", "WhatsApp pricing (help text mirror and BSP-hosted rate cards)", "https://support.chatarchitect.com/books/whatsapp-business-platform/page/about-billing-for-your-whatsapp-business-account", "SECONDARY",
   ["Per-message pricing since 2025-07-01; service and in-window utility free; 72-hour free entry point window for CTWA."], ["C0"], "Algeria's rate not retrieved."),
 R("D13", "AI Providers clause reporting", "https://techcrunch.com/2025/10/18/whatssapp-changes-its-terms-to-bar-general-purpose-chatbots-from-its-platform", "SECONDARY",
   ["Effective 2026-01-15; primary-versus-incidental functionality test at Meta's sole discretion; business customer-service AI not affected per Meta's statement."], ["X1"]),
 R("D14", "Business Agent announcement and pricing reports", "https://itdaily.com/news/software/meta-business-agent-available-worldwide/", "SECONDARY",
   ["Announced as global on 2026-06-03; reported US$2.00 per million tokens from 2026-08-01."], ["B2"]),
 R("D15", "Meta ad payment methods for Algeria", "https://help.instagram.com/1522953744580283", "ATTEMPTED",
   ["Meta's page is a country selector; the Algeria list could not be retrieved and results were unrelated third parties."], ["P1"], "Inconclusive; not used as evidence."),
 N("N01", "WhatsApp pricing page and the Algeria rate card", "HIGH", "Needed to size cost per order; rate cards came only through a BSP and did not parse.", ["C0"], ["A-13"]),
 N("N02", "Business Agent authorized-country list and non-template pricing page", "HIGH", "Decides whether the agent can be used at all from Algeria.", ["B2"], ["A-04"]),
 N("N03", "Business verification requirements and accepted documents for an Algerian entity", "HIGH", "Gates every account-level step.", ["TP1", "M1"], ["A-07"]),
 N("N04", "Full current Business Solution Terms, including the Third Party Service Provider definition", "HIGH", "Decides whether couriers, the PSP and an LLM vendor can receive data.", ["X1"], ["A-08", "A-10", "A-11"]),
 N("N05", "Meta ad payment methods and WABA billing requirements for Algeria", "HIGH", "Decides whether ads and messaging can be funded.", ["P1"], ["A-06"]),
 N("N06", "Platform Terms and Developer Policies (data deletion, retention)", "HIGH", "Meta-side obligations for data we receive through the platform.", ["K1", "X1"], ["A-19"]),
 N("N07", "Messaging limits, quality rating and phone number registration", "MEDIUM", "Operational ceilings and number health.", ["M1"], ["A-19"]),
 N("N08", "WhatsApp Flows documentation", "MEDIUM", "Flows carry address and wilaya capture in the order path.", ["D2"], ["A-19"]),
 N("N09", "Click-to-WhatsApp ad creation (Marketing API) and ad policies", "MEDIUM", "Source of every ctwa_clid.", ["D1", "A1"], ["A-19"]),
 N("N10", "Commerce Policy prohibited list and catalogue or Shops availability for Algeria", "MEDIUM", "Product categories and the E5 label.", ["E5", "D3", "O1"], ["A-19"]),
 N("N11", "Template categories, approval rules and marketing restrictions", "MEDIUM", "Order-update templates and their cost.", ["O1", "C0"], ["A-12"]),
 N("N12", "Graph API versioning, deprecation and rate limits", "MEDIUM", "Maintenance burden and the v26.0 pin.", ["F1", "M1"], ["A-19"]),
 N("N13", "Business Agent Platform API reference", "MEDIUM", "Needed before any adapter for B2.", ["B2"], ["A-04"]),
 N("N14", "Instagram and Messenger messaging APIs", "LOW", "No adapter specified for them yet.", ["B1"], []),
 N("N15", "Meta Verified and badge programmes", "LOW", "Not on the critical path.", ["F4"], []),
]

# ---------------------------------------------------------------- assumptions
def A(id, statement, category, depends, if_false, test, needs, grade, basis, tested_by_note=""):
    return dict(id=id, statement=statement, category=category, depends=depends, if_false=if_false, test=test, needs=needs,
                grade=grade, basis=basis, status="OPEN", owner=None, review_by=None)

ASSUMPTIONS = [
 A("A-01", "A direct developer can send business-messaging conversion events for its own WABA and dataset under Standard Access.", "platform", ["F1", "F3", "S1"],
   "CAPI cannot be used directly; a Tech Provider or Solution Partner route (TP1) or no conversion signal.",
   "Send a test event for a real ctwa_clid to our own dataset and see it in Events Manager.", ["account", "spend"], "SUPPORTED",
   "App Review page says direct developers need no Advanced access; neither CAPI guide says so for this endpoint."),
 A("A-02", "Meta accepts DZD as the event currency.", "platform", ["F1", "F3"], "Convert to USD or EUR before sending, adding a rate source and rounding policy.",
   "Send a DZD test event; check Events Manager.", ["account", "spend"], "OPEN", "Not stated in the pages read."),
 A("A-03", "The WhatsApp channel we use (direct or BSP) preserves the referral object and ctwa_clid.", "platform", ["M1", "S1", "F1"],
   "Attribution is lost silently; the provider choice must change.", "Real click-to-WhatsApp entry through the chosen channel; confirm clid in our webhook.", ["account", "spend"], "SUPPORTED",
   "Wrappers are reported to drop or relocate the referral."),
 A("A-04", "Meta Business Agent is authorized for businesses based in Algeria and handles Darja and Arabizi acceptably.", "platform", ["B2", "B4"],
   "Use our own conversation runtime (own_templates, own_encoder) and keep the agent out of the plan.", "Read the authorized-country list; try enabling; score it on a labelled set.", ["none", "account", "data"], "OPEN",
   "Overview requires an authorized country; press says global; no dialect evidence."),
 A("A-05", "Algerian counsel permits the additional flows to foreign providers: conversion dispatch, hosted LLM on redacted text, Meta's agent, and Z2 hosting location.", "legal", ["K1", "F1", "B2", "B4"],
   "No personal data leaves Algeria beyond the channel itself; CAPI with ctwa_clid and any hosted LLM are off.", "Written opinion on the flows in section 14.1.", ["counsel"], "OPEN",
   "Law summary read; specifics conflict across sources."),
 A("A-06", "An Algerian business can fund Meta ads and WhatsApp billing with an instrument Meta accepts.", "economic", ["P1"],
   "No ads and no paid messaging from our own account; an agency or partner billing route is needed.", "Add a payment method in Ads Manager and WhatsApp Manager; reconcile a small charge.", ["account", "entity"], "OPEN",
   "Meta's country list was not retrievable; trade sources report CIB and Edahabia are generally rejected."),
 A("A-07", "An Algerian entity can complete Meta business verification.", "platform", ["TP1", "M1"], "All account-level steps stall.", "Start verification with the entity's documents.", ["entity"], "OPEN", "Requirements not read."),
 A("A-08", "Our conversational agent is incidental to a business service, not an AI Provider under the Business Solution Terms.", "legal", ["B2", "B4", "X1"],
   "WhatsApp access could be refused or removed in Meta's sole discretion; positioning and scope must change.", "Counsel review of the terms and our positioning; ask Meta Direct Support in writing if available.", ["counsel"], "OPEN",
   "Clause text seen second-hand; the test is Meta's own discretion."),
 A("A-09", "Training or fine-tuning our NLU on our WhatsApp conversations stays inside the exclusive-use exception.", "legal", ["B4", "X1"],
   "Training data must come from synthetic and public Darja corpora only; no vendor may touch conversation-derived data.", "Counsel review plus architecture check: model private, dataset unshared, no vendor training.", ["counsel"], "SUPPORTED",
   "Exception text read on the terms page; its application to a classifier head is unreviewed."),
 A("A-10", "Couriers, the payment PSP and an LLM vendor are Third Party Service Providers under the terms.", "legal", ["L1", "P2", "X1"],
   "Sharing customer data with them breaches the terms.", "Read the definition; sign written terms with each.", ["none", "counsel"], "OPEN", "Definition not read."),
 A("A-11", "Lead tagging (HOT, WARM, COLD) and per-contact attribution are not profile building on individual WhatsApp users.", "legal", ["S1", "X1"],
   "Remove scoring or confine it to message-thread content.", "Counsel review against the profile-building clause and its message-thread exception.", ["counsel"], "OPEN", "Clause read; application unreviewed."),
 A("A-12", "A user-initiated click-to-WhatsApp conversation is sufficient opt-in for service replies and utility updates; marketing needs separate opt-in.", "legal", ["O1", "K2"],
   "Add explicit opt-in capture before order updates outside the 24-hour window.", "Counsel review of the policy and local law.", ["counsel"], "OPEN", "Opt-in may be general per policy; sufficiency unreviewed."),
 A("A-13", "Per-message costs in Algeria are acceptable: the sales conversation fits the 72-hour free window and post-window updates are cheap enough.", "economic", ["C0"],
   "Cut notification count or move updates to another channel.", "Read Algeria's rate card and model cost per order.", ["none"], "OPEN", "Rate not retrieved."),
 A("A-14", "Sending the purchase signal at delivery improves optimisation versus sending it at confirmation.", "economic", ["F3"], "Send earlier, accepting returns in the signal.",
   "A/B the trigger on live campaigns.", ["account", "spend"], "OPEN", "Meta says purchase optimisation exists; says nothing about COD timing."),
 A("A-15", "Last click before order creation selects the right ctwa_clid.", "technical", ["S1", "F1"], "Audit mismatches and change the rule.",
   "Compare chosen clids with Meta-reported conversions on a sample.", ["account", "spend"], "OPEN", "Judgment."),
 A("A-16", "Algerian courier APIs are available to us with verified accounts, and commune-name mismatches are manageable.", "technical", ["L1"],
   "Manual parcel creation or a unified wrapper.", "Open courier accounts and create sandbox parcels.", ["account"], "SUPPORTED", "Vendor docs and plugin pages."),
 A("A-17", "A domestic payment-link rail does not cost more conversion than it gains in cash certainty.", "economic", ["P2"], "Stay COD-only.", "A/B test.", ["account", "spend"], "OPEN", "Single vendor claim."),
 A("A-18", "Records keyed by an opaque id with a Z1 identity map are not personal data.", "legal", ["K1"], "Treat the event log as personal data everywhere.", "Counsel opinion.", ["counsel"], "OPEN", "Conservative default already treats them as personal."),
 A("A-19", "Meta policies, terms, pricing and API versions change often enough to need a 30 to 90 day re-verification cycle.", "operational", ["O1", "C0", "X1", "F1"],
   "Shorten or lengthen the cycle.", "Track diffs of the key pages over two or three cycles.", ["none"], "SUPPORTED", "Policy says changes may occur without notice; two CAPI guide versions coexist."),
 A("A-20", "The Cloud API test number is enough to test webhooks, signatures, message flow and status events without a business WhatsApp account.", "technical", ["T1", "M1"],
   "A real WABA is needed even for plumbing tests.", "Set up the test number, point the webhook at our endpoint, send a message.", ["dev"], "SUPPORTED", "Get Started page; limits on referrals known."),
 A("A-21", "Phase 1 operates for businesses we own or control, as a direct developer, not as a multi-merchant platform.", "scope", ["TP1", "X1"],
   "Tech Provider onboarding, App Review, per-customer billing and heavier scrutiny under the AI Providers clause become required.", "Decision by the project owner.", ["user"], "OPEN",
   "Not stated by the owner; assumed from the single-business framing."),
]

# ---------------------------------------------------------------- roadmap
def I(id, title, kind, needs, depends=None, tests=None, unlocks="", scenario_only=None, moot_when=None):
    return dict(id=id, title=title, kind=kind, needs=needs, depends_on=depends or [], tests=tests or [], unlocks=unlocks,
                scenario_only=scenario_only or [], moot_when=moot_when or [])
ITEMS = [
 I("V-01", "Read Algeria's rate card on Meta's pricing page and model cost per order", "verify", ["none"], tests=["A-13"], unlocks="cost model for W2 notifications"),
 I("V-02", "Read the Business Agent authorized-country list and non-template pricing page", "verify", ["none"], tests=["A-04"], unlocks="go or no-go on the agent"),
 I("V-03", "Read business verification requirements for an Algerian entity", "verify", ["none"], tests=["A-07"], unlocks="account setup plan"),
 I("V-04", "Read the full current Business Solution Terms, including the Third Party Service Provider definition", "verify", ["none"], tests=["A-08", "A-10", "A-11"], unlocks="counsel brief"),
 I("V-05", "Read Meta ad payment and WABA billing requirements for Algeria", "verify", ["none"], tests=["A-06"], unlocks="funding plan"),
 I("V-06", "Read the documentation backlog: platform terms, limits and quality, Flows, CTWA ads, commerce policy, templates, Graph versioning", "verify", ["none"], tests=["A-19", "A-12"], unlocks="coverage map to zero HIGH items"),
 I("D-01", "Decide the operating model: direct developer for owned businesses, or multi-merchant platform", "decide", ["user"], tests=["A-21"], unlocks="scenario S7 on or off"),
 I("L-01", "Brief Algerian counsel with the flow inventory and the Meta terms constraints; obtain a written opinion", "legal", ["counsel"], depends=["V-04"],
   tests=["A-05", "A-08", "A-09", "A-10", "A-11", "A-12", "A-18"], unlocks="policy table decisions"),
 I("L-02", "Record each ruling in the policy table with owner and decided_on; rerun the gate", "decide", ["counsel"], depends=["L-01"], unlocks="gate G2"),
 I("B-01", "Spec v0.3: provider requirements, send_template with opt-in guard and cost class, opt-in purposes, window logic", "build", ["none"], unlocks="spec matches Meta's rules"),
 I("B-02", "Build the template responder and the order workflow on mocks", "build", ["none"], depends=["B-01"], unlocks="a working Z1-only conversation path"),
 I("B-03", "Build the NLU benchmark harness on synthetic and public Darja data only", "build", ["none"], unlocks="agent comparison"),
 I("B-04", "Build the CAPI transport, token handling and stuck-send reconciler behind an injected transport", "build", ["none"], unlocks="live CAPI test"),
 I("B-05", "Deploy the webhook ingress behind public HTTPS for the test number", "build", ["dev"], unlocks="live plumbing test"),
 I("B-06", "Build the Yalidine and Ecotrack adapters against mocks", "build", ["none"], unlocks="courier sandbox test"),
 I("T-01", "Test number smoke test: webhook delivery, signature, statuses, message flow into the store", "test", ["dev"], depends=["B-05"], tests=["A-20"], unlocks="plumbing proven live"),
 I("X-01", "Complete account setup: business verification, WABA, ad account and payment methods", "test", ["entity", "account"], depends=["D-01", "V-03", "V-05"], tests=["A-06", "A-07"], unlocks="every live test"),
 I("X-02", "Run a real click-to-WhatsApp entry and confirm ctwa_clid reaches the webhook through the chosen channel", "test", ["account", "spend"], depends=["X-01", "T-01"], tests=["A-03"], unlocks="attribution proven"),
 I("X-03", "Send a CAPI test event with DZD from the direct-developer path and audit clid selection", "test", ["account", "spend"], depends=["X-02", "B-04", "L-02"], tests=["A-01", "A-02", "A-15"], unlocks="conversion signal proven",
   moot_when=[{"A-01": "fails"}, {"A-05": "fails"}]),
 I("X-04", "Open courier accounts and create sandbox parcels", "test", ["account"], depends=["B-06"], tests=["A-16"], unlocks="logistics proven"),
 I("X-05", "Domestic payment-link rail experiment", "test", ["account", "spend"], depends=["X-01"], tests=["A-17"], unlocks="payment decision"),
 I("E-01", "Experiment: purchase signal at confirmation versus delivery", "test", ["account", "spend"], depends=["X-03"], tests=["A-14"], unlocks="signal timing decision",
   moot_when=[{"A-01": "fails"}, {"A-05": "fails"}]),
 I("E-02", "Trial Business Agent against our own runtime on a labelled set", "test", ["account", "data"], depends=["X-01", "V-02", "B-03"], tests=["A-04"], unlocks="agent decision",
   moot_when=[{"A-08": "fails"}, {"A-04": "fails"}]),
 I("G-01", "Production gate review: G0 to G5 evidence present, no open HIGH assumption on the critical path", "decide", ["user"], depends=["X-01", "X-02", "X-03", "L-02", "B-02", "X-04"], unlocks="first production traffic"),
 # scenario-only items
 I("SC-2", "Select a Tech Provider or BSP route and verify it preserves the referral", "decide", ["account"], depends=["X-01"], tests=["A-03"], scenario_only=["S2"], unlocks="channel choice"),
 I("SC-4", "Measure without conversion dispatch: first-party funnel and Ads Manager conversation counts", "build", ["none"], scenario_only=["S4"], unlocks="attribution fallback"),
 I("SC-6", "Own runtime only: templates and encoder in Z1; defer hosted LLM until counsel permits", "build", ["none"], scenario_only=["S6"], unlocks="conversation path without Meta's agent"),
 I("SC-7", "Tech Provider onboarding path: verification, App Review, Embedded Signup v4, per-customer billing", "build", ["entity", "account"], depends=["X-01"], scenario_only=["S7"], unlocks="multi-merchant capability"),
 I("SC-8", "Alternative ad funding route through an agency or partner account", "decide", ["entity"], scenario_only=["S8"], unlocks="ads without own billing"),
 I("SC-9", "Narrow to Meta's own agent and stop building a separate LLM conversation layer", "decide", ["counsel"], depends=["L-01"], scenario_only=["S9"], unlocks="policy-safe agent"),
]

def S(id, title, when, consequences, watch):
    return dict(id=id, title=title, when=when, consequences=consequences, watch=watch)
SCENARIOS = [
 S("S1", "Direct path works", {"A-01": "holds"}, ["M1 can be the direct Cloud API; no BSP is required for conversion events.", "F1 and F3 proceed as specified."], ["A-02", "A-03"]),
 S("S2", "Partner or BSP route required", {"A-01": "fails"}, ["TP1 or a BSP becomes the channel; M1 changes.", "Policy rows gain the BSP as a provider; the referral must be re-verified through it (A-03)."], ["A-03", "A-10"]),
 S("S3", "Counsel permits the extra flows", {"A-05": "holds"}, ["capi_meta, meta_business_agent and llm_hosted can be enabled once rows are decided.", "Hosted LLM still needs written no-training terms (A-09, A-10)."], ["A-09", "A-10"]),
 S("S4", "Counsel restricts the extra flows", {"A-05": "fails"}, ["No ctwa_clid or personal text leaves Z1 beyond the channel; conversion dispatch off.", "Conversation runs on own_templates and own_encoder; attribution falls back to first-party measurement."], ["A-18"]),
 S("S5", "Business Agent usable", {"A-04": "holds"}, ["B2 becomes an adapter behind the conversation port, per-intent by benchmark.", "Token pricing enters the cost model (C0)."], ["A-08", "A-13"]),
 S("S6", "Business Agent unavailable or unfit", {"A-04": "fails"}, ["Own runtime is the only conversation path; B4 and templates carry the load."], ["A-09"]),
 S("S7", "Multi-merchant platform", {"A-21": "fails"}, ["TP1 required: business verification, App Review, Embedded Signup v4, business tokens, per-customer payment methods.", "Our own positioning is scrutinised under the AI Providers clause (A-08).", "Each merchant becomes a data controller relationship to document."], ["A-08", "A-07"]),
 S("S8", "Ad funding blocked", {"A-06": "fails"}, ["No own ad billing; ads run through an agency or partner account, which changes who owns the dataset and the clid."], ["A-01", "A-07"]),
 S("S9", "Our agent counts as an AI Provider", {"A-08": "fails"}, ["Use Meta's own agent only; stop shipping a separate LLM conversation layer on WhatsApp."], ["A-04", "A-09"]),
]

HERE.joinpath("meta_docs_map.json").write_text(json.dumps(DOCS, indent=1, ensure_ascii=False))
HERE.joinpath("assumptions.json").write_text(json.dumps(ASSUMPTIONS, indent=1, ensure_ascii=False))
HERE.joinpath("roadmap.json").write_text(json.dumps({"items": ITEMS, "scenarios": SCENARIOS,
    "needs": ["none", "dev", "account", "spend", "entity", "counsel", "data", "user"]}, indent=1, ensure_ascii=False))
print(f"meta_docs_map.json {len(DOCS)} entries ({sum(1 for d in DOCS if d['grade']=='NOT_READ')} not read) | "
      f"assumptions.json {len(ASSUMPTIONS)} | roadmap.json {len(ITEMS)} items, {len(SCENARIOS)} scenarios")

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
        rec = {"id": c["id"], "name": c["name"], "code": c["code"], "layer": LAYER[g["id"]],
               "group": g["id"], "artefact_origin": "A", "a_status": c["status"], "status": c["status"],
               "complexity": c["complexity"], "meta_ref": c["meta_ref"], "desc": c["desc"],
               "checked": False, "notes": "Inherited from artefact A; not examined in this study.",
               "depends_on": DEPS.get(c["id"], []),
               "evidence": [ev("OPEN", "Taken from artefact A without independent verification.", "artefact_A")],
               "verified_on": None}
        if c["id"] in OVERRIDE:
            rec.update(OVERRIDE[c["id"]]); rec["verified_on"] = VERIFIED_ON
        caps.append(rec)
for n in NEW:
    n.setdefault("verified_on", VERIFIED_ON if n.get("checked") else None)
    caps.append(n)

out = {"generated": VERIFIED_ON, "grades": ["PROVEN", "SUPPORTED", "OPEN", "CONTRADICTED"],
       "capabilities": caps, "shapes": SHAPES, "rows": ROWS, "sources": S}
json.dump(out, open(HERE / "registry.json", "w"), indent=1, ensure_ascii=False)
print(f"registry.json written: {len(caps)} capabilities "
      f"({sum(1 for c in caps if c['artefact_origin']=='A')} from A, "
      f"{sum(1 for c in caps if c['artefact_origin']!='A')} added), "
      f"{len(SHAPES)} shapes, {len(ROWS)} rows")

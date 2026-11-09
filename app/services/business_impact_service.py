"""Business Impact Analysis Engine
Translates technical graph diffs, missing items, and validation warnings into
plain-language ("pati bangla" and simple business terms) executive summaries,
highlighting financial/operational risks and recommending concrete client decisions.
"""
import re


# Domain specific knowledge dictionary for FMCG and Finance
BUSINESS_TERM_KNOWLEDGE = {
    # Trade Promotions & Gross-to-Net
    "tradespend": {
        "title_bn": "ট্রেড প্রমোশন ও রিটেইলার ডিসকাউন্ট স্কিম",
        "title_en": "Trade Promotion & Retailer Scheme Spend",
        "explanation_bn": "ডিস্ট্রিবিউটর, ডিলার বা রিটেইলারদের দেওয়া বিশেষ ডিসকাউন্ট, ক্যাশ ব্যাক বা ফ্রি স্যাম্পল অফার।",
        "impact_bn": "ইনভয়েসের পর কত টাকা ডিসকাউন্টে খরচ হলো তা ট্র্যাক করা যাবে না। বাজেট ছাড়া অতিরিক্ত ছাড় চলে গেলে কোম্পানির মোট মার্জিন বা মুনাফা কমে যাবে।",
        "action_bn": "আপনার ব্যবসায় ডিলার স্কিম বা ক্যাশ ডিসকাউন্ট থাকলে এটি মডেলে বহাল রাখুন। ফিক্সড প্রাইসে সেল হলে বাদ দিতে পারেন।",
        "severity": "high",
    },
    "promoplan": {
        "title_bn": "প্রমোশনাল ক্যাম্পেইন ও অফার প্ল্যানিং",
        "title_en": "Trade Promotional Campaign Planning",
        "explanation_bn": "উৎসব বা সিজনভিত্তিক প্রমোশনাল অফার ও স্কিম পূর্বপরিকল্পনা করার কাঠামো।",
        "impact_bn": "কোন স্কিমে কত বিক্রি বাড়ল এবং স্কিমের খরচ পুষিয়ে লাভ হলো কিনা (Promo ROI) তা যাচাই করা অসম্ভব হবে।",
        "action_bn": "ভবিষ্যতে প্রমোশনের লাভ-ক্ষতি হিসাব করতে চাইলে এটি অন্তর্ভুক্ত রাখা অত্যন্ত জরুরি।",
        "severity": "high",
    },
    "grosstonetwaterfall": {
        "title_bn": "গ্রস থেকে আসল নেট আয় হিসাব (Gross-to-Net)",
        "title_en": "Gross-to-Net Revenue Reconciliation",
        "explanation_bn": "ইনভয়েসের মোট মূল্য (Gross) থেকে ডিসকাউন্ট, ড্যামেজ রিটার্ন ও ট্যাক্স বাদ দিয়ে ব্যাংকে জমা হওয়া আসল রেভিনিউ গণনা।",
        "impact_bn": "এই নিয়ম পরিবর্তিত হলে ব্যালেন্স শিটে মোট বিক্রির সাথে ব্যাংকে ঢোকা আসল টাকার অমিল হবে।",
        "action_bn": "ক্যাশ ফ্লো এবং ফাইন্যান্সিয়াল অডিটের সুরক্ষার জন্য এই ক্যালকুলেশন রুল সতর্কতার সাথে যাচাই করুন।",
        "severity": "high",
    },
    "onoffinvoice": {
        "title_bn": "অন-ইনভয়েস বনাম অফ-ইনভয়েস ছাড় পলিসি",
        "title_en": "On-Invoice vs Off-Invoice Deduction Policy",
        "explanation_bn": "বিলের ভেতরে দেওয়া তাৎক্ষণিক ছাড় এবং বিলের বাইরে মাস শেষে দেওয়া বিশেষ রিবেট বা ইনসেন্টিভ।",
        "impact_bn": "বিল বা রসিদের বাইরে পরে দেওয়া কমিশন ও রিবেট ট্র্যাক না হলে অ্যাকাউন্টিংয়ে অসঙ্গতি ও রাজস্ব ফাঁক তৈরি হবে।",
        "action_bn": "যদি ডিলারদের বছর বা মাস শেষে টার্নওভার রিবেট দেওয়ার নিয়ম থাকে তবে এটি রাখুন।",
        "severity": "medium",
    },
    "accrualbasis": {
        "title_bn": "বকেয়া ও অগ্রিম সমন্বয়ের নিয়ম (Accrual Accounting)",
        "title_en": "Accrual Accounting Principle",
        "explanation_bn": "মাল ডেলিভারির সাথে সাথেই খাতায় খরচ বা আয় তোলা, টাকা হাতে পাওয়ার জন্য অপেক্ষা না করা।",
        "impact_bn": "এটি বাদ দিলে যেদিন ক্যাশ টাকা লেনদেন হবে শুধু সেদিন হিসাব হবে, ফলে চলতি মাসের লাভ-ক্ষতির চিত্র ভুল দেখাবে।",
        "action_bn": "স্ট্যান্ডার্ড অ্যাকাউন্টিং এবং কর অডিটের জন্য অ্যাক্রুয়াল পলিসি সচল রাখা শ্রেয়।",
        "severity": "medium",
    },
    "deductionmethod": {
        "title_bn": "ডিসকাউন্ট কর্তনের পদ্ধতি (Deduction Method)",
        "title_en": "Deduction Method Rules",
        "explanation_bn": "পার্সেন্টেজ হারে নাকি ফিক্সড টাকায় ডিসকাউন্ট কাটা হবে তার ফর্মুলা।",
        "impact_bn": "ফর্মুলা না থাকলে বিলিং সিস্টেম স্বয়ংক্রিয়ভাবে ডিসকাউন্ট কাটতে পারবে না, ম্যানুয়াল ভুলের সুযোগ তৈরি হবে।",
        "action_bn": "বিলিং সফটওয়্যার ও ইআরপির সাথে মেলানোর জন্য নির্দিষ্ট ফর্মুলা বহাল রাখুন।",
        "severity": "medium",
    },
    # Sales & Distribution (RtM)
    "secondarysales": {
        "title_bn": "ডিস্ট্রিবিউটর সেকেন্ডারি সেলস (দোকানে আসল বিক্রি)",
        "title_en": "Secondary Sales (Distributor to Retail Outlet)",
        "explanation_bn": "কোম্পানি থেকে ডিস্ট্রিবিউটরের গুদামে মাল যাওয়ার পর সেখান থেকে রিটেইল দোকানে প্রতিদিন কত বিক্রি হচ্ছে।",
        "impact_bn": "দোকানে কী বিক্রি হচ্ছে না জানলে বাজারে কোন মালের ঘাটতি বা ওভারস্টক আছে বোঝা যাবে না। এতে ফ্যাক্টরিতে ভুল পরিমাণের উৎপাদন হতে পারে।",
        "action_bn": "মার্কেটের রিয়েল ডিমান্ড বুঝতে সেকেন্ডারি সেলস ডেটা পয়েন্ট আবশ্যক।",
        "severity": "high",
    },
    "primarysales": {
        "title_bn": "কোম্পানির প্রাইমারি সেলস ও ডিলার ইনভয়েসিং",
        "title_en": "Primary Sales (Company Billing to Distributors)",
        "explanation_bn": "ফ্যাক্টরি বা সিপিসি ডিপো থেকে ডিস্ট্রিবিউটর বা ডিলারের কাছে সরাসরি পণ্যের চালান পাঠানো।",
        "impact_bn": "এটি কোম্পানির প্রাথমিক রাজস্ব প্রবাহ নির্দেশ করে। এটি ব্যাহত হলে কোম্পানির টপ-লাইন রেভিনিউ রিপোর্টিং বন্ধ হয়ে যাবে।",
        "action_bn": "কোম্পানির নিজস্ব বিলিং ও অ্যাকাউন্টস মেলানোর জন্য এটি মডেলে অপরিবর্তিত রাখুন।",
        "severity": "high",
    },
    "outlet": {
        "title_bn": "রিটেইল আউটলেট ও স্টোর মাস্টার ডেটা",
        "title_en": "Retail Outlet Master & Coverage",
        "explanation_bn": "মুদি দোকান, ফার্মেসি বা সুপারশপের নাম, অবস্থান ও ক্যাটাগরি।",
        "impact_bn": "দোকানের মাস্টার ডেটা না থাকলে সেলস রিপ্রেজেন্টেটিভদের (SR) রুট প্ল্যান ও অর্ডার কালেকশনের কার্যকারিতা মনিটর করা যাবে না।",
        "action_bn": "ফিল্ড ফোর্সের দক্ষতা এবং আউটলেট পেনিট্রেশন ট্র্যাক করতে এটি অবশ্যই বজায় রাখুন।",
        "severity": "high",
    },
    "customeroutlet": {
        "title_bn": "গ্রাহক আউটলেট ও রিটেইলার প্রোফাইল",
        "title_en": "Customer Outlet & Retailer Profile",
        "explanation_bn": "রিটেইলারদের ক্রেডিট লিমিট, পেমেন্ট হিস্ট্রি ও শপের সাইজ।",
        "impact_bn": "কোন দোকান থেকে টাকা আদায় বাকি বা কার ক্রেডিট রিক্স বেশি তা চিহ্নিত করা যাবে না।",
        "action_bn": "বকেয়া আদায়ের ঝুঁকি কমাতে আউটলেট প্রোফাইল সংযুক্ত রাখা উচিত।",
        "severity": "medium",
    },
    "distributor": {
        "title_bn": "ডিস্ট্রিবিউটর ও ডিলারশিপ নেটওয়ার্ক",
        "title_en": "Distributor & Channel Partner Network",
        "explanation_bn": "পণ্য সরবরাহকারী ডিলারদের ভৌগোলিক সীমানা, গুদাম ও চুক্তি।",
        "impact_bn": "ডিস্ট্রিবিউটর চ্যানেল ছাড়া সামগ্রিক ডিস্ট্রিবিউশন পাইপলাইন ও পণ্যের প্রাপ্যতা ট্র্যাক করা অসম্ভব।",
        "action_bn": "ডিস্ট্রিবিউটর কমিশন ও পারফরম্যান্স পরিমাপে এটি সেন্ট্রাল নোড হিসেবে রাখুন।",
        "severity": "high",
    },
    "inventory": {
        "title_bn": "ইনভেন্টরি ও পণ্য স্টক ব্যালেন্স",
        "title_en": "Warehouse & In-Transit Inventory",
        "explanation_bn": "গুদামে, ফ্যাক্টরিতে ও রাস্তায় ট্রাকে কত টাকার ফিনিশড গুডস ও কাঁচামাল মজুত রয়েছে।",
        "impact_bn": "স্টকের হিসাব না থাকলে অতিরিক্ত স্টক জমে ক্যাশ আটকে যেতে পারে (Working Capital Blocked) অথবা পণ্য মেয়াদোত্তীর্ণ হয়ে ক্ষতি হতে পারে।",
        "action_bn": "কার্যকর সাপ্লাই চেইনের জন্য স্টক ট্র্যাকারের সাথে ইনভেন্টরি নোড বজায় রাখুন।",
        "severity": "high",
    },
}

# Structural warning translation
WARNING_TRANSLATIONS = {
    "reference_entities_removed": {
        "title_bn": "রেফারেন্স স্ট্যান্ডার্ড থেকে কিছু উপাদান বাদ পড়েছে",
        "title_en": "Industry Reference Elements Removed",
        "explanation_bn": "গ্লোবাল এফএমসিজি স্ট্যান্ডার্ডের কিছু গুরুত্বপূর্ণ বিষয় বর্তমান মডেলে রাখা হয়নি।",
        "impact_bn": "ভবিষ্যতে কোম্পানি যখন নতুন সিস্টেম বা উন্নত অটোমেশন চালু করতে যাবে, তখন এই বাদ পড়া বিষয়গুলোর অভাব দেখা দিতে পারে।",
        "action_bn": "বাদ পড়া উপাদানগুলো দেখে নিন; আপনার বর্তমান অপারেশনাল স্কোপে প্রয়োজন না হলে আপনি নিশ্চিন্তে ফাইনাল করতে পারেন।",
        "severity": "medium",
    },
    "no_attributes": {
        "title_bn": "একাধিক উপাদানে ডেটা ফিল্ডের অভাব (No Attributes)",
        "title_en": "Entities Lack Detailed Data Fields",
        "explanation_bn": "এন্টিটির নাম আছে কিন্তু ভেতরে কী কী ফিল্ড (যেমন: তারিখ, টাকা, পরিমাণ) থাকবে তা ফাঁকা রয়েছে।",
        "impact_bn": "ভবিষ্যতে এক্সেল, সিএসভি বা ইআরপি ডাটা আপলোড করলে সিস্টেম স্বয়ংক্রিয়ভাবে হিসাব মেলাতে পারবে না।",
        "action_bn": "ডেটা আপলোড করার আগে প্রয়োজনে চ্যাটবটের মাধ্যমে এই এন্টিটিগুলোতে প্রয়োজনীয় অ্যাট্রিবিউট যোগ করে নিন।",
        "severity": "high",
    },
    "isolated_entity": {
        "title_bn": "সম্পর্কহীন বা বিচ্ছিন্ন উপাদান (Isolated Entities)",
        "title_en": "Disconnected Data Elements",
        "explanation_bn": "মডেলে কিছু নতুন উপাদান যুক্ত করা হয়েছে কিন্তু অন্যান্য ডিপার্টমেন্টের সাথে এদের কোনো সংযোগ নেই।",
        "impact_bn": "রিপোর্টিংয়ের সময় সামগ্রিক ডেটার সাথে এটি যুক্ত হবে না, ফলে সাইলো (Data Silo) তৈরি হবে।",
        "action_bn": "অন্যান্য বিজনেস প্রসেসের সাথে লিঙ্ক তৈরি করুন অথবা অপ্রয়োজনীয় হলে বাদ দিন।",
        "severity": "medium",
    },
    "disconnected": {
        "title_bn": "মডেলের বিভিন্ন অংশের মধ্যে সংযোগের অভাব",
        "title_en": "Disconnected Process Sub-Graphs",
        "explanation_bn": "নলেজ গ্রাফের একটি বড় অংশ সম্পূর্ণ আলাদা হয়ে রয়েছে, মূল প্রক্রিয়ার সাথে যোগসূত্র নেই।",
        "impact_bn": "এন্ড-টু-এন্ড অটোমেশন বা ডেটা ফ্লো মাঝপথে আটকে যাবে।",
        "action_bn": "প্রসেসগুলোর মধ্যে মিসিং রিলেশনশিপ তৈরি করুন।",
        "severity": "high",
    },
}


def _normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def _find_term_match(term: str):
    k = _normalize_key(term)
    if k in BUSINESS_TERM_KNOWLEDGE:
        return BUSINESS_TERM_KNOWLEDGE[k]
    for dict_key, meta in BUSINESS_TERM_KNOWLEDGE.items():
        if dict_key in k or k in dict_key:
            return meta
    return None


def generate_business_impact(comparison: dict, validation: dict, domain: dict) -> dict:
    """Generate structured, plain-language business impact analysis from technical diff and validation."""
    items = []
    seen_ids = set()

    counts = comparison.get("counts", {}) if comparison else {}
    nodes_added = comparison.get("nodes_added", []) if comparison else []
    nodes_removed = comparison.get("nodes_removed", []) if comparison else []
    nodes_modified = comparison.get("nodes_modified", []) if comparison else []
    edges_added = comparison.get("edges_added", []) if comparison else []
    edges_removed = comparison.get("edges_removed", []) if comparison else []

    # 1. Process Removed Reference Entities (High/Medium business relevance)
    for node in nodes_removed:
        name = node.get("name", "Unknown")
        key = node.get("key", name)
        item_id = f"rem_{_normalize_key(key)}"
        if item_id in seen_ids:
            continue
        seen_ids.add(item_id)

        matched = _find_term_match(name) or _find_term_match(key)
        if matched:
            items.append({
                "id": item_id,
                "type": "entity_removed",
                "severity": matched["severity"],
                "technical_ref": f"Node removed: {name} ({key})",
                "title_bn": f"‘{matched['title_bn']}’ মডেল থেকে বাদ দেওয়া হয়েছে",
                "title_en": f"‘{matched['title_en']}’ removed from ontology",
                "explanation_bn": matched["explanation_bn"],
                "impact_bn": matched["impact_bn"],
                "action_bn": matched["action_bn"],
            })
        else:
            items.append({
                "id": item_id,
                "type": "entity_removed",
                "severity": "medium",
                "technical_ref": f"Node removed: {name} ({key})",
                "title_bn": f"‘{name}’ সংক্রান্ত তথ্য আপনার মডেল থেকে সরানো হয়েছে",
                "title_en": f"‘{name}’ entity removed from current ontology",
                "explanation_bn": f"স্ট্যান্ডার্ড আর্কিটেকচারের ‘{name}’ কম্পোনেন্টটি আপনার কাস্টমাইজড মডেলে অন্তর্ভুক্ত নেই।",
                "impact_bn": f"যদি আপনার বর্তমান বিজনেসে ‘{name}’ সংক্রান্ত কার্যক্রম থেকে থাকে, তবে সেই ডেটা ডিজিটাল টুইনে ট্র্যাক হবে না।",
                "action_bn": f"যদি আপনার কোম্পানিতে এটি দরকার না হয় তবে বাদ রাখা নিরাপদ। অন্যথায় ব্যাক করে চ্যাটে এটি যুক্ত করতে পারেন।",
            })

    # 2. Process Modified Entities (Name changes, attribute additions/removals)
    for node in nodes_modified:
        name = node.get("name", "Unknown")
        key = node.get("key", name)
        changes = node.get("changes", {})
        attr_rem = node.get("attributes_removed", [])
        attr_add = node.get("attributes_added", [])

        # Check for removed attributes
        for attr in attr_rem:
            item_id = f"attr_rem_{_normalize_key(attr)}"
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)
            matched = _find_term_match(attr)
            if matched:
                items.append({
                    "id": item_id,
                    "type": "attribute_removed",
                    "severity": matched["severity"],
                    "technical_ref": f"{name} attribute removed: {attr}",
                    "title_bn": f"{name}-এর ভেতরে ‘{matched['title_bn']}’ ফিল্ডটি বাদ দেওয়া হয়েছে",
                    "title_en": f"Field '{attr}' removed from {name}",
                    "explanation_bn": matched["explanation_bn"],
                    "impact_bn": matched["impact_bn"],
                    "action_bn": matched["action_bn"],
                })
            else:
                items.append({
                    "id": item_id,
                    "type": "attribute_removed",
                    "severity": "low",
                    "technical_ref": f"{name} attribute removed: {attr}",
                    "title_bn": f"{name}-এর ডেটা ফিল্ড ‘{attr}’ সরানো হয়েছে",
                    "title_en": f"Attribute '{attr}' removed from {name}",
                    "explanation_bn": f"এই এন্টিটি থেকে ‘{attr}’ তথ্যের কলামটি বাদ দেওয়া হয়েছে।",
                    "impact_bn": f"ভবিষ্যতে আপলোড করা ডকুমেন্টে এই ফিল্ডটি থাকলে তা এই মডেলে অটোম্যাপ হবে না।",
                    "action_bn": "যদি এই ফিল্ডের তথ্য আপনার ব্যবসায় অপ্রয়োজনীয় হয়, তবে ইগনোর করতে পারেন।",
                })

        # Name change interpretation
        if changes.get("name"):
            old_name = changes["name"].get("from")
            new_name = changes["name"].get("to")
            item_id = f"rename_{_normalize_key(key)}"
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                items.append({
                    "id": item_id,
                    "type": "renamed",
                    "severity": "low",
                    "technical_ref": f"Renamed: '{old_name}' -> '{new_name}'",
                    "title_bn": f"নাম পরিবর্তন: ‘{old_name}’ থেকে ‘{new_name}’ করা হয়েছে",
                    "title_en": f"Terminology adapted: '{old_name}' to '{new_name}'",
                    "explanation_bn": f"আপনার কোম্পানির ব্যবহৃত নিজস্ব অভ্যন্তরীণ পরিভাষা বা নামের সাথে সামঞ্জস্য রাখতে এটি রিনেম করা হয়েছে।",
                    "impact_bn": f"এটি একটি পজিটিভ কাস্টমাইজেশন। আপনার টিম নিজেদের চেনা নামে ডেটা দেখতে পারবে।",
                    "action_bn": "নামকরণ আপনার প্রতিষ্ঠানের ব্যবহারের সাথে মিললে এটি এপ্রুভ করে এগিয়ে যান।",
                })

    # 3. Process Validation Warnings
    warnings = validation.get("warnings", []) if validation else []
    for w in warnings:
        code = w.get("code")
        msg = w.get("message", "")
        item_id = f"warn_{code}_{_normalize_key(msg[:20])}"
        if item_id in seen_ids:
            continue
        seen_ids.add(item_id)

        rule = WARNING_TRANSLATIONS.get(code)
        if rule:
            items.append({
                "id": item_id,
                "type": "validation_warning",
                "severity": rule["severity"],
                "technical_ref": f"Warning [{code}]: {msg}",
                "title_bn": rule["title_bn"],
                "title_en": rule["title_en"],
                "explanation_bn": f"{rule['explanation_bn']} (বিস্তারিত: {msg})",
                "impact_bn": rule["impact_bn"],
                "action_bn": rule["action_bn"],
            })

    # 4. Process Validation Errors
    errors = validation.get("errors", []) if validation else []
    for e in errors:
        code = e.get("code")
        msg = e.get("message", "")
        item_id = f"err_{code}_{_normalize_key(msg[:20])}"
        if item_id in seen_ids:
            continue
        seen_ids.add(item_id)
        items.append({
            "id": item_id,
            "type": "validation_error",
            "severity": "critical",
            "technical_ref": f"Error [{code}]: {msg}",
            "title_bn": "গুরুত্বপূর্ণ ত্রুটি যা সংশোধন করা বাধ্যতামূলক",
            "title_en": "Critical schema error required to fix",
            "explanation_bn": f"মডেলে একটি টেকনিক্যাল জটিলতা রয়েছে: {msg}।",
            "impact_bn": "এই ত্রুটি ঠিক না করা পর্যন্ত ডিজিটাল টুইন ফাইনাল করা যাবে না এবং কোনো ফাইল প্রসেস হবে না।",
            "action_bn": "চ্যাটবটে ফিরে গিয়ে ত্রুটিটি সমাধান করুন।",
        })

    # Sort items by severity: critical > high > medium > low
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    items.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 4))

    # Calculate overall readiness verdict
    crit_count = sum(1 for i in items if i["severity"] == "critical")
    high_count = sum(1 for i in items if i["severity"] == "high")
    med_count = sum(1 for i in items if i["severity"] == "medium")
    low_count = sum(1 for i in items if i["severity"] == "low")

    if crit_count > 0:
        readiness_status = "blocked"
        verdict_bn = f"{crit_count}টি গুরুতর ত্রুটি রয়েছে যা ঠিক না করলে ডিজিটাল টুইন চূড়ান্ত করা যাবে না।"
        verdict_en = f"{crit_count} critical error(s) must be resolved before finalization."
    elif high_count > 0:
        readiness_status = "review_needed"
        verdict_bn = f"{high_count}টি গুরুত্বপূর্ণ পয়েন্টে বিজনেস সিদ্ধান্ত প্রয়োজন। এগুলো ব্যবসার জন্য প্রযোজ্য না হলে ইগনোর করে ফাইনাল করতে পারেন।"
        verdict_en = f"{high_count} high-impact business decisions require review."
    elif med_count > 0:
        readiness_status = "acceptable"
        verdict_bn = f"মডেলটি গ্রহণযোগ্য পর্যায়ে রয়েছে ({med_count}টি মাঝারি পর্যবেক্ষণ রয়েছে)। আপনি চাইলে ফাইনাল করতে পারেন।"
        verdict_en = f"Model is largely ready with {med_count} minor operational notes."
    else:
        readiness_status = "ready"
        verdict_bn = "অভিনন্দন! আপনার মডেলটি সম্পূর্ণ নিখুঁত এবং ব্যবসার জন্য শতভাগ প্রস্তুত।"
        verdict_en = "All business requirements verified. Fully ready for enterprise finalization."

    return {
        "status": readiness_status,
        "verdict_bn": verdict_bn,
        "verdict_en": verdict_en,
        "counts": {
            "critical": crit_count,
            "high": high_count,
            "medium": med_count,
            "low": low_count,
            "total": len(items),
        },
        "items": items,
    }


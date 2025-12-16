DEFAULT_PUZZLE_XP = 5

BIT_FLIPPER_LEVELS = [
    {"level": 1, "target": 10, "title": "Bit Flipper: Getting Started"},
    {"level": 2, "target": 42, "title": "Bit Flipper: A Classic"},
    {"level": 3, "target": 170, "title": "Bit Flipper: Alternating Bits"},  # 10101010
    {"level": 4, "target": 195, "title": "Bit Flipper: Edge Case"},        # 11000011
]

SELECTOR_SLEUTH_LEVELS = [
    {
        "level": 1,
        "title": "Selector Sleuth: The Basics",
        "instruction": "Select all the `<span>` elements that are inside a `<div>` with the class `box`.",
        "target_selector": "div.box span",
        "html_snippet": """<div class="container">
  <p>Some text here.</p>
  <div class="box">
    <span>Apple</span>
    <span>Banana</span>
  </div>
  <span>Orange</span>
</div>""",
    },
    {
        "level": 2,
        "title": "Selector Sleuth: Child's Play",
        "instruction": "Select only the `<li>` elements that are *direct children* of the `<ul>` with the ID `fruit-list`.",
        "target_selector": "#fruit-list > li",
        "html_snippet": """<ul id="fruit-list">
  <li>Apple</li>
  <li>Banana</li>
  <div class="nested">
    <li>Not a direct child!</li>
  </div>
  <li>Cherry</li>
</ul>""",
    },
    {
        "level": 3,
        "title": "Selector Sleuth: The Next Sibling",
        "instruction": "Select the paragraph (`<p>`) that immediately follows the `<h2>` heading.",
        "target_selector": "h2 + p",
        "html_snippet": """<div class="article">
  <h2>An Important Heading</h2>
  <p>This is the one you want.</p>
  <p>This one is not adjacent.</p>
</div>""",
    },
]

REGEX_RESCUE_LEVELS = [
    {
        "level": 1,
        "title": "Regex Rescue: The Literal",
        "instruction": "Write a regex to match the exact word 'code'.",
        "test_string": "I love to code in Python.",
        "expected_matches": ["code"],
    },
    {
        "level": 2,
        "title": "Regex Rescue: Digits",
        "instruction": "Match all numbers in the text using the digit shorthand.",
        "test_string": "Order 66 was executed at 14:00.",
        "expected_matches": ["66", "14", "00"],
    },
    {
        "level": 3,
        "title": "Regex Rescue: Character Classes",
        "instruction": "Match the words 'cat', 'bat', and 'hat'.",
        "test_string": "The cat and bat sat on a hat.",
        "expected_matches": ["cat", "bat", "hat"],
    },
]

GIT_REBASE_RESCUE_LEVELS = [
    {
        "level": 1,
        "title": "Git Rebase Rescue: Audit Trail",
        "intro": "Reorder the commits so schema changes and renames land before usage. Use squash/fixup to clean WIP noise.",
        "commits": [
            {
                "id": "schema",
                "title": "Add audit_log table",
                "details": "Creates the schema/migration the rest of the work relies on.",
                "depends": [],
            },
            {
                "id": "rename",
                "title": "Rename log_user -> record_user",
                "details": "API rename that other commits must respect.",
                "depends": ["schema"],
            },
            {
                "id": "use_helper",
                "title": "Use record_user inside auth handler",
                "details": "Switches handler to the renamed helper.",
                "depends": ["rename"],
            },
            {
                "id": "cleanup",
                "title": "Remove leftover log_user references",
                "details": "Finishes the rename so tests stop hitting the old API.",
                "depends": ["use_helper"],
            },
            {
                "id": "tests",
                "title": "Add auth audit tests",
                "details": "Covers record_user usage and flags regressions.",
                "depends": ["use_helper"],
            },
            {
                "id": "docs",
                "title": "Document audit trail format",
                "details": "Docs should land after behavior is verified.",
                "depends": ["tests"],
            },
            {
                "id": "debug",
                "title": "Debug prints for auth handler",
                "details": "Noisy commit that should be fixed up into the handler change.",
                "depends": ["use_helper"],
                "required_merge": {"type": "fixup", "target": "use_helper"},
            },
            {
                "id": "flag",
                "title": "WIP: feature flag skeleton",
                "details": "Half-done flag that should ride along with the tests.",
                "depends": ["schema"],
                "required_merge": {"type": "squash", "target": "tests"},
            },
        ],
    },
    {
        "level": 2,
        "title": "Git Rebase Rescue: Feature Freeze",
        "intro": "Stitch together a clean release branch: migrations first, renames before call sites, polish comes last.",
        "commits": [
            {
                "id": "migration",
                "title": "Add release_config migration",
                "details": "Bootstrap data for downstream commits.",
                "depends": [],
            },
            {
                "id": "rename_method",
                "title": "Rename send_email -> dispatch_email",
                "details": "API rename for the notification service.",
                "depends": [],
            },
            {
                "id": "use_rename",
                "title": "Call dispatch_email in notifications",
                "details": "Updates callers to the new API.",
                "depends": ["rename_method"],
            },
            {
                "id": "fix_tests",
                "title": "Update notification tests",
                "details": "Aligns expectations with the rename.",
                "depends": ["use_rename"],
            },
            {
                "id": "split_helpers",
                "title": "Extract EmailTemplate helper",
                "details": "Refactor that prepares for wiring",
                "depends": ["migration"],
            },
            {
                "id": "wire_helper",
                "title": "Use EmailTemplate helper",
                "details": "Swaps call sites to the new helper.",
                "depends": ["split_helpers", "use_rename"],
            },
            {
                "id": "cleanup_debug",
                "title": "Remove debug prints",
                "details": "Should be fixed up into the helper wiring.",
                "depends": ["wire_helper"],
                "required_merge": {"type": "fixup", "target": "wire_helper"},
            },
            {
                "id": "draft_docs",
                "title": "Copy/paste doc draft",
                "details": "Messy draft that should be squashed into the test update.",
                "depends": ["fix_tests"],
                "required_merge": {"type": "squash", "target": "fix_tests"},
            },
            {
                "id": "final_docs",
                "title": "Document release_config flag",
                "details": "Docs ship after code and tests settle.",
                "depends": ["migration", "fix_tests"],
            },
        ],
    },
]

BIG_O_BISTRO_LEVELS = [
    {
        "level": 1,
        "title": "Big-O Bistro: Pantry Rush",
        "scenario": "The pantry labels list can be 8k items long and the current duplicate check uses nested loops. The kitchen tablet times out at ~120ms.",
        "goal": "Pick the smallest change that guarantees correctness while dropping the worst-case time.",
        "constraints": {"n": 8000, "limit_ms": 120},
        "function_snippet": """def has_duplicate(labels):
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            if labels[i] == labels[j]:
                return True
    return False
""",
        "hidden_cases": [
            "Other stations reuse `labels` later and expect its original order to stay intact.",
            "Input can already be unique; we still need the worst-case path to be fast.",
        ],
        "best_option": "set_tracking",
        "options": [
            {
                "id": "set_tracking",
                "label": "Swap nested loops for a `set` of seen labels",
                "kind": "data structure swap",
                "big_o": "O(n)",
                "result": "best",
                "speed_gain": "n^2 -> n with one pass",
                "explanation": "Track seen labels in a set and bail on the first repeat. Order is untouched and the worst case scales linearly.",
            },
            {
                "id": "sort_in_place",
                "label": "Sort labels in-place, then scan neighbors",
                "kind": "sorting tradeoff",
                "big_o": "O(n log n)",
                "result": "fail",
                "fail_reason": "Sorting in-place mutates the list. Hidden tests expect the original order for later steps.",
                "explanation": "Sorting plus neighbor scan lowers comparisons, but the mutation breaks callers and adds log n cost.",
            },
            {
                "id": "early_cutoff",
                "label": "Only scan the first 3k labels to stay under the limit",
                "kind": "shortcut",
                "big_o": "O(k^2) on a prefix",
                "result": "fail",
                "fail_reason": "Skips tail data, so duplicates beyond 3k slip through.",
                "explanation": "Time improves by ignoring work, but correctness collapses on long inputs.",
            },
        ],
    },
    {
        "level": 2,
        "title": "Big-O Bistro: Line Cook Cache",
        "scenario": "Every minute, a batch request asks for counts of up to 200 ingredients across 20k orders. The function rescans the orders list for every query.",
        "goal": "Avoid rework while staying correct if orders change between requests.",
        "constraints": {"n": 20000, "q": 200, "limit_ms": 140},
        "function_snippet": """def top_counts(orders, requested):
    totals = []
    for item in requested:
        count = 0
        for order in orders:
            if order == item:
                count += 1
        totals.append((item, count))
    totals.sort(key=lambda x: x[1], reverse=True)
    return totals[:3]
""",
        "hidden_cases": [
            "New online orders can appear between calls; cached results must notice.",
            "Some batches repeat identical `requested` lists and should not rescan everything.",
        ],
        "best_option": "precompute_counts",
        "options": [
            {
                "id": "precompute_counts",
                "label": "Build a dict of counts once, then answer every query from it",
                "kind": "precomputation",
                "big_o": "O(n + q)",
                "result": "best",
                "speed_gain": "n*q -> n + q",
                "explanation": "One pass to tally orders, O(1) lookups per ingredient, and no stale data because it recomputes when orders change.",
            },
            {
                "id": "global_cache",
                "label": "Cache the last result and always return it if queries match",
                "kind": "caching",
                "big_o": "O(1) after first run",
                "result": "fail",
                "fail_reason": "Ignores that `orders` mutate. Hidden tests append new orders and expect updated counts.",
                "explanation": "Great for identical inputs, but without invalidation the cache serves stale totals.",
            },
            {
                "id": "sort_then_search",
                "label": "Sort orders once, then binary-search ranges per item",
                "kind": "sorting tradeoff",
                "big_o": "O(n log n + q log n)",
                "result": "ok",
                "almost_reason": "Correct and faster than n\u00d7q, but still slower than a hash map and adds sorting overhead every minute.",
                "explanation": "Binary searching sorted data is fine, yet it burns log n and still walks q times.",
            },
        ],
    },
    {
        "level": 3,
        "title": "Big-O Bistro: Plating Order",
        "scenario": "Servers send a 12k-item ticket stream with repeats. We need the first occurrence of each dish in arrival order for expo screens.",
        "goal": "Drop duplicates fast without scrambling the original arrival order.",
        "constraints": {"n": 12000, "limit_ms": 200},
        "function_snippet": """def unique_lineup(dishes):
    unique = []
    for dish in dishes:
        if dish not in unique:
            unique.append(dish)
    return unique
""",
        "hidden_cases": [
            "Expo screens rely on first-seen order; any sorting or set that reorders will fail.",
            "Long streaks of repeats mean `dish not in unique` must stay O(1).",
        ],
        "best_option": "ordered_dict",
        "options": [
            {
                "id": "ordered_dict",
                "label": "Use dict.fromkeys to dedupe while preserving order",
                "kind": "data structure swap",
                "big_o": "O(n)",
                "result": "best",
                "speed_gain": "n^2 membership -> n with ordered hashing",
                "explanation": "Python dicts keep insertion order, so you dedupe in one pass and keep the first appearance intact.",
            },
            {
                "id": "plain_set",
                "label": "Cast to a set to drop repeats",
                "kind": "data structure swap",
                "big_o": "O(n)",
                "result": "fail",
                "fail_reason": "Sets are unordered; hidden tests compare against the original arrival order.",
                "explanation": "Time is great, but order is destroyed so correctness fails.",
            },
            {
                "id": "sort_and_unique",
                "label": "Sort dishes then walk once to dedupe",
                "kind": "sorting tradeoff",
                "big_o": "O(n log n)",
                "result": "fail",
                "fail_reason": "Sorting reorders arrivals and the hidden cases reject it.",
                "explanation": "Even though it removes repeats quickly, it violates the order contract and adds log n time.",
            },
        ],
    },
]

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

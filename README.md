# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> The Unit 3 tools and planning loop are implemented. Run the checks below after
> activating the project's virtual environment:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> The last command uses the configured model for outfit advice and its caption.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr takes a natural-language request for a secondhand clothing item and
searches the local listings by description, optional size, and maximum price.
When it finds a match, it suggests an outfit using the user's wardrobe and
creates a short fit-card caption. If there are no matches, it explains which
part of the request the user can broaden and stops before calling the model.

## Data Read

`python app.py fields` showed these listing fields: `id` (str), `title` (str),
`description` (str), `category` (str), `style_tags` (list), `size` (str),
`condition` (str), `price` (float), `colors` (list), `brand` (str or null),
and `platform` (str). The first six full records confirmed that sizes have
different formats (`W30 L30`, `S/M`, `XL (oversized)`, `M`, `W28`, and `L`),
and that some brands are null.

The wardrobe is a dict with an `items` list. Each item has `id`, `name`,
`category`, `colors`, `style_tags`, and optional `notes`; the empty wardrobe is
`{"items": []}`.

The six records read with `python app.py listings --full -n 6` were:

| ID | Listing | Category | Size | Price |
|---|---|---|---|---:|
| `lst_001` | Vintage Levi's 501 Jeans — Medium Wash | bottoms | W30 L30 | $38 |
| `lst_002` | Y2K Baby Tee — Butterfly Print | tops | S/M | $18 |
| `lst_003` | Oversized Flannel Shirt — Plaid Red/Black | tops | XL (oversized) | $22 |
| `lst_004` | 90s Track Jacket — Navy/White Stripe | outerwear | M | $45 |
| `lst_005` | Corduroy Wide-Leg Pants — Rust | bottoms | W28 | $32 |
| `lst_006` | Graphic Tee — 2003 Tour Bootleg Style | tops | L | $24 |

`python app.py examples` listed five queries intended to find results and the
impossible query `designer ballgown size XXS under $5` for the empty-search
branch.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Loads the local listings, filters by an optional size and
     inclusive maximum price, then ranks matching records by description keyword
     overlap across title, description, style tags, category, colors, and brand.
- **Inputs:** `description` (`str`, required); `size` (`str | None`, optional);
     `max_price` (`float | None`, optional).
- **Returns:** Up to `config.SEARCH_RESULT_LIMIT` original listing dicts in
     descending keyword-score order, retaining source order for ties. Each dict has
     `id` (`str`), `title` (`str`), `description` (`str`), `category` (`str`),
     `style_tags` (`list[str]`), `size` (`str`), `condition` (`str`), `price`
     (`float`), `colors` (`list[str]`), `brand` (`str | None`), and `platform`
     (`str`). Size comparison is case-insensitive and token-bounded (`M` matches
     `S/M`, but not `XL`); price is inclusive.
- **When it has nothing:** Returns `[]` if there are no description tokens or
     no listings satisfy both the keyword and supplied filters; it does not return
     `None` or raise for no matches.

**Spec check:** Could someone build this from these details without asking me?
Yes: the data fields, optional filters, matching rule, ranking, tie behavior,
limit, and empty result are specified.

### `suggest_outfit`

- **What it does:** Uses the model to suggest one or two outfits around a found
     listing, naming pieces from the user's wardrobe when it is non-empty.
- **Inputs:** `new_item` (`dict` with the listing fields defined above);
     `wardrobe` (`dict` with `items: list[dict]`, each item containing `id`
     (`str`), `name` (`str`), `category` (`str`), `colors` (`list[str]`),
     `style_tags` (`list[str]`), and optional `notes` (`str | None`)).
- **Returns:** A non-empty `str` of outfit advice. With wardrobe items, the
     prompt asks for named combinations using those items; without them, it asks
     for two practical ideas using common pieces and no claim of closet ownership.
- **When it has nothing:** An empty model response becomes
     `"Try pairing the item with simple neutral basics and comfortable shoes."`.
     A provider failure raises `ModelUnavailable`; `run_agent` records its message
     in `session["error"]` and stops.

**Spec check:** Could someone build this from these details without asking me?
Yes: both dictionary shapes, the empty-wardrobe behavior, output type, empty
response fallback, and provider-failure path are stated.

### `create_fit_card`

- **What it does:** Uses the model to write a post-ready caption from an outfit
     suggestion and listing, prompting it to mention the title, price, and platform
     once each and describe the vibe in two to four sentences.
- **Inputs:** `outfit` (`str`); `new_item` (`dict` with the listing fields
     defined above).
- **Returns:** A non-empty `str` containing the model's caption when the model
     responds; if the model returns empty text, returns a two-sentence fallback
     naming the item, price, platform, and outfit.
- **When it has nothing:** If `outfit` is empty or whitespace, returns
     `Found {title}, listed for ${price} on {platform}. Add an outfit idea to turn
     it into a look.` using the listing values (or the defaults in `tools.py`),
     without calling the model. Provider failures raise `ModelUnavailable` and are
     recorded by `run_agent`.

**Spec check:** Could someone build this from these details without asking me?
Yes: the inputs, caption requirements, blank-outfit response, empty-model
fallback, and provider-failure behavior are specified.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a helpful
message in the session and stop. Otherwise, take the first result and go to
`suggest_outfit`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regular expressions extract a `size ...` phrase
and a price ceiling introduced by `under`, `below`, `less than`, `at most`,
`up to`, or `max`. The remaining words form the search description.

**What moves through the session:** `query` becomes `parsed`; the returned
listings go into `search_results`; the first listing becomes `selected_item`
and is passed with `wardrobe` to `suggest_outfit`; its result becomes
`outfit_suggestion` and is passed with that same item to `create_fit_card`;
the final string is stored in `fit_card`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'
The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
1 model calls this session
```

The CLI search ran, but the live model rejected the configured key before the
outfit and fit-card tools completed. I did not include the key in this README.
The starting stub message cannot be re-run now because `agent.py::run_agent` has
since been implemented.

**Offline end-to-end control-flow check**

```
$ python -c "import agent; from utils.data_loader import get_example_wardrobe; agent.suggest_outfit=lambda item, wardrobe: 'Mock outfit: pair it with your white ribbed tank and black denim jacket.'; agent.create_fit_card=lambda outfit, item: 'Mock caption: A vintage tee with an easy streetwear feel. Styled with denim for a relaxed weekend look.'; result=agent.run_agent('vintage graphic tee under \$30', get_example_wardrobe()); print(result['selected_item']['title']); print(result['outfit_suggestion']); print(result['fit_card'])"
Y2K Baby Tee — Butterfly Print
Mock outfit: pair it with your white ribbed tank and black denim jacket.
Mock caption: A vintage tee with an easy streetwear feel. Styled with denim for a relaxed weekend look.
```

This end-to-end smoke run replaces the two model-backed tools with fixed test
responses; it verifies local control flow, not live model quality.

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('90s track jacket', size='M', max_price=50)[0])"
{'id': 'lst_004', 'title': '90s Track Jacket — Navy/White Stripe', 'description': 'Authentic 90s track jacket with stripe detail down the sleeves. Full zip. Lightweight — great for layering.', 'category': 'outerwear', 'style_tags': ['90s', 'vintage', 'athletic', 'streetwear'], 'size': 'M', 'condition': 'excellent', 'price': 45.0, 'colors': ['navy', 'white'], 'brand': 'Champion', 'platform': 'poshmark'}
```

```
$ python -c "from tools import search_listings, suggest_outfit; from utils.data_loader import get_empty_wardrobe; from generate import ModelUnavailable; item=search_listings('90s track jacket', size='M', max_price=50)[0]; exec('try:\n print(suggest_outfit(item, get_empty_wardrobe()))\nexcept ModelUnavailable as error:\n print(error)')"
The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
```

```
$ python -c "from tools import search_listings, create_fit_card; from generate import ModelUnavailable; item=search_listings('90s track jacket', size='M', max_price=50)[0]; outfit='Style it with black jeans and white sneakers.'; results=[]; exec('for attempt in range(3):\n try:\n  results.append(create_fit_card(outfit, item))\n except ModelUnavailable as error:\n  results.append(str(error))'); print('\\n---\\n'.join(results))"
The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
---
The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
---
The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
```

The search command succeeds and shows the size and price filters in use. The
outfit and caption commands call the real model adapter but cannot return model
text until `GEMINI_API_KEY` in `.env` is replaced with a valid key. The three
caption attempts therefore do not establish whether model captions vary. In
`config.py`, `CACHE_ENABLED` is on and `TEMPERATURE` is `0.9`; rerun the three
attempts after fixing the key to evaluate the caption output.

**Session handoff and empty-search checks**

The happy-path run used fixed local responses for the two model-backed tools,
printed the complete session with `pprint(session)`, and checked object identity
at the outfit-tool boundary:

```text
suggest_outfit received the exact selected item: True
selected_item: lst_002 — Y2K Baby Tee — Butterfly Print
outfit_suggestion: Pair it with dark jeans and white sneakers.
fit_card: A vintage tee styled for an easy weekend.
error: None
```

For `designer ballgown size XXS`, local search returned `[]`; the loop did not
call the model-backed tools:

```text
error: No listings matched that request. Try a broader item description, a size from the listings, or a higher price ceiling.
selected_item: None
outfit_suggestion: None
fit_card: None
```

---

## How I Used AI

<!-- Record your own prompts and edits before submission. The entries below
     describe the assistance used during this implementation; revise them so
     they accurately reflect your process. -->

**Moment 1**

- *What I asked for:* I asked Copilot to implement the search contract against
     the provided listing data.
- *What came back:* It proposed local keyword scoring with size and price
     filters instead of sending search to the model.
- *What I changed:* I checked the actual `S/M` and `XL` size formats and kept
     size matching token-aware so a small size cannot match `XL` accidentally.

**Moment 2**

- *What I asked for:* I asked Copilot to connect the tools through a session
     with the required empty-search branch.
- *What came back:* It proposed a staged loop that stores each tool result and
     stops before outfit generation when search is empty.
- *What I changed:* I checked the flow using test doubles and verified that the
     exact selected listing reaches `suggest_outfit`, while the no-results path
     leaves the later fields unset.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**

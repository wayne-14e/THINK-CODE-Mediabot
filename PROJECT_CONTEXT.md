# PROJECT_CONTEXT.md — THINK//CODE AI Content Bot (single source of truth)

## 1. What this is
Telegram-first AI content assistant. Founders decide what/when; AI drafts ready-to-publish
posts in the exact THINK//CODE terminal voice, learned from `ChatExport_2026-09-16/`.
MVP: Telegram admin bot + approval + scheduling. Discord = V2 (copy-adapt only).

## 2. Backend (Firebase — created 2026-09-16)
- Firebase project: `think-code-mediabot` (#2228267746), Firestore `(default)` in `europe-west1` (Belgium)
- Access: Admin SDK only (service account). `firestore.rules` = deny-all for clients.
- Collections: `posts | ideas | style_profile | content_schedule | generation_runs | admin_users`
- Local config: `firebase.json`, `firestore.rules`, `firestore.indexes.json`, `.firebaserc`

## 3. Repo structure
```
bot/
  main.py          # aiogram polling entry (python -m bot.main)
  config.py        # env-only settings (GEMINI_MODEL configurable, default gemini-3.5-flash-lite)
  db.py            # Firestore wrapper (posts/ideas/style/schedule/runs)
  ai.py            # pipeline: ideas -> generate -> exec-validate -> LLM-validate (3 retries)
  scheduler.py     # APScheduler daily publish of `scheduled` posts at DEFAULT_PUBLISH_TIME
  handlers/
    admin.py       # /start /schedule /today /generate /ideas /history /style /settings + gen callbacks
    approval.py    # preview KB: Approve / Regenerate / Edit(FSM) / Reject / Approve&Schedule; publishes post+poll
data/
  style_profile.json          # hand-derived from channel history (headers, $ vars, quiz/solution/workshop structures)
  channel_history.json        # generated: 42 items parsed from ChatExport_2026-09-16/messages.html
  prompts/generate.txt        # JSON-only generator prompt (style + recent posts + anti-repetition)
  prompts/validate.txt        # validator prompt (answer==exec_result, style, factual)
  prompts/ideas.txt           # exactly-2-ideas prompt
scripts/
  ingest_history.py           # parse export -> channel_history.json; --upload seeds Firestore
requirements.txt  # aiogram3, google-genai, firebase-admin, APScheduler, dotenv, bs4
.env.example      # TELEGRAM_* / GEMINI_* / FIREBASE_* / publish time template
```

## 4. Style profile (from 42 parsed posts, 13.08–14.09.2026)
- Headers `> UPPER` (QUIZ_02, SOLUTION, SYSTEM_UPDATE, WORKSHOP_01, WHY?, WHAT_IS_THE_OUTPUT?);
  vars `$ lower_snake:` (execute_the_code, correct_output, key_idea, think_before_you_run_, status).
- Quiz = post (`> QUIZ_NN → LANGUAGE → $ execute → code → > WHAT_IS_THE_OUTPUT? → CTA`) + poll
  (`$ ANSWER_REQUIRED:` 4 options) ; solution next day (`$ CORRECT_OUTPUT: → stats → > WHY? trace →
  `$ KEY_IDEA:` rule → `> THINK_BEFORE_YOU_RUN 🧠`).
- Tone friendly-nerdy-concise, terminal persona; emoji signature 🐍👾⚡🔥🧠👀🤯🏆📍💻🍿;
  short lines, ASCII diagrams ok; no hashtags; EN primary (+RU jokes/workshops).
- Workshop flow: announcement → `$ SELECT_TIME:` poll (19/20/21:00) → `$ DECISION: → ✅` →
  countdown → `WE_ARE_STARTING` → attendance log. Evenings UTC+5 most active.

## 5. AI pipeline
`style_profile + recent posts (Firestore, fallback local JSON)` → `suggest_ideas(2)` →
`generate_post(type/lang/diff)` → local `py -c` exec ground truth for python quizzes →
Gemini validator (pass/issues/fix) → up to 3 retries → save `pending_review` post +
`generation_runs` log. Model IDs env-configurable (`GEMINI_MODEL`, `GEMINI_VALIDATOR_MODEL`).

## 6. Telegram UX (admin-only via TELEGRAM_ADMIN_IDS)
Review happens in the admin group (`TELEGRAM_REVIEW_GROUP_ID`), NEVER in DMs or the channel.
`/generate` (DM or group) → preview card + Approve/Regenerate/Edit/Reject/Schedule keyboard
lands in the review group (`send_preview()` in approval.py; regen + edited previews too).
Approval clicks work in the group (admin-id checked); Approve publishes content msg + poll msg to
`TELEGRAM_CHANNEL_ID`; schedule = mark `scheduled`, APScheduler cron publishes daily + notifies
review group. No review group set → fallback to old in-place DM preview.
`/start /today /generate <type> [lang] [diff] /ideas /schedule /history /style /settings`;
inline `gen:` / `ideas:refresh`. Bot must be admin of the review group.
Update 2026-09-16: standalone ✓ Approve button REMOVED (died silently on channel errors),
then ✓ Approve & Schedule + the whole scheduler REMOVED too — founder posts manually.
Cards carry Regenerate / Reject only (Approve, Approve & Schedule, Edit all removed —
founder edits the copy when posting). `bot/scheduler.py` kept but unwired.
`/schedule` + `/today` remain as planning info only (what type to generate).

## 6b. Formatting (founder-set)
Telegram HTML via `bot/format.py::to_telegram_html`: `<b>` titles, `<blockquote>` important
text, `<pre>` code. NEVER italic/underline/strikethrough. Bot runs parse_mode=HTML; all
generated/edited outgoing text passes the sanitizer (fences→pre, **→b, banned tags stripped,
stray <>& escaped, LLM pre-escaped entities normalized via unescape-first, all > / $ header
lines auto-bold outside code). Generator prompt + validator enforce the same rules.
Preview cards append a review-only POLL_PREVIEW — each option's text in its own <pre>
(letter outside, one-tap copy per option) + $ CORRECT letter + explanation in <pre>.
Bot UI messages (/start /today /ideas /schedule /history /style /settings, statuses)
all pass the same sanitizer: > headings and $ lines bold; POLL_PREVIEW options live in
one <pre> monospace block for one-tap copy.

## 7. How to run (dev)
1. `py -m venv .venv` + install `requirements.txt`
2. copy `.env.example` → `.env`, fill TELEGRAM_BOT_TOKEN, GEMINI_API_KEY, TELEGRAM_ADMIN_IDS
3. service account: `firebase projects:create` done; get JSON via Firebase Console →
   save as `service-account.json` (or `FIREBASE_SERVICE_ACCOUNT_JSON`), keep `FIREBASE_PROJECT_ID=think-code-mediabot`
4. `py scripts/ingest_history.py` (regenerate local JSON); `--upload` to seed Firestore
5. `py -m bot.main` (polling; keep running for scheduler)

## 8. Status / next
- DONE: Firebase project + Firestore init, full bot scaffold, style profile, prompts,
  ingestion (42 items), approval+schedule flow, validation with code exec.
- TODO (needs founder): secrets (.env + service-account.json), `@BotFather` token,
  channel admin rights, `GEMINI_API_KEY` (AI Studio), test `/generate quiz python medium`
  end-to-end, `firebase deploy --only firestore:rules`. V2: Discord mirror, image briefs→gen, web dashboard.

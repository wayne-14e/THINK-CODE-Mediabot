# THINK//CODE AI Content Bot --- IDEA

## 1. Overview

**THINK//CODE AI Content Bot** is a Telegram-first content assistant
that generates ready-to-publish posts for the THINK//CODE coding
community.

The goal is simple:

> The founders decide **what and when to publish**.\
> The AI handles the repetitive work of **creating the post**.

The bot should learn the community's existing writing style, formatting
conventions, recurring content formats, and tone from the channel
history. Founders then review and approve generated content before
publication.

The system should initially focus on **Telegram**, while producing
content that can also be copied to the THINK//CODE Discord server.

------------------------------------------------------------------------

## 2. Core Workflow

### Daily content

1.  Founder creates or reviews a content schedule.
2.  The bot knows what type of post is planned for the day.
3.  AI generates a complete ready-to-publish post.
4.  If the format requires an image, the bot can provide an image
    brief/prompt or attach a generated visual in a later phase.
5.  Founder sees a preview.
6.  Founder can:
    -   Approve
    -   Regenerate
    -   Edit
    -   Reject
7.  Approved content is scheduled/published automatically.

### Example

``` text
Monday    → Python Quiz
Tuesday   → IT Fact
Wednesday → Meme / Community Post
Thursday  → Python Quiz
Friday    → Interesting Programming Topic
Sunday    → Workshop / Community Update
```

The exact schedule should be configurable.

------------------------------------------------------------------------

# 3. Main Features

## 3.1 Channel History Ingestion

The founder should be able to provide the bot with the existing
THINK//CODE channel history.

The system extracts useful information such as:

-   Post text
-   Formatting
-   Recurring headers
-   Emoji usage
-   Tone
-   Post length
-   Quiz structure
-   Solution structure
-   Common terminology
-   CTA patterns
-   Image descriptions when available
-   Poll structure
-   Workshop announcement structure

The AI should not simply memorize individual posts. It should build a
reusable **THINK//CODE Style Profile**.

### Style Profile

Example:

``` json
{
  "tone": "friendly, nerdy, concise",
  "language": "English",
  "format": "terminal-inspired",
  "preferred_length": "short",
  "emoji_usage": "moderate",
  "quiz_structure": "header → language → difficulty → code → options → CTA",
  "solution_structure": "answer → short explanation → key idea",
  "visual_style": "dark terminal / lime accent",
  "audience": "beginner to intermediate developers"
}
```

The founder should be able to manually edit this profile.

------------------------------------------------------------------------

# 4. Content Types

The MVP should support several predefined content types.

## 4.1 Quiz

The AI generates:

-   Programming language
-   Difficulty
-   Question/code
-   4 answer choices
-   Correct answer
-   Explanation
-   Solution post
-   Optional bonus question

Example:

``` text
Python
Medium
Question
A/B/C/D
```

### Important

The AI must validate the quiz before showing it to the founder.

For programming questions, it should reason through the code and verify:

-   Correct output
-   Edge cases
-   Syntax
-   Answer uniqueness
-   Difficulty
-   Explanation

A quiz with an incorrect answer should never reach the approval screen.

------------------------------------------------------------------------

## 4.2 IT Fact

Generate short, interesting facts about:

-   Programming
-   Computer history
-   AI
-   Internet
-   Cybersecurity
-   Software
-   Hardware
-   Algorithms

The bot should prioritize facts that are genuinely interesting rather
than generic trivia.

------------------------------------------------------------------------

## 4.3 Meme / Funny Post

Generate short programming-related jokes, situations, developer
confessions, polls, or humorous posts.

Examples:

-   Debugging
-   Stack Overflow
-   Git
-   Python
-   C++
-   Bugs
-   "It works on my machine"
-   Developer habits
-   Hackathons

The humor should remain understandable to the target audience.

------------------------------------------------------------------------

## 4.4 Interesting Topic

Generate short posts around a programming/IT concept.

Examples:

-   Why `0.1 + 0.2 != 0.3`
-   How DNS works
-   Why Git was created
-   How early computers generated speech
-   Weird programming languages
-   Famous bugs
-   Hidden programming history

------------------------------------------------------------------------

## 4.5 Community Post

Generate posts designed specifically to get reactions or comments.

Examples:

-   Polls
-   Coding preferences
-   "What did you learn today?"
-   Developer confessions
-   Favorite languages
-   Workshop announcements
-   Community questions

------------------------------------------------------------------------

## 4.6 Workshop Post

Generate:

-   Workshop announcement
-   Time poll
-   15-minute reminder
-   Start-now reminder
-   Post-workshop thank-you
-   Workshop recap

The bot should remember the workshop's recurring structure.

------------------------------------------------------------------------

# 5. Content Suggestions

When the founder doesn't know what to post, the bot should provide
**exactly two suggestions** by default.

Example:

``` text
TODAY'S CONTENT IDEAS

1. Weird Python Behavior
   A medium quiz about mutable default arguments.

2. The Bug That Cost Millions
   A short story about a famous software failure.

[Generate #1]
[Generate #2]
[Give me different ideas]
```

Suggestions should consider:

-   Recent posts
-   Content already published
-   Recent topics
-   Content type balance
-   Audience level
-   Previous successful posts
-   Upcoming events
-   Avoiding repetition

------------------------------------------------------------------------

# 6. Content Calendar

The founder should be able to define a simple weekly schedule.

Example:

``` text
MONDAY     Quiz
TUESDAY    Interesting Fact
WEDNESDAY  Meme
THURSDAY   Quiz
FRIDAY     Interesting Topic
SATURDAY   Community
SUNDAY     Workshop
```

The schedule should be editable.

The bot should track:

``` text
Last published:
Quiz → yesterday
Meme → 3 days ago
Fact → 5 days ago

Next:
Quiz
```

This prevents the AI from repeatedly generating the same type of
content.

------------------------------------------------------------------------

# 7. Approval System

**Nothing should be published automatically without founder approval in
the MVP.**

Every generated post should have an approval interface.

Example:

``` text
┌─────────────────────────────┐
│ QUIZ_07                     │
│                             │
│ > THINK//CODE / QUIZ_07     │
│                             │
│ ...generated post...        │
│                             │
└─────────────────────────────┘

[ ✓ APPROVE ]
[ ↻ REGENERATE ]
[ ✎ EDIT ]
[ ✕ REJECT ]
```

Approval is the central safety mechanism.

------------------------------------------------------------------------

# 8. One-Click Publishing

After approval:

``` text
[ ✓ APPROVE & SCHEDULE ]
```

The bot should:

1.  Save the final post.
2.  Schedule it.
3.  Publish it to Telegram at the selected time.
4.  Optionally mirror it to Discord.

The founder should not need to copy/paste the post manually.

------------------------------------------------------------------------

# 9. Telegram Integration

The bot should support:

-   Telegram Bot API
-   Channel publishing
-   Scheduled publishing
-   Poll creation
-   Image attachments
-   Post editing
-   Draft management
-   Admin-only controls

Only authorized THINK//CODE founders should be able to generate,
approve, schedule, or publish content.

------------------------------------------------------------------------

# 10. Discord Integration

Discord should initially be treated as a **secondary publishing
destination**.

After approving a Telegram post:

``` text
Publish to:

☑ Telegram
☑ Discord
```

The bot should adapt formatting where necessary instead of blindly
copying Telegram formatting.

For example:

-   Telegram post → terminal-style formatting
-   Discord post → Markdown-compatible formatting

------------------------------------------------------------------------

# 11. AI Architecture

## Primary model

Use **Gemini Flash** models.

Recommended production baseline:

``` text
gemini-3.8-flash
```

Gemini 3.8 Flash is currently a stable GA model and supports a 1M-token
context window, structured outputs, function calling, caching, file
search, and adjustable thinking levels. citeturn0search0turn0search1

Use:

``` text
gemini-3.8-flash
```

for the main content-generation workflow.

Use lower-cost/previous Flash models when appropriate for lightweight
tasks:

``` text
gemini-3.6-flash
```

Gemini 3.6 Flash is also a stable model and was specifically released
with improved token efficiency and coding/agentic planning at lower
cost. citeturn0search2turn0search8

The model ID should be configurable through environment variables rather
than hard-coded.

------------------------------------------------------------------------

# 12. AI Pipeline

Do not use one enormous prompt for everything.

Use a pipeline.

``` text
CHANNEL HISTORY
       ↓
STYLE ANALYSIS
       ↓
CONTENT MEMORY
       ↓
CONTENT IDEA
       ↓
POST GENERATION
       ↓
VALIDATION
       ↓
FOUNDER REVIEW
       ↓
SCHEDULE
       ↓
TELEGRAM / DISCORD
```

------------------------------------------------------------------------

# 13. Style Learning

The system should have two kinds of memory.

## Static style memory

Things that rarely change:

-   Brand tone
-   Formatting
-   Visual identity
-   Audience
-   Language
-   Preferred post length
-   Content philosophy

## Dynamic content memory

Things that change:

-   Recently published posts
-   Recent topics
-   Quiz answers
-   Content types
-   Upcoming workshops
-   Community reactions
-   Previously rejected ideas

This prevents the AI from generating the same post repeatedly.

------------------------------------------------------------------------

# 14. Content Database

Suggested entities:

### `posts`

``` text
id
content
content_type
language
difficulty
status
scheduled_at
published_at
telegram_message_id
discord_message_id
created_at
```

### `ideas`

``` text
id
title
description
content_type
status
created_at
```

### `style_profile`

``` text
id
tone
format_rules
emoji_rules
language_rules
visual_rules
audience_description
updated_at
```

### `content_schedule`

``` text
id
weekday
content_type
preferred_time
enabled
```

### `generation_runs`

``` text
id
post_id
model
prompt_version
input_tokens
output_tokens
created_at
```

------------------------------------------------------------------------

# 15. Validation Layer

The AI should have a separate validation step.

For example:

``` text
GENERATOR
   ↓
VALIDATOR
   ↓
PASS ─────────→ Founder
   │
   └── FAIL → regenerate
```

For quizzes, validate:

-   Correct answer
-   Code correctness
-   Syntax
-   No ambiguous options
-   Explanation correctness
-   Difficulty
-   No accidental duplicate answers

For facts:

-   Factual consistency
-   No unsupported claims
-   Avoid fabricated statistics

For all content:

-   Match THINK//CODE style
-   Not too long
-   No repetitive phrasing
-   No inappropriate content
-   No accidental references to previous private conversations

------------------------------------------------------------------------

# 16. Image Generation

### MVP

Do not make image generation mandatory.

For posts that need an image, generate an **image brief**:

``` text
IMAGE_BRIEF

Canvas: 1280x720
Style: dark terminal
Background: #0B0D10
Accent: #A3FF12
Typography: monospace
Main subject: ...
Text: ...
```

The founder can create the visual manually.

### Later

Add image generation using a suitable image model/API.

The bot could eventually produce:

``` text
POST
+
IMAGE
+
POLL
```

as one complete package.

------------------------------------------------------------------------

# 17. Admin Interface

The first interface can simply be **Telegram itself**.

Possible commands:

``` text
/start
/schedule
/today
/generate
/ideas
/history
/style
/settings
```

Example:

``` text
/generate quiz python medium
```

Bot:

``` text
Generated QUIZ_07

[Preview]

[✓ Approve]
[↻ Regenerate]
[✎ Edit]
[✕ Reject]
```

Later, a small web dashboard can replace/augment the Telegram admin
interface.

------------------------------------------------------------------------

# 18. Suggested Tech Stack

## Backend

**Python**

Reason:

-   Excellent Telegram ecosystem
-   Easy Gemini API integration
-   Fast development
-   Good AI tooling
-   Easy scheduling/background jobs

## Telegram

**aiogram 3.x**

For:

-   Commands
-   Inline keyboards
-   Channel publishing
-   Admin workflow

## AI

**Google Gemini API**

Primary:

``` text
gemini-3.8-flash
```

Secondary:

``` text
gemini-3.6-flash
```

Google's current Gemini API supports both standard `generateContent` and
the newer Interactions API; the Interactions API is positioned as the
recommended primitive for stateful/agentic workflows.
citeturn0search6turn0search9

For this relatively deterministic content workflow, start with
`generateContent` or the current Google GenAI SDK and move to
Interactions API only if stateful multi-turn workflows become useful.

## Database

**Supabase / PostgreSQL**

Use it for:

-   Posts
-   Ideas
-   Schedule
-   Style profile
-   Generation history
-   Admin users
-   Analytics

## Scheduler

For MVP:

**APScheduler**

Later:

-   Celery + Redis
-   Supabase scheduled jobs
-   Cloud task system

depending on deployment requirements.

## Hosting

Possible:

-   Railway
-   Render
-   Fly.io
-   VPS
-   Google Cloud Run

Start with whichever is simplest and inexpensive.

------------------------------------------------------------------------

# 19. Security

The bot must never expose:

-   Gemini API key
-   Telegram bot token
-   Supabase credentials
-   Admin credentials

Use environment variables/secrets.

Example:

``` env
GEMINI_API_KEY=
TELEGRAM_BOT_TOKEN=
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
```

Only explicitly authorized Telegram user IDs should have admin access.

Every publishing action should be logged.

------------------------------------------------------------------------

# 20. MVP Scope

The first version should **not** try to do everything.

### MVP

``` text
✓ Telegram bot
✓ Admin-only access
✓ Weekly schedule
✓ Channel history import
✓ Style profile
✓ Quiz generation
✓ Fact generation
✓ Meme/community generation
✓ 2 idea suggestions
✓ Post preview
✓ Approve
✓ Regenerate
✓ Edit
✓ Schedule
✓ Telegram publishing
✓ Generation history
✓ Basic validation
```

### V2

``` text
+ Discord publishing
+ Automatic image briefs
+ Better analytics
+ Content performance tracking
+ More content types
+ Automatic topic rotation
+ Web dashboard
```

### V3

``` text
+ Image generation
+ Performance-based content recommendations
+ Automatic A/B testing
+ Engagement-aware scheduling
+ Advanced semantic memory
+ Multi-channel adaptation
```

------------------------------------------------------------------------

# 21. Important Product Principle

The bot should **not become a generic AI content generator**.

Its job is to reproduce and extend the specific THINK//CODE identity.

Bad:

> "Here is a generic Python quiz."

Good:

> "Here is a THINK//CODE Python quiz that looks, sounds, and behaves
> like the posts the community already knows."

The channel history is therefore one of the most important inputs to the
system.

------------------------------------------------------------------------

# 22. Example End-to-End Session

``` text
BOT:

Good morning.

Today's scheduled content:
PYTHON QUIZ — MEDIUM

[Generate]

FOUNDER:
✓

BOT:

Generating...

[Post preview]

> THINK//CODE / QUIZ_07
> ...

[✓ APPROVE]
[↻ REGENERATE]
[✎ EDIT]

FOUNDER:
✓ APPROVE

BOT:

Scheduled for 18:00.

Telegram ✓
Discord ✓
```

For a non-scheduled day:

``` text
BOT:

No content selected for today.

Here are 2 ideas:

1. The Python Trap
   A medium quiz about references.

2. The Computer That Learned to Sing
   A short IT-history post.

[Generate #1]
[Generate #2]
[More ideas]
```

------------------------------------------------------------------------

# 23. Success Criteria

The bot succeeds if the founders can go from:

``` text
"I need today's post"
```

to:

``` text
"Approved and scheduled."
```

in **under 1--2 minutes**.

The ideal workflow should eventually become:

``` text
PLAN THE WEEK
      ↓
BOT GENERATES
      ↓
REVIEW
      ↓
ONE CLICK
      ↓
PUBLISHED
```

The founders should spend their time **building THINK//CODE**, not
formatting the same terminal header for the 40th time.

------------------------------------------------------------------------

# 24. Future Idea: THINK//CODE Content Intelligence

Once enough historical data exists, the bot can learn which content
performs best.

Track:

-   Views
-   Reactions
-   Poll participation
-   Comments
-   Shares/forwards
-   Workshop attendance
-   Subscriber growth after posts

Then the AI can recommend:

``` text
Based on the last 30 posts:

Python quizzes:
↑ strongest engagement

IT facts:
→ average

Memes:
↑ high reactions, low conversion

Recommendation:
Generate 2 Python quizzes this week.
```

This turns the bot from a **post generator** into a lightweight
**content strategist**.

------------------------------------------------------------------------

# 25. Final Product Definition

> **THINK//CODE AI Content Bot is an AI-powered content assistant that
> learns the community's style, generates recurring and original
> programming/IT content, validates it, gives founders two ideas when
> needed, and lets them approve and schedule finished posts in one
> click.**

The founders decide the strategy.

The AI handles the repetitive execution.

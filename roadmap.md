# Hageglede Roadmap

## Decision Preamble

This is a complete reset from any previous gardening app project. We start with zero assumptions and will only build what evidence tells us is necessary. Every phase must deliver concrete, measurable value before progressing. No technical debt is accepted.

## Phase 0: Live Discovery

**Timeframe:** 2-3 weeks
**Success Metric:** 10 completed user interviews with gardeners in our target demographic, all validating the same core problem statement
**Explicit Constraint:** ZERO lines of code written until Phase 0 is fully complete

**Purpose:** To discover through direct conversation what actual problem gardeners have that our solution should address. We have no product yet — we have only a hypothesis that gardeners struggle to choose appropriate plants.

**Core Hypothesis to Test:** "Gardeners waste time and money selecting plants that fail due to incompatible growing conditions (soil type, sunlight, space constraints)."

**Validation Method:** 10× 30-minute semi-structured interviews with gardeners who have attempted to grow something that failed. Interviews must be recorded (with consent) and transcribed.

**Exit Criteria:** When 8 out of 10 interviews independently identify the same root cause without leading questions. If not achieved, return to hypothesis formulation.

**Deliverables:**
1. Annotated interview transcripts
2. Validated problem statement
3. List of concrete user needs (not wants)
4. First-pass user personas (based on actual people interviewed)

## Phase 1: Single Recommendation Works

**Timeframe:** 3-4 weeks after Phase 0 completion
**Success Metric:** 5 real users successfully receive accurate plant recommendations and report the recommendations were helpful

**Purpose:** Prove that we can deliver useful plant recommendations using the simplest possible technology.

**Core Hypothesis:** "Given a postcode (location) and basic garden conditions, we can recommend 3-5 plants that have a high probability of thriving."

**Technical Stack:**
- Static HTML site (no build steps)
- Pico CSS for styling (no custom CSS)
- HTMX for dynamic interactions (no JavaScript frameworks)
- SQLite ONLY if absolutely necessary (prefer static CSV files)
- Deploy via GitHub Pages or similar static hosting

**Explicit NO List:**
- No JavaScript frameworks (React, Vue, etc.)
- No build steps (Webpack, Vite, etc.)
- No OAuth/authentication
- No database beyond SQLite
- No real-time features
- No ML/AI components
- No mobile app

**Features:**
1. Single-page form: postcode + soil type + sunlight hours + space available
2. Submit button → shows 3-5 plant recommendations with reason why
3. All plant data stored locally in CSV/JSON file
4. No user accounts or history
5. Printable results

**Outcome:** Working proof-of-concept that delivers value. If successful, we have validated demand for the core service.

## Phase 2: Add Persistence (if needed)

**Timeframe:** TBD based on Phase 1 findings
**Success Metric:** 20 users save and return to see their recommendations

**Purpose:** Only if Phase 1 users explicitly request saving their recommendations.

**Technical Approach:**
- Local storage first, then possibly server-side SQLite
- Email-based magic links (no passwords)
- Still no OAuth, no user databases with PII

## Out-of-Scope (Never Build)

These features are explicitly out of scope for this project. If evidence later shows they're critical, they become a separate project with separate funding.

1. **AI Chat Interface** — No conversational AI about gardening
2. **Predictive Models** — No ML forecasting of plant growth
3. **Mobile App** — No native iOS/Android apps (web only)
4. **Social Features** — No sharing, following, user profiles
5. **Marketplace** — No buying/selling plants
6. **Image Recognition** — No plant identification from photos
7. **Automated Gardening** — No IoT/sensor integrations
8. **Gamification** — No points, badges, leaderboards

## Phase 0 Kickoff Checklist

### Week 1: Preparation
- [ ] Define target demographic: Home gardeners, UK-based, mixed experience
- [ ] Create interview recruitment message (offer £10 voucher)
- [ ] Set up Calendly for scheduling
- [ ] Prepare recording/transcription tools (Otter.ai + backup)
- [ ] Write interview script template
- [ ] Create consent form template
- [ ] Set up shared folder for transcripts

### Week 2-3: Execution
- [ ] Conduct 10 interviews (2-3 per day max)
- [ ] Transcribe within 24 hours of each interview
- [ ] Annotate transcripts with observations
- [ ] Weekly synthesis session to identify patterns

### Week 4: Synthesis
- [ ] Cluster findings into themes
- [ ] Validate problem statement
- [ ] Document user needs (direct quotes)
- [ ] Create provisional personas
- [ ] Decide go/no-go for Phase 1

## Interview Script Template

**Introduction (5 mins)**
"Thanks for your time. I'm researching gardening challenges. This isn't a sales call — we're trying to understand real problems before building anything. The session will take about 30 minutes. May I record for transcription? Everything is anonymous."

**Warm-up (5 mins)**
1. Tell me about your gardening experience — how long, what types of plants?
2. What's been your biggest gardening success recently?

**Core Problem Exploration (15 mins)**
3. Think about a time you tried to grow something that didn't work out. Walk me through what happened.
4. What did you do to choose that plant in the first place?
5. When you realized it wasn't working, what did you try?
6. How much time/money do you estimate you lost?
7. If you could wave a magic wand, what would have prevented this?

**Solution Space (5 mins)**
8. Have you used any apps or websites to help with plant selection?
9. What worked well about them? What frustrated you?
10. If you could have one tool to solve this problem forever, what would it do?

**Closing (2 mins)**
11. Is there anything else I should have asked about?
12. Can I follow up with one clarifying question if needed?

**Immediate Post-Interview Notes:**
- Key quotes to highlight
- Emotional tone during problem description
- Unmet needs mentioned
- Willingness to pay/time investment indicated

---

*This document is living. Update after each phase based on evidence, not opinion.*
*Last updated: Project Start*
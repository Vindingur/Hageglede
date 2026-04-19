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

## Phase 1: Single Recommendation Works (FastAPI + SQLite + HTMVP)

**Timeframe:** 3-4 weeks after Phase 0 completion
**Success Metric:** 5 real users successfully receive accurate plant recommendations and report the recommendations were helpful

**Purpose:** Prove that we can deliver useful plant recommendations using the simplest possible backend technology.

**Core Hypothesis:** "Given a postcode (location) and basic garden conditions, we can recommend 3-5 plants that have a high probability of thriving."

**Technical Stack (Updated per ARCHITECTURE.md):**
- **Backend**: FastAPI with Python 3.11+
- **Database**: SQLite (single file, zero configuration)
- **Frontend**: Vanilla HTML/CSS with HTMX for dynamic interactions
- **Server**: Uvicorn ASGI server
- **Deployment**: Simple container or process manager (Docker optional)
- **Data**: Static datasets loaded into SQLite tables

**Explicit NO List (Updated):**
- No JavaScript frameworks (React, Vue, etc.)
- No complex build steps (simple HTML/CSS only)
- No OAuth/authentication (anonymous sessions only)
- No database beyond SQLite (no PostgreSQL, no MongoDB)
- No real-time features beyond basic API calls
- No ML/AI components
- No mobile app
- No user accounts with passwords

**Features (Updated per Architecture):**
1. Single-page form: postcode input + optional garden conditions
2. Submit button → HTMX calls `/api/climate-zone/{postcode}` endpoint
3. Backend maps postcode to climate zone using `postcode_zones` table
4. Backend queries `plant_zone_mapping` and `plants` tables for matching plants
5. Returns structured JSON with plant recommendations
6. Frontend renders plant cards with images, names, and details
7. User can save plants to localStorage (anonymous session)
8. All plant data stored in SQLite database with proper schema

**Database Schema (from ARCHITECTURE.md):**
- `climate_zones` table with zone codes and temperature ranges
- `postcode_zones` table mapping Norwegian postcodes to zones
- `plants` table with scientific names, common names, plant types
- `plant_zone_mapping` table with suitability scores and seasonal info
- `user_saved_plants` table for localStorage sync backup

**API Endpoints (Core MVP):**
- `GET /api/climate-zone/{postcode}` - Get zone for a postcode
- `GET /api/plants/zone/{zone_id}` - Get plants for a zone
- `POST /api/session` - Create anonymous session
- `GET /api/health` - Health check

**Outcome:** Working proof-of-concept that delivers value. If successful, we have validated demand for the core service and have a scalable backend foundation.

## Phase 2: Add Persistence & User Features (if needed)

**Timeframe:** TBD based on Phase 1 findings
**Success Metric:** 20 users save and return to see their recommendations

**Purpose:** Only if Phase 1 users explicitly request saving their recommendations or additional features.

**Technical Approach:**
- Maintain FastAPI + SQLite backbone
- Add PostgreSQL migration path if concurrent users > 100
- Email-based magic links for cross-device access (no passwords)
- Enhanced plant filtering by type, season, sun requirements
- Planting calendar view based on seasonal data
- Still no complex authentication, minimal PII collection

**Potential Features:**
1. Cross-device sync via email magic links
2. Advanced filtering (plant type, season, difficulty)
3. Planting/harvest calendar
4. Companion planting suggestions
5. Basic garden planning grid

## Phase 3: Enhanced Recommendations & Personalization

**Timeframe:** After Phase 2 validation
**Success Metric:** 50% of returning users engage with personalized features

**Purpose:** Move beyond basic zone matching to personalized recommendations.

**Technical Approach:**
- Add user garden profiles (size, soil type, sunlight hours)
- Implement preference-based ranking
- Add success tracking (user feedback on recommendations)
- Possibly: simple ML for preference learning
- Maintain FastAPI backend, potentially add Redis cache

## Phase 4: Community & Scale

**Timeframe:** After Phase 3 validation
**Success Metric:** Organic user growth and community engagement

**Purpose:** Build network effects and scale the platform.

**Technical Approach:**
- React frontend migration if complexity warrants
- PostgreSQL for production scale
- User-generated content (tips, photos, success stories)
- Social features (following expert gardeners)
- Possibly: native mobile apps via React Native
- Advanced monitoring and observability

## Out-of-Scope (Never Build)

These features are explicitly out of scope for this project. If evidence later shows they're critical, they become a separate project with separate funding.

1. **AI Chat Interface** — No conversational AI about gardening
2. **Predictive Models** — No ML forecasting of plant growth
3. **Mobile App** — No native iOS/Android apps (web only, Phase 1)
4. **Social Features** — No sharing, following, user profiles (until Phase 4)
5. **Marketplace** — No buying/selling plants
6. **Image Recognition** — No plant identification from photos
7. **Automated Gardening** — No IoT/sensor integrations
8. **Gamification** — No points, badges, leaderboards

## Phase 0 Kickoff Checklist

### Week 1: Preparation
- [ ] Define target demographic: Home gardeners, Norway-based, mixed experience
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

## Architecture Alignment Note

This roadmap has been updated to reflect the architecture defined in ARCHITECTURE.md. Key changes from previous static site approach:

1. **Backend-first**: FastAPI + SQLite replaces static site approach
2. **Proper database**: SQLite with normalized schema instead of CSV/JSON files
3. **API-driven**: HTMX frontend calls RESTful endpoints
4. **Scalable foundation**: Architecture supports future growth to PostgreSQL, React, etc.
5. **Production-ready patterns**: Proper error handling, validation, documentation

The Phase 1 MVP maintains simplicity while establishing a foundation that can scale through Phases 2-4 without major rewrites.

---

*This document is living. Update after each phase based on evidence, not opinion.*  
*Last updated: Aligned with ARCHITECTURE.md FastAPI+SQLite+HTMX architecture*
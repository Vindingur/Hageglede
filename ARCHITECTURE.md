# Hageglede Architecture Document

## Overview
Hageglede is a gardening web application that helps users discover plants suitable for their climate zone based on their postcode. This document outlines the system architecture, data flow, database schema, API design, and technology decisions for the Phase 1 MVP.

## System Architecture

### High-Level Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                     User Browser                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │  HTML/CSS/JS Frontend (Vanilla, no framework)     │    │
│  │  • Postcode input form                           │    │
│  │  • Plant display grid                           │    │
│  │  • LocalStorage for persistence                │    │
│  └────────────────────────────────────────────────────┘    │
│            │                                                │
│            │ HTTP API calls                                 │
│            ▼                                                │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│               FastAPI Backend Server                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Python 3.11+                                     │    │
│  │  • FastAPI framework                             │    │
│  │  • SQLite database                              │    │
│  │  • Uvicorn ASGI server                         │    │
│  └────────────────────────────────────────────────────┘    │
│            │                                                │
│            │ Database operations                           │
│            ▼                                                │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                 SQLite Database                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │  • climate_zones table                           │    │
│  │  • plants table                                 │    │
│  │  • plant_zone_mapping table                    │    │
│  │  • user_saved_plants table                     │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### Postcode → Zone → Plants Process
1. **User Input**: User enters postcode in frontend form
2. **Postcode Validation**: Frontend validates format (Norwegian: 4 digits)
3. **API Request**: Frontend calls `/api/climate-zone/{postcode}`
4. **Zone Lookup**: Backend maps postcode to climate zone using `climate_zones` table
5. **Plant Retrieval**: Backend queries `plant_zone_mapping` and `plants` tables for plants matching the zone
6. **Response**: Returns structured JSON with zone info and plant list
7. **Frontend Display**: Renders plant cards with images, names, and details
8. **User Actions**: User can save plants, which are stored in browser's localStorage

### Data Sources
- Postcode to climate zone mapping (static dataset)
- Plant database with attributes (from datasources.md research)
- Plant images (external CDN or local storage)

## Data Pipeline

### Overview
The Hageglede data pipeline is responsible for fetching, transforming, and loading plant and climate data into the SQLite database that powers the runtime API. This separation ensures that the runtime system serves a pre-built, optimized database read-only, while data updates are handled through a separate pipeline process.

### Architecture Separation
- **Runtime API**: FastAPI application that serves the pre-built SQLite database read-only
- **Data Pipeline**: Standalone scripts that fetch, transform, and load data into the database
- **External Scripts**: Located in the `scripts/` directory, separate from the main application code

### Scripts Directory Structure
```
scripts/
├── fetch_data.py          # Fetches raw data from external sources
├── transform_data.py      # Transforms raw data into database-ready format
├── load_data.py           # Loads transformed data into SQLite database
├── seed_database.py       # Main entry point that orchestrates fetch→transform→load
├── init_db.py             # Initializes database schema (creates tables)
└── validate_data.py       # Validates data integrity after loading
```

### Seeding Workflow
The database seeding follows a consistent fetch → transform → load → commit workflow:

1. **Fetch Phase** (`fetch_data.py`):
   - Downloads plant data from external APIs (Wikidata, GBIF, etc.)
   - Fetches climate zone mapping data
   - Retrieves plant images from Wikimedia Commons
   - Stores raw data in temporary JSON/CSV files

2. **Transform Phase** (`transform_data.py`):
   - Cleans and normalizes raw data
   - Maps external IDs to internal schema
   - Converts temperature ranges to appropriate units
   - Extracts and formats planting/harvest months
   - Creates relationship mappings between plants and climate zones

3. **Load Phase** (`load_data.py`):
   - Drops and recreates tables (for full refresh) or updates existing records
   - Loads transformed data into SQLite database
   - Creates indexes for performance optimization
   - Validates foreign key relationships

4. **Commit Phase**:
   - Verifies data integrity and completeness
   - Creates database backup before replacement
   - Atomically swaps the old database with the new one
   - Updates version metadata

### Pipeline Execution
```bash
# Full database refresh
python scripts/seed_database.py --refresh

# Incremental update (if supported by data sources)
python scripts/seed_database.py --incremental

# Dry run (validate without committing)
python scripts/seed_database.py --dry-run

# Seed with sample data for development
python scripts/seed_database.py --sample
```

### Runtime Considerations
- The pipeline can be run manually, scheduled via cron, or triggered by webhook
- During pipeline execution, the runtime API continues to serve the previous database version
- Database swap is atomic to prevent partial updates
- Version metadata tracks when and from what sources data was loaded

### Data Sources Integration
Each data source has its own adapter in the pipeline:
- **Wikidata/DBpedia**: For plant taxonomy and descriptions
- **GBIF**: For geographical distribution data
- **NOAA/Climate APIs**: For climate zone boundaries
- **Norwegian Post Registry**: For postcode to municipality mapping
- **Wikimedia Commons**: For plant images

### Data Freshness
- **Static Data**: Climate zones, postcode mappings (updated quarterly)
- **Dynamic Data**: Plant availability, seasonal recommendations (updated monthly)
- **Images**: Cached indefinitely with fallback to placeholder

### Error Handling
- Pipeline scripts include comprehensive logging
- Failed steps can be retried independently
- Data validation ensures only clean data reaches production
- Email notifications for pipeline failures

### Development vs Production
- **Development**: Uses sample data for faster iteration
- **Production**: Uses full datasets with proper error handling
- **Testing**: Pipeline includes unit tests for transformation logic

This pipeline architecture ensures that data management is separated from application runtime, allowing for reliable updates without disrupting the user-facing API.

## Database Schema Design

### SQLite Database: `gardening.db`

```sql
-- Climate zones table
CREATE TABLE climate_zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_code VARCHAR(10) NOT NULL UNIQUE,  -- e.g., "1a", "1b", "2a", etc.
    zone_name VARCHAR(100) NOT NULL,        -- e.g., "Very cold", "Cold", "Mild"
    description TEXT,
    min_temperature_celsius DECIMAL(5,2),
    max_temperature_celsius DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Postcode to zone mapping
CREATE TABLE postcode_zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    postcode VARCHAR(10) NOT NULL UNIQUE,   -- Norwegian postcode format
    zone_id INTEGER NOT NULL,
    municipality VARCHAR(100),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (zone_id) REFERENCES climate_zones(id),
    UNIQUE(postcode, zone_id)
);

-- Plants master table
CREATE TABLE plants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scientific_name VARCHAR(200) NOT NULL,
    common_name_norwegian VARCHAR(200) NOT NULL,
    common_name_english VARCHAR(200),
    plant_type VARCHAR(50) CHECK(plant_type IN ('vegetable', 'fruit', 'herb', 'flower', 'berry', 'tree', 'shrub')),
    description TEXT,
    growing_season_start INTEGER,  -- Month number (1-12)
    growing_season_end INTEGER,    -- Month number (1-12)
    sun_requirements VARCHAR(50) CHECK(sun_requirements IN ('full_sun', 'partial_sun', 'shade')),
    water_requirements VARCHAR(50) CHECK(water_requirements IN ('low', 'moderate', 'high')),
    difficulty_level VARCHAR(20) CHECK(difficulty_level IN ('easy', 'medium', 'hard')),
    image_url VARCHAR(500),
    wikipedia_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(scientific_name)
);

-- Plant to climate zone compatibility
CREATE TABLE plant_zone_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plant_id INTEGER NOT NULL,
    zone_id INTEGER NOT NULL,
    suitability VARCHAR(20) CHECK(suitability IN ('excellent', 'good', 'moderate', 'poor')),
    planting_months VARCHAR(100),  -- Comma-separated month numbers, e.g., "3,4,5"
    harvest_months VARCHAR(100),   -- Comma-separated month numbers, e.g., "7,8,9"
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plant_id) REFERENCES plants(id),
    FOREIGN KEY (zone_id) REFERENCES climate_zones(id),
    UNIQUE(plant_id, zone_id)
);

-- User saved plants (localStorage sync backup)
CREATE TABLE user_saved_plants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_session_id VARCHAR(100) NOT NULL,  -- Anonymous session identifier
    plant_id INTEGER NOT NULL,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (plant_id) REFERENCES plants(id),
    UNIQUE(user_session_id, plant_id)
);

-- Indexes for performance
CREATE INDEX idx_postcode_zones_postcode ON postcode_zones(postcode);
CREATE INDEX idx_plant_zone_mapping_zone_id ON plant_zone_mapping(zone_id);
CREATE INDEX idx_plant_zone_mapping_plant_id ON plant_zone_mapping(plant_id);
CREATE INDEX idx_user_saved_plants_session ON user_saved_plants(user_session_id);
```

## API Endpoints

### FastAPI Application Structure
```
app/
├── main.py              # FastAPI app initialization
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── plants.py    # Plant-related endpoints
│   │   ├── zones.py     # Zone-related endpoints
│   │   └── users.py     # User/session endpoints
│   └── models.py        # Pydantic models
├── database/
│   ├── __init__.py
│   ├── database.py      # Database connection
│   ├── crud.py          # CRUD operations
│   └── models.py        # SQLAlchemy models
└── config.py            # Configuration
```

### API Endpoint Specification

#### 1. Climate Zone Endpoints
```python
# GET /api/climate-zones
# Returns: List of all climate zones
Response: List[ClimateZone]

# GET /api/climate-zones/{zone_id}
# Returns: Single climate zone details
Response: ClimateZone

# GET /api/climate-zone/{postcode}
# Returns: Climate zone for a given postcode
Response: {
    "postcode": "1234",
    "zone": ClimateZone,
    "municipality": "Oslo"
}
```

#### 2. Plant Endpoints
```python
# GET /api/plants
# Query params: zone_id, plant_type, season, sun_requirements, etc.
# Returns: Filtered list of plants
Response: List[Plant]

# GET /api/plants/{plant_id}
# Returns: Detailed plant information
Response: PlantDetail

# GET /api/plants/zone/{zone_id}
# Returns: Plants suitable for a specific climate zone
Response: List[ZonePlant]  # Includes suitability info

# GET /api/plants/search?q={query}
# Returns: Plants matching search term
Response: List[Plant]
```

#### 3. User/Session Endpoints
```python
# POST /api/session
# Creates a new anonymous session
Response: {"session_id": "uuid-string"}

# GET /api/session/{session_id}/plants
# Returns: User's saved plants
Response: List[SavedPlant]

# POST /api/session/{session_id}/plants/{plant_id}
# Saves a plant for the user
Response: {"success": true, "message": "Plant saved"}

# DELETE /api/session/{session_id}/plants/{plant_id}
# Removes a saved plant
Response: {"success": true, "message": "Plant removed"}
```

#### 4. System Endpoints
```python
# GET /api/health
# Health check
Response: {"status": "healthy", "timestamp": "2024-01-01T12:00:00Z"}

# GET /api/version
# Returns API version info
Response: {"version": "1.0.0", "build": "abc123"}
```

### Pydantic Models Example
```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ClimateZone(BaseModel):
    id: int
    zone_code: str
    zone_name: str
    description: Optional[str]
    min_temperature_celsius: Optional[float]
    max_temperature_celsius: Optional[float]
    
    class Config:
        from_attributes = True

class Plant(BaseModel):
    id: int
    scientific_name: str
    common_name_norwegian: str
    common_name_english: Optional[str]
    plant_type: str
    image_url: Optional[str]
    
    class Config:
        from_attributes = True

class ZonePlant(Plant):
    suitability: str
    planting_months: List[int]
    harvest_months: List[int]
```

## Frontend Architecture

### File Structure
```
frontend/
├── index.html              # Main HTML file
├── styles/
│   └── main.css           # CSS styles
├── scripts/
│   ├── app.js             # Main application logic
│   ├── api.js             # API client
│   ├── storage.js         # localStorage wrapper
│   └── ui.js              # UI rendering functions
└── assets/
    └── images/            # Static images
```

### Key Frontend Components

#### 1. Postcode Input Component
- Validates Norwegian postcode format (4 digits)
- Shows loading state during API call
- Displays error messages for invalid postcodes

#### 2. Plant Grid Component
- Responsive grid of plant cards
- Each card shows: image, name, type, difficulty
- Save/unsave toggle button
- Filter and sort controls

#### 3. LocalStorage Service
```javascript
// storage.js
const StorageService = {
    SESSION_KEY: 'hageglede_session',
    SAVED_PLANTS_KEY: 'hageglede_saved_plants',
    
    getSessionId() {
        let sessionId = localStorage.getItem(this.SESSION_KEY);
        if (!sessionId) {
            sessionId = crypto.randomUUID();
            localStorage.setItem(this.SESSION_KEY, sessionId);
        }
        return sessionId;
    },
    
    getSavedPlants() {
        const plants = localStorage.getItem(this.SAVED_PLANTS_KEY);
        return plants ? JSON.parse(plants) : [];
    },
    
    savePlant(plantId) {
        const plants = this.getSavedPlants();
        if (!plants.includes(plantId)) {
            plants.push(plantId);
            localStorage.setItem(this.SAVED_PLANTS_KEY, JSON.stringify(plants));
        }
    },
    
    removePlant(plantId) {
        const plants = this.getSavedPlants();
        const updated = plants.filter(id => id !== plantId);
        localStorage.setItem(this.SAVED_PLANTS_KEY, JSON.stringify(updated));
    },
    
    syncWithBackend() {
        // Sync localStorage with backend for persistence
        const sessionId = this.getSessionId();
        const plants = this.getSavedPlants();
        // Call API to sync
    }
};
```

## Deployment Configuration

### Backend Requirements (`requirements.txt`)
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
python-multipart==0.0.6
```

### Docker Configuration (`Dockerfile`)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create database directory
RUN mkdir -p /data

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (`docker-compose.yml`)
```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
      - ./app:/app
    environment:
      - DATABASE_URL=sqlite:////data/gardening.db
      - ENVIRONMENT=production
    restart: unless-stopped
```

## Technology Decisions & Trade-offs

### 1. Backend Framework: FastAPI vs Django/Flask
**Decision**: FastAPI
**Rationale**:
- Automatic OpenAPI documentation generation
- Excellent performance (async support)
- Type hints and Pydantic validation
- Simpler learning curve than Django for MVP
- Better suited for API-first applications

**Trade-off**: Less batteries-included than Django, but appropriate for simple API backend.

### 2. Database: SQLite vs PostgreSQL
**Decision**: SQLite for MVP
**Rationale**:
- Zero configuration, single file
- Perfect for low-to-medium traffic MVP
- ACID compliant
- Easy backups (copy single file)
- Can migrate to PostgreSQL later if needed

**Trade-off**: Limited concurrent writes, but sufficient for MVP read-heavy workload.

### 3. Frontend: Vanilla JS vs React/Vue
**Decision**: Vanilla HTML/CSS/JS
**Rationale**:
- No build step or toolchain complexity
- Faster initial load (no framework overhead)
- Simpler debugging and deployment
- Sufficient for MVP with limited interactivity
- Can add React later if complexity increases

**Trade-off**: More manual DOM manipulation, but acceptable for MVP scale.

### 4. Persistence: LocalStorage vs Backend Database
**Decision**: LocalStorage primary, backend sync optional
**Rationale**:
- Works immediately without authentication
- Offline capability
- Reduces server load and complexity
- Backend sync provided as backup/analytics

**Trade-off**: Data only on user's device, but acceptable for MVP plant saving feature.

### 5. Session Management: Anonymous vs Authentication
**Decision**: Anonymous sessions with UUID
**Rationale**:
- No sign-up friction for users
- Works immediately
- Can add authentication later
- Session persists in localStorage

**Trade-off**: Cannot access saved plants from different devices.

### 6. Image Storage: CDN vs Local
**Decision**: External CDN (Wikimedia Commons, etc.)
**Rationale**:
- No storage costs for MVP
- Large existing plant image database
- Fast delivery via CDN
- Can cache locally later if needed

**Trade-off**: Dependent on external service, but acceptable for MVP.

## Phase 1 MVP Scope

### Core Features
1. Postcode → climate zone lookup
2. Plant recommendations based on zone
3. Plant details view
4. Save plants to "My Garden"
5. Responsive web design

### Out of Scope for MVP
1. User accounts and authentication
2. Advanced plant filtering
3. Planting calendar
4. Social features
5. Mobile apps
6. Payment integration

## Future Considerations

### Scalability Path
1. **Phase 2**: Add PostgreSQL, user accounts, advanced filters
2. **Phase 3**: Add React frontend, planting calendar, notifications
3. **Phase 4**: Mobile apps, community features, premium content

### Database Migration
- SQLite → PostgreSQL when concurrent users > 100
- Add Redis cache for frequently accessed data
- Implement database connection pooling

### Monitoring & Observability
- Add logging middleware
- Implement metrics endpoint
- Set up health checks
- Add error tracking (Sentry)

## Development Setup

### Local Development
```bash
# 1. Clone repository
git clone https://github.com/Vindingur/Hageglede.git
cd Hageglede

# 2. Set up Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database
python scripts/init_db.py

# 5. Seed with sample data
python scripts/seed_data.py

# 6. Run development server
uvicorn app.main:app --reload
```

### Environment Variables
```bash
DATABASE_URL=sqlite:///./gardening.db
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## Testing Strategy

### Backend Tests
- Unit tests for models and CRUD operations
- Integration tests for API endpoints
- Database transaction rollback in tests

### Frontend Tests
- Manual testing for core user flows
- Browser compatibility testing
- Responsive design testing

### Data Validation
- Postcode format validation
- Plant data completeness checks
- Climate zone mapping verification

## Success Metrics for MVP

### Technical Metrics
- API response time < 200ms
- Frontend load time < 2 seconds
- 99% uptime for core services
- Zero critical security issues

### User Metrics
- Postcode lookup success rate > 95%
- Plant save rate > 20%
- Session duration > 3 minutes
- Return rate > 30%

---

*This architecture document serves as the technical blueprint for Hageglede Phase 1 MVP. All implementation should follow these design decisions unless explicitly approved through architecture review.*
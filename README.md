# **Deribit Price Tracker**
Service for tracking cryptocurrency prices from Deribit exchange. The system automatically fetches BTC/USD and ETH/USD prices every minute and provides a REST API for accessing historical data.
## **Table of Contents**
- Project Overview
- Technology Stack
- Design Decisions
- Installation and Deployment
- API Reference
- Monitoring and Maintenance
- Testing
-----
## **Project Overview**
Deribit Price Tracker is a service for collecting and storing cryptocurrency prices from the Deribit exchange. The application fetches current BTC/USD and ETH/USD index prices every minute, stores them in PostgreSQL, and provides a convenient REST API for accessing historical data.

-----
### **Technology Stack**
### **Backend**

|Component|Technology|Version|Description|
| :- | :- | :- | :- |
|Web Framework|FastAPI|0\.104+|High-performance async framework|
|Database|PostgreSQL|15|Relational database|
|ORM|SQLAlchemy|2\.0+|Async ORM with async/await support|
|Migrations|Alembic|1\.12+|Database schema management|
|Task Queue|Celery|5\.3+|Distributed task queue|
|Message Broker|Redis|7|Message broker for Celery|
|HTTP Client|aiohttp|3\.9+|Async HTTP client|
|Validation|Pydantic|2\.5+|Data validation and settings management|
### **Infrastructure**
- **Docker** & **Docker Compose** - containerization and orchestration
- **Flower** - Celery task monitoring
- **pgAdmin** (optional) - PostgreSQL management
-----
## **Design Decisions**
### **1. Architectural Approach: Clean Architecture**
The project strictly follows Clean Architecture principles with clear separation of concerns:


```text
┌─────────────────────────────────────────────────────┐
│              Presentation Layer (API)               │
│              app/api/routes.py                      │
│              FastAPI endpoints, HTTP handling       │
├─────────────────────────────────────────────────────┤
│                 Use Cases Layer                     │
│              app/use\_cases/                        │
│              Business logic                         │
├─────────────────────────────────────────────────────┤
│                  Domain Layer                       │
│              app/domain/                            │
│              Entities and interfaces                │
├─────────────────────────────────────────────────────┤
│              Infrastructure Layer                   │
│              app/infrastructure/                    │
│              Repositories, API clients              │
└─────────────────────────────────────────────────────┘

```

**Rationale**: Clean Architecture ensures:

- **Framework Independence** - business logic doesn't depend on FastAPI or SQLAlchemy
- **Testability** - each layer can be tested in isolation
- **Maintainability** - clear boundaries between components
- **Flexibility** - easy replacement of any layer implementation
### **2. Repository Pattern**
**Rationale**: Data access abstraction enables:

- Easy database switching without business logic changes
- Testing with mock objects
- Unified data access interface
### **3. Dependency Injection**
**Rationale**: DI ensures:

- Loose coupling between components
- Easy implementation swapping
- Simplified testing
- Object lifecycle management
### **4. Domain-Driven Design Principles (DDD)**
**Rationale**: DDD approach guarantees:

- Business rule encapsulation
- Data integrity at domain level
- Clear domain expression
- Protection against invalid states
### **5. CQRS Principles (Command Query Responsibility Segregation)**
- **Command**: FetchAndSavePriceUseCase - write operations
- **Query**: GetAllPricesUseCase, GetLatestPriceUseCase - read operations

**Rationale**: Separating commands and queries allows:

- Independent optimization of reads and writes
- Separate scaling of components
- Simplified code understanding
### **6. Error Handling and Logging**
**Rationale**: Comprehensive error handling provides:

- Clear client messages
- Detailed debugging logs
### **7. Environment-Based Configuration**
**Rationale**: Environment-based configuration ensures:

- Easy environment switching
- Docker environment simplicity
### **8. Celery for Background Tasks**
**Rationale**: Using Celery provides:

- Reliable periodic task execution
- Automatic retry on failures
- Distributed processing
- Flower monitoring
### **9. API Versioning**
**Rationale**: API versioning enables:

- Backward-incompatible changes
- Multiple version support
- Gradual client migration
- Change documentation
-----
## **Installation and Deployment**
### **Method 1: Quick Start with Docker (Recommended)**
#### **Step 1: Clone Repository**
git clone https://github.com/xvma/deribit-price-tracker.git

cd deribit-price-tracker
#### **Step 2: Configure Environment**
cp .env.example .env

\# Edit .env if needed (default values usually work)
#### **Step 3: Start Containers**
\# Build and start all services

docker-compose up --build -d

\# Check status

docker-compose ps
#### **Step 4: Apply Database Migrations**
docker-compose exec app alembic upgrade head
#### **Step 5: Verify Installation**
\# Health check

curl http://localhost:8000/health

\# API check

curl http://localhost:8000/api/v1/prices/latest?ticker=btc\_usd
### **Method 2: Local Development**
#### **Step 1: Clone and Setup**
git clone https://github.com/yourusername/deribit-price-tracker.git

cd deribit-price-tracker

python -m venv venv

source venv/bin/activate  # Linux/Mac

\# venv\Scripts\activate  # Windows
#### **Step 2: Install Dependencies**
pip install --upgrade pip

pip install -r requirements.txt
#### **Step 3: Start Infrastructure (PostgreSQL and Redis)**
docker-compose up -d db redis
#### **Step 4: Apply Migrations**
alembic upgrade head
#### **Step 5: Run Application**
\# Terminal 1: FastAPI application

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

\# Terminal 2: Celery worker

celery -A app.worker.celery\_app worker --loglevel=info --beat

-----
## **API Reference**
### **Base URL**
http://localhost:8000/api/v1
### **Endpoints**
#### **1. Get All Prices**
GET /api/v1/prices?ticker={ticker}&limit={limit}

**Parameters:**

|Parameter|Type|Required|Default|Description|
| :- | :- | :- | :- | :- |
|ticker|string|✅|-|btc\_usd or eth\_usd|
|limit|integer|❌|1000|Max records (1-10000)|

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/prices?ticker=btc\_usd&limit=5"
```

**Example Response:**
```json
[
  {
    "id": 12345,
    "ticker": "btc_usd",
    "price": 52345.67,
    "timestamp": 1709577600,
    "created_at": "2024-03-04T12:00:00"
  }
]
```
#### **2. Get Latest Price**

GET /api/v1/prices/latest?ticker={ticker}

**Example Request:**
```bash

curl "http://localhost:8000/api/v1/prices/latest?ticker=eth\_usd"
```

**Example Response:**
```json
{
  "id": 12345,
  "ticker": "eth_usd",
  "price": 3125.89,
  "timestamp": 1709577600,
  "created_at": "2024-03-04T12:00:00"
}

```
#### **3. Get Prices by Date**

GET /api/v1/prices/by-date?ticker={ticker}&date={date}

**Parameters:**

|Parameter|Type|Required|Format|Description|
| :- | :- | :- | :- | :- |
|ticker|string|✅|-|btc\_usd or eth\_usd|
|date|string|✅|YYYY-MM-DD|Date filter|

#### **4. Get Paginated History**

GET /api/v1/prices/history?ticker={ticker}&limit={limit}&offset={offset}

#### **5. Get Price Statistics**

GET /api/v1/prices/stats?ticker={ticker}&days={days}

**Example Response:**

```json
{
  "ticker": "btc_usd",
  "period_days": 7,
  "count": 10080,
  "min_price": 49876.54,
  "max_price": 53456.78,
  "avg_price": 51678.23,
  "first_price": 51234.56,
  "last_price": 52345.67,
  "change": 1111.11,
  "change_percent": 2.17
}

```

### **Response Codes**

|Code|Description|Possible Reasons|
| :- | :- | :- |
|200|Success|Request processed|
|400|Bad Request|Invalid ticker|
|404|Not Found|No data for period|
|422|Validation Error|Invalid date format|
|500|Internal Error|DB or API issues|

-----
## **Monitoring and Maintenance**
### **Service Monitoring**
#### **Flower (Celery Monitoring)**

URL: http://localhost:5555

- Task execution tracking
- Worker statistics
- Task history and errors

#### **Health Check**

curl http://localhost:8000/health

```json
{
  "status": "healthy",
  "timestamp": 1709577600,
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "deribit_api": "available"
  }
}

```

### **Logging**
#### **Viewing Logs**

```bash
# All logs
docker-compose logs -f

# Specific service logs
docker-compose logs -f app
docker-compose logs -f worker
docker-compose logs -f db

# Last N lines
docker-compose logs --tail=100 worker

```

#### **Log Level Configuration**
```python
# app/core/config.py
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

```

### **Alembic Migrations**

```bash
# Create new migration
docker-compose exec app alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec app alembic upgrade head

# Rollback one migration
docker-compose exec app alembic downgrade -1

# View history
docker-compose exec app alembic history

```

### **Backup and Restore**

```bash
# Create backup
docker-compose exec db pg_dump -U postgres deribit_db > backup_$(date +%Y%m%d).sql

# Restore from backup
cat backup_20240304.sql | docker-compose exec -T db psql -U postgres -d deribit_db

# Automatic backup (cron)
0 2 * * * cd /path/to/project && docker-compose exec -T db pg_dump -U postgres deribit_db > backups/backup_$(date +\%Y\%m\%d).sql

```

### **Celery Management**

```bash
# Restart workers
docker-compose restart worker

# Clear queue
docker-compose exec redis redis-cli FLUSHALL

# Check task status
docker-compose exec worker celery -A app.worker.celery_app inspect active

# Cancel task
docker-compose exec worker celery -A app.worker.celery_app control revoke task_id

```

### **Performance Monitoring**

```bash
# Container resource usage
docker stats

# Log size
du -sh logs/

# Request rate
docker-compose logs app | grep "GET" | wc -l

# API response time
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/prices/latest?ticker=btc_usd

```
-----
## **Testing**
### **Running Tests**

```bash
# All tests with verbose output
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# Specific file
pytest tests/test_repository_async.py -v

# Specific test
pytest tests/test_api_async.py::TestAPI::test_get_latest_price -v

```

### **Code Coverage**

```bash
# Run with coverage report
pytest --cov=app --cov-report=term --cov-report=html

# Open HTML report
open htmlcov/index.html

# Enforce minimum coverage (requires >80%)
pytest --cov=app --cov-fail-under=80

```

### **Integration Testing**

```bash
# Run tests with real database
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Load testing with Locust
locust -f tests/locustfile.py --host=http://localhost:8000

```

### **Adding New Features**
1. **Add interface** in app/domain/interfaces.py
2. **Implement use case** in app/use\_cases/
3. **Add endpoint** in app/api/routes.py
4. **Write tests** in tests/
5. **Update documentation**


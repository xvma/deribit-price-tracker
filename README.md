# **Deribit Price Tracker**
Service for tracking cryptocurrency prices from Deribit exchange. The system automatically fetches BTC/USD and ETH/USD prices every minute and provides a REST API for accessing historical data.
## **Table of Contents**
- Project Overview
- Technology Stack
- Design Decisions
- Installation and Deployment
- API Reference
- Monitoring and Maintenance
- Troubleshooting
- Testing
- Development
- License
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
http

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

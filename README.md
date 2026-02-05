# Coupon & Voucher Platform

A comprehensive **FastAPI-based** coupon and voucher marketplace with **category-based** and **geography-based** discovery, built for high performance and scalability.

## 🚀 Features

### 🎯 Smart Discovery
- **10 Curated Categories**: Pets, Automotive, Home Furnishings, Electronics, Fashion, Beauty, Food & Grocery, Health & Wellness, Tools & DIY, Travel
- **Geographic Organization**: Browse deals by 6 regions (Asia, Middle East, Europe, North America, South America, Africa) and 11+ countries
- **Hybrid Navigation**: Category-first approach with region/country filters for optimal user experience
- **Online vs Local Deals**: Clear distinction between global online deals and location-specific offers

### 💳 Full E-commerce Capabilities
- User registration and JWT authentication
- Shopping cart management
- Secure checkout with mock payment integration
- Order history and purchased coupon tracking
- Revealed redeem codes after purchase

### 🔍 Advanced Filtering
- Filter coupons by category, region, country, and availability type
- Combine multiple filters for precise results
- Browse coupons by category slug (e.g., `/categories/electronics-gadgets/coupons`)
- Browse coupons by country slug (e.g., `/countries/india/coupons`)

### ⚡ Performance Optimized
- Redis caching for frequently accessed data
- Database connection pooling
- Indexed queries for fast lookups
- GZip compression for API responses
- Rate limiting to prevent abuse

### 🛡️ Security & Administration
- Role-based access control (Admin/User)
- Password hashing with bcrypt
- JWT token authentication
- Admin-only endpoints for coupon/category/region/country management

---

## 📁 Project Structure

```
coupons/
├── app/
│   ├── api/              # API route handlers
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── coupons.py    # Coupon CRUD + filtering
│   │   ├── categories.py # Category management
│   │   ├── regions.py    # Region management
│   │   ├── countries.py  # Country management
│   │   ├── users.py      # User profile
│   │   ├── cart.py       # Shopping cart
│   │   └── orders.py     # Order management
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic validation schemas
│   ├── services/         # Business logic layer
│   ├── middleware/       # Rate limiting, logging, auth
│   ├── utils/            # Helpers, JWT, permissions
│   ├── config.py         # Environment configuration
│   ├── database.py       # Database connection
│   └── main.py           # FastAPI application
├── migrations/           # SQL migration scripts
├── API_DOCUMENTATION.md  # Complete API reference
└── requirements.txt      # Python dependencies
```

---

## 🛠️ Technology Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 12+ (with UUID support)
- **Caching**: Redis (optional, for performance)
- **Authentication**: JWT (JSON Web Tokens)
- **ORM**: SQLAlchemy 2.0+
- **Validation**: Pydantic v2
- **Server**: Gunicorn with Uvicorn workers

---

## 📦 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd coupons
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file:
```env
DATABASE_URL=postgresql://user:password@localhost/coupons_db
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080
```

### 4. Run Database Migrations
```bash
# Apply the categories and geography migration
psql $DATABASE_URL -f migrations/002_add_categories_and_geography.sql

# Optional: Add indexes for performance
psql $DATABASE_URL -f migrations/add_indexes.sql
```

### 5. Create Admin User
```bash
python3 create_admin.py
```

### 6. Start the Server
```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn app.main:app -c gunicorn.conf.py
```

---

## 🌐 API Overview

**Base URL**: `http://localhost:8000` (or your deployed URL)  
**Swagger Docs**: `http://localhost:8000/docs`  
**Version**: 2.0.0

### Core Endpoints

| Category | Endpoint | Description |
|----------|----------|-------------|
| **Categories** | `GET /categories/` | List all categories |
| | `GET /categories/{slug}/coupons` | Browse coupons by category |
| **Regions** | `GET /regions/` | List regions with countries |
| | `GET /regions/{slug}/coupons` | Browse coupons by region |
| **Countries** | `GET /countries/` | List all countries |
| | `GET /countries/{slug}/coupons` | Browse coupons by country |
| **Coupons** | `GET /coupons/` | List/filter coupons |
| | `POST /coupons/` | Create coupon (admin) |
| **Auth** | `POST /auth/register` | Register new user |
| | `POST /auth/login` | Login and get JWT token |
| **Cart** | `POST /cart/add` | Add coupon to cart |
| | `GET /cart/` | View cart |
| **Orders** | `POST /orders/checkout` | Purchase cart items |
| | `GET /orders/` | View order history |

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete details.

---

## 🎯 Usage Examples

### Browse Electronics in India
```bash
# Get category ID for Electronics
CATEGORY_ID=$(curl -s http://localhost:8000/categories/ | jq -r '.[] | select(.slug=="electronics-gadgets") | .id')

# Get country ID for India
COUNTRY_ID=$(curl -s http://localhost:8000/countries/ | jq -r '.[] | select(.slug=="india") | .id')

# Filter coupons
curl "http://localhost:8000/coupons/?category_id=$CATEGORY_ID&country_id=$COUNTRY_ID&active_only=true"
```

### Create a Local Coupon for UAE
```bash
# Login as admin
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"country_code":"+91","number":"7907975711","password":"afsal@123"}' | jq -r '.access_token')

# Get category and country
FOOD_CAT=$(curl -s http://localhost:8000/categories/ | jq -r '.[] | select(.slug=="food-grocery") | .id')
UAE_ID=$(curl -s http://localhost:8000/countries/ | jq -r '.[] | select(.slug=="united-arab-emirates") | .id')

# Create coupon
curl -X POST http://localhost:8000/coupons/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"code\": \"DUBAIMEAL30\",
    \"redeem_code\": \"MEAL30OFF\",
    \"brand\": \"Dubai Restaurants\",
    \"title\": \"30% off any meal\",
    \"discount_type\": \"percentage\",
    \"discount_amount\": 30.0,
    \"price\": 3.99,
    \"category_id\": \"$FOOD_CAT\",
    \"availability_type\": \"local\",
    \"country_ids\": [\"$UAE_ID\"]
  }"
```

---

## 📊 Database Schema

### Core Tables
- `users` - User accounts with authentication
- `coupons` - Coupon details with category and availability
- `categories` - 10 predefined coupon categories
- `regions` - Geographic regions (6 total)
- `countries` - Countries within regions (11+ seeded)
- `coupon_countries` - Many-to-many link between coupons and countries
- `cart_items` - User shopping cart
- `orders` - Purchase history
- `user_coupons` - Claimed coupons with revealed codes

---

## 🔒 Admin Credentials

**Phone**: +917907975711  
**Password**: afsal@123  
*(Change after first login)*

---

## 🚢 Deployment

The platform includes GitHub Actions CI/CD:
- Automated Docker builds
- Push to GitHub Container Registry
- Deploy script for production

See `.github/workflows/ci-cd.yml` for details.

---

## 📄 License

MIT License - feel free to use this project for commercial purposes.

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📞 Support

For issues or questions, please open a GitHub issue.

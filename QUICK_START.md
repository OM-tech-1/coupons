# ⚡ Quick Start - 2 Minutes Setup

## Step 1: Clone & Setup (One Command)

```bash
git clone <repository-url>
cd coupons
make setup
```

**Wait 2-3 minutes** while it:
- Creates Python environment
- Installs dependencies
- Starts Docker (PostgreSQL + Redis)
- Sets up database
- Creates admin user

## Step 2: Start Development

```bash
source .venv/bin/activate  # Activate Python environment
make dev                    # Start server
```

## Step 3: Open Browser

- **API Docs**: http://localhost:8000/docs
- **Try it out**: Click any endpoint and test it!

---

## 🔑 Login Credentials

**Admin User:**
- Phone: `+917907975711`
- Password: `afsal@123`

**Database:**
- Host: `localhost:5432`
- User: `coupon_user`
- Password: `coupon_pass`

---

## 📝 Environment Variables (.env)

The `.env` file is **auto-created** by `make setup`. Default values:

```bash
# Database (Docker)
DATABASE_URL=postgresql://coupon_user:coupon_pass@localhost:5432/coupon_db

# Redis (Docker)
REDIS_URL=redis://localhost:6379/0

# JWT (Development)
JWT_SECRET=dev-secret-key-change-in-production-12345678
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

# Stripe (Test Mode - won't charge real money)
STRIPE_SECRET_KEY=sk_test_51234567890abcdefghijklmnopqrstuvwxyz
STRIPE_PUBLISHABLE_KEY=pk_test_51234567890abcdefghijklmnopqrstuvwxyz
STRIPE_WEBHOOK_SECRET=whsec_1234567890abcdefghijklmnopqrstuvwxyz

# Optional (leave empty if not needed)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
EXTERNAL_API_KEY=

# App Settings
ENVIRONMENT=development
DEBUG=True
```

### 🔧 When to Update .env

**You DON'T need to change anything** for basic development!

**Only update if:**
- Testing Stripe payments → Get real test keys from [Stripe Dashboard](https://dashboard.stripe.com/test/apikeys)
- Testing file uploads → Add AWS credentials
- Using different database → Change DATABASE_URL

---

## 🎯 Common Commands

```bash
make help              # Show all commands
make dev               # Start development server
make test              # Run tests
make docker-logs       # View database logs
make docker-db         # Connect to PostgreSQL
make docker-redis      # Connect to Redis
make clean             # Clean cache files
```

---

## 🐛 Troubleshooting

### "Port already in use"
```bash
# Kill process on port 8000
lsof -i :8000
kill -9 <PID>
```

### "Docker not running"
```bash
# Start Docker Desktop, then:
make docker-restart
```

### "Database connection failed"
```bash
# Check if Docker is running
docker ps

# Restart services
make docker-restart
```

### "Module not found"
```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
make install
```

---

## ✅ Verify Everything Works

```bash
# 1. Check setup
./verify-setup.sh

# 2. Run tests
make test

# 3. Try API
curl http://localhost:8000/health
```

---

## 📚 Next Steps

1. ✅ Setup complete
2. 📖 Read [INTERN_GUIDE.md](INTERN_GUIDE.md) for detailed guide
3. 🔍 Explore API at http://localhost:8000/docs
4. 💻 Start coding!

---

## 🆘 Need Help?

- Run `make help` for all commands
- Check [INTERN_GUIDE.md](INTERN_GUIDE.md) for detailed docs
- Ask your mentor

---

**That's it! You're ready to code! 🎉**

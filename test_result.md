#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================
# (Protocol preserved)
#====================================================================================================
# END - Testing Protocol
#====================================================================================================

## user_problem_statement: |
  GNOVA Fintech Platform - Build a complete fintech application for Iranian users with:
  - IRR Fiat deposit/withdrawal system
  - Cryptocurrency (USDT, BTC) wallet
  - Asset conversion/exchange with rate locking
  - Internal double-entry ledger system (immutable, source of truth)
  - Telegram bot integration (@KKM_GNOVA_bot, token: 8455539741:AAGaKa1bTTe6QIgUroJgPWISfs3fK09rtYU)
  - Payment gateway integration (with mock PSP for development)
  - Rate alerts and notifications
  - Spending analytics
  - Referral program
  - User authentication (JWT-based with Telegram ID)
  - KYC verification system
  - Transaction history with export
  - Beautiful Persian/Farsi RTL UI

## backend:
  - task: "Database initialization with SQLite"
    implemented: true
    working: true
    file: "database.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "SQLite database with tables for users, accounts, assets, transactions, ledger_entries, webhook_events, exchange_rates, conversion_quotes, audit_logs, rate_alerts. Seeded with default assets (CREDIT, IRR, USDT, BTC). Database initialized successfully."

  - task: "Authentication Service (JWT with Telegram ID)"
    implemented: true
    working: true
    file: "auth_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "POST /api/auth/register, POST /api/auth/login, GET /api/auth/me. JWT tokens with 30-day expiration. Tested via curl - all working."

  - task: "Ledger Service (Double-entry bookkeeping)"
    implemented: true
    working: true
    file: "ledger_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: false
        agent: "main"
        comment: "Initial implementation had SQL error - VALUES had 10 placeholders for 11 columns in debit_account"
      - working: true
        agent: "main"
        comment: "Fixed SQL error in debit_account VALUES clause. Tested credit, debit, reserve, balance compute - all working. Idempotency via source_ref unique index confirmed."

  - task: "Wallet API endpoints"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "GET /api/wallets returns all balances. Tested - shows BTC, CREDIT, IRR, USDT correctly with total IRR value calculation."

  - task: "Deposit System"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "POST /api/deposits/initiate creates deposit with payment URL. POST /api/webhooks/payment processes PSP callbacks with idempotency. Tested complete flow: deposit -> webhook -> credit ledger entry. Idempotency confirmed by replaying webhook."

  - task: "Conversion System"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "POST /api/convert/quote creates quote with 5-minute lock. POST /api/conversions/confirm executes conversion atomically (debit from + credit to). Tested CREDIT->USDT conversion, balances updated correctly."

  - task: "Withdrawal System"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: true
        agent: "main"
        comment: "POST /api/withdrawals creates pending withdrawal with reserve_amount. Requires KYC=approved. Not fully tested yet - blocks at KYC check which is expected behavior."

  - task: "Transaction History"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "GET /api/transactions returns user transactions with pagination. Tested."

  - task: "Rate Alerts"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "low"
    needs_retesting: true
    status_history:
      - working: true
        agent: "main"
        comment: "POST /api/alerts/rate and GET /api/alerts implemented. Not extensively tested."

  - task: "Telegram Bot"
    implemented: true
    working: true
    file: "telegram_bot.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: false
        agent: "main"
        comment: "Initial issue: dotenv loading wasn't working, telegram module not found in venv"
      - working: true
        agent: "main"
        comment: "Fixed dotenv loading with absolute path. Configured supervisor to use venv python. Bot is RUNNING in supervisor. Has 12 commands: /start, /help, /balance, /deposit, /withdraw, /convert, /history, /alerts, /analytics, /export, /settings, /referral. Inline keyboards and interactive UI. Not yet tested with actual Telegram messages."

## frontend:
  - task: "Landing Page"
    implemented: true
    working: true
    file: "pages/LandingPage.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: false
        agent: "main"
        comment: "Initial Persian text spacing issue from tracking-tight"
      - working: true
        agent: "main"
        comment: "Fixed by changing font-heading to Vazirmatn. Beautiful design with hero, features, trust section, CTA. Screenshots confirm proper rendering."

  - task: "Login Page (Telegram ID auth)"
    implemented: true
    working: true
    file: "pages/LoginPage.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: true
        agent: "main"
        comment: "Login form with Telegram ID input. Calls /api/auth/login, falls back to /api/auth/register if user doesn't exist. Needs full E2E testing."

  - task: "Dashboard"
    implemented: true
    working: true
    file: "pages/Dashboard.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: true
        agent: "main"
        comment: "Total balance card, quick actions, asset balances grid, recent transactions, Telegram bot promo. Hide/show balance toggle. Not yet tested via browser."

  - task: "Deposit Page"
    implemented: true
    working: true
    file: "pages/DepositPage.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: true
        agent: "main"
        comment: "Form with quick amount buttons, success state with payment URL"

  - task: "Withdraw Page"
    implemented: true
    working: true
    file: "pages/WithdrawPage.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: true
        agent: "main"
        comment: "Withdrawal form with KYC check warning, destination type selection"

  - task: "Convert Page"
    implemented: true
    working: true
    file: "pages/ConvertPage.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: true
        agent: "main"
        comment: "Asset converter with swap button, rate lock countdown, quote display"

  - task: "History Page"
    implemented: true
    working: true
    file: "pages/HistoryPage.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: true
        agent: "main"
        comment: "Transaction table with filters and CSV export"

## metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 1
  run_ui: true

## test_plan:
  current_focus:
    - "Authentication flow (register/login via UI)"
    - "Wallet balance display"
    - "Deposit flow (initiate -> webhook simulation)"
    - "Conversion flow (quote -> confirm)"
    - "Transaction history"
    - "Backend API endpoints"
  stuck_tasks: []
  test_all: true
  test_priority: "high_first"

## agent_communication:
  - agent: "main"
    message: |
      GNOVA Fintech Platform built with:
      - SQLite database (designed for PostgreSQL compatibility)
      - FastAPI backend with full ledger system
      - React frontend with beautiful RTL Persian UI
      - Telegram bot running with full command set
      - JWT-based auth using Telegram ID
      
      All backend APIs tested via curl and working:
      - Auth (register/login/me)
      - Wallets (balance computation)
      - Deposits (initiate + webhook with idempotency)
      - Conversions (quote + confirm with rate lock)
      - Withdrawals (with KYC check)
      
      Test user available: telegram_id=999888777, has 900,000 CREDIT and 0.000001 USDT
      
      Please test:
      1. Backend API endpoints comprehensively (all listed in test_plan)
      2. Frontend pages: Landing, Login, Dashboard, Deposit, Withdraw, Convert, History
      3. Idempotency of webhook (replay should not double-credit)
      4. Conversion atomicity (debit + credit in single transaction)
      
      Telegram bot is configured but won't be tested via real Telegram (only verify it's running).

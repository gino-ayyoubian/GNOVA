# GNOVA Fintech Platform - Product Requirements Document

## Original Problem Statement
بررسی و آنالیز و تحلیل و اصلاح خطاها یا اشکالات و داده های غیر حقیقی یا واقعی و عملکردهای غیر صحیح و جستجوی عمیق و به روز و ارایه و اعمال توصیه ها و پیشنهادات خلاقانه و نو اورانه و موثر و مفید و کاربردی و تولید و ایجاد و ساختن اپلیکیشن و بات و تست و راه اندازی.

Build the GNOVA financial platform - a comprehensive fintech application for Iranian users with IRR Fiat deposits, internal ledger, payment gateway integration, Telegram bot integration, and cryptocurrency wallet operations.

## Architecture

### Backend (FastAPI + SQLite)
- **Database**: SQLite with PostgreSQL-compatible schema (12 tables)
- **Auth**: JWT-based with Telegram ID integration
- **Ledger**: Double-entry, append-only, immutable transactions
- **Idempotency**: source_ref unique constraint prevents double-credit
- **Atomicity**: All financial operations in DB transactions

### Frontend (React 19 + Tailwind)
- **Language**: Persian (RTL) with Vazirmatn font
- **Theme**: Swiss & High-Contrast (Light) - Deep Persian Blue + Emerald Green
- **Components**: shadcn/ui-based with custom GNOVA design system
- **State**: AuthContext + axios + JWT tokens

### Telegram Bot (@KKM_GNOVA_bot)
- 12 commands: /start, /help, /balance, /deposit, /withdraw, /convert, /history, /alerts, /analytics, /export, /settings, /referral
- Interactive inline keyboards
- Real-time notifications support

## User Personas
1. **Iranian Crypto Trader**: Wants quick IRR↔USDT/BTC conversion with locked rates
2. **Casual User**: Wants simple Telegram-based wallet for daily transactions
3. **Business User**: Needs analytics, invoicing, and bulk operations

## Core Requirements (Static)
- Persian/Farsi RTL support
- Iranian payment gateway integration (PSP)
- Multi-asset wallet (IRR, CREDIT, USDT, BTC)
- Internal ledger as single source of truth
- KYC verification gates for withdrawals
- Idempotent webhook processing
- Rate locking for conversions (5-min)

## What's Been Implemented (2026-01)

### Backend ✅
- ✅ SQLite database with 12 tables (users, accounts, assets, transactions, ledger_entries, webhook_events, exchange_rates, conversion_quotes, audit_logs, rate_alerts, transaction_categories, user_settings, referrals)
- ✅ JWT auth service (register, login, /me)
- ✅ Ledger service (credit, debit, reserve, balance compute with double-entry)
- ✅ Wallet API (multi-asset balances + total IRR value)
- ✅ Deposit system (initiate + webhook with idempotency)
- ✅ Conversion system (quote with rate lock + atomic confirm)
- ✅ Withdrawal system (with KYC check, reserve_amount creates PENDING)
- ✅ Transaction history with pagination
- ✅ Rate alerts (create/list)
- ✅ CORS middleware
- ✅ Health check endpoint

### Frontend ✅
- ✅ Landing Page (hero, features grid, trust section, CTA)
- ✅ Login Page (Telegram ID auth with auto-register fallback)
- ✅ Dashboard (total balance, asset cards, recent transactions, quick actions)
- ✅ Deposit Page (amount input, quick amounts, payment URL display)
- ✅ Withdraw Page (form with KYC warning, destination type selection)
- ✅ Convert Page (asset swap, 5-min rate lock countdown, quote display)
- ✅ History Page (filterable transaction table with CSV export)
- ✅ Placeholder pages (Wallet, Analytics, Alerts, Settings)
- ✅ AuthContext with protected routes
- ✅ Sidebar navigation
- ✅ Persian RTL with Vazirmatn font

### Telegram Bot ✅
- ✅ Bot running via supervisor as @KKM_GNOVA_bot
- ✅ 12 commands implemented with inline keyboards
- ✅ User registration/login on /start
- ✅ Balance display with real backend integration
- ✅ Deposit, withdraw, convert flows
- ✅ Analytics, history, referral commands

## Test Results (2026-01)
- **Backend**: 20/20 tests passed (100%)
- **Frontend**: 100% success rate
- **Webhook Idempotency**: ✅ Verified (replay returns "already_processed")
- **Conversion Atomicity**: ✅ Verified (debit + credit in same transaction)
- **KYC Gate**: ✅ Verified (withdrawal blocked for pending KYC)

## Mocked/Pending Items
- 🟡 **Payment Gateway PSP**: MOCKED - signature verification optional, accepts any payload
- 🟡 **Exchange Rates**: HARDCODED (USDT=65000 IRR, BTC=2.85B IRR) - should integrate live feed
- 🟡 **Telegram Bot**: Not tested with real Telegram messages, but service is RUNNING
- ⏳ **Blockchain Integration**: Not implemented for actual crypto withdrawals
- ⏳ **Real PSP Integration**: ZarinPal/IDPay/Saman bank not configured

## Prioritized Backlog

### P0 (Production-blocking)
- Real PSP integration (ZarinPal/IDPay)
- Live exchange rate feed (CoinGecko/NobiTex)
- HMAC signature verification (mandatory)
- Move secrets to Secret Manager
- HSM/multisig for cold wallet

### P1 (Important features)
- Analytics page (charts, spending breakdown)
- Settings page (KYC submission, 2FA toggle, language switch)
- Rate alerts page (create/manage)
- Wallet page (detailed view per asset)
- Real-time notifications via WebSocket
- Telegram bot deep linking for web auth

### P2 (Enhancements)
- QR code generation for deposits
- PDF export for transactions
- Referral program (with actual rewards)
- Multi-language (English support)
- Mobile responsive optimization
- Dark mode

## Test Credentials
See `/app/memory/test_credentials.md`

## Tech Stack Summary
- **Backend**: Python 3.11, FastAPI 0.110, SQLite, aiosqlite, JWT
- **Frontend**: React 19, Tailwind, axios, react-router-dom 7, lucide-react
- **Bot**: python-telegram-bot 22.7
- **DB**: SQLite (dev), PostgreSQL-ready schema
- **Auth**: JWT with Telegram ID

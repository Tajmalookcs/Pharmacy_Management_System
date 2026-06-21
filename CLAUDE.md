# PharmaPOS — Claude Session Context

## Project Overview
A full-featured **Pharmacy Point of Sale (POS)** web application built with Django.
One physical pharmacy shop with multiple counters, partners, and employees.

## Tech Stack
- **Backend:** Django 4.2.13
- **Database:** SQLite (PostgreSQL-ready for future)
- **Frontend:** Bootstrap 5 + Vanilla JS
- **PDF/Receipt:** WeasyPrint
- **Excel Export:** openpyxl
- **Charts:** Chart.js
- **Barcode:** python-barcode
- **Python:** 3.12.10

## Business Structure
```
One Pharmacy Shop
│
├── Superuser (admin) — full control of everything
├── Partners (owners) — read-only: profit, sales, reports
├── Pharmacist — inventory, purchases, suppliers
└── Counters (2 now, scalable)
    ├── Counter 1 → Cashier 1
    └── Counter 2 → Cashier 2
```

## User Roles & Access
| Feature        | Superuser | Partner | Pharmacist | Cashier |
|----------------|-----------|---------|------------|---------|
| POS / Sales    | ❌        | ❌      | ❌         | ✅      |
| Returns        | ❌        | ❌      | ❌         | ✅      |
| Inventory      | ✅        | ❌      | ✅         | ❌      |
| Purchases      | ✅        | ❌      | ✅         | ❌      |
| Day Closing    | ✅        | ❌      | ❌         | ✅      |
| Reports        | ✅        | ✅      | ✅         | ❌      |
| Partners       | ✅        | ✅      | ❌         | ❌      |
| Suppliers      | ✅        | ❌      | ✅         | ❌      |
| Customers      | ✅        | ❌      | ✅         | ✅      |
| Settings       | ✅        | ❌      | ❌         | ❌      |
| Users/Counters | ✅        | ❌      | ❌         | ❌      |

## Core Modules
1. **Authentication & Roles** — login, role-based access
2. **Inventory / Stock** — drugs, categories, expiry, low stock alerts
3. **Counters** — 2+ counters, each assigned to one cashier
4. **POS / Sales** — cart, discount, payment (cash/card/partial), receipt
5. **Returns** — within 15 days, cash refund or drug exchange, auto stock restore
6. **Day Closing** — evening cash reconciliation per counter
7. **Partners & Profit Sharing** — ownership %, profit share reports
8. **Suppliers & Purchases** — stock in, supplier payments
9. **Customers** — profile, purchase history, return history
10. **Reports** — sales, stock, profit, per counter/cashier, PDF/Excel
11. **Settings** — pharmacy info, tax, currency, return policy days

## Database Models (overview)
```
User            — role: superuser, partner, pharmacist, cashier
Partner         — linked to User + ownership %
Counter         — name, assigned cashier
Category        — drug categories
Supplier        — supplier profiles
Drug            — category, supplier, barcode, sale price, cost price, qty, reorder level, expiry
Customer        — name, phone, purchase history
Sale            — counter, cashier, customer, date, total, discount, payment method
SaleItem        — sale, drug, qty, unit price, discount
Return          — linked to original Sale, type: cash/exchange (within 15 days)
ReturnItem      — return, drug, qty, reason
Purchase        — supplier, pharmacist, date, total
PurchaseItem    — purchase, drug, qty, cost price
DayClosing      — counter, cashier, date, expected cash, actual cash, difference
StockAdjustment — drug, qty, reason, date
```

## URL Structure
```
/                        → dashboard (role-based)
/pos/<counter_id>/       → POS screen (cashier)
/sales/                  → sales list
/sales/<id>/             → sale detail + receipt
/returns/                → returns list
/returns/new/<sale_id>/  → process return
/inventory/              → drug list
/inventory/add/          → add drug
/purchases/              → purchase orders
/customers/              → customer list
/suppliers/              → supplier list
/day-closing/            → counter day closing
/reports/                → reports dashboard
/partners/               → partner profit view
/settings/               → pharmacy settings
/users/                  → user & counter management
```

## Django App Structure
```
pharmapos/          ← project config (settings, urls, wsgi)
apps/
  accounts/         ← users, roles, partners, counters
  inventory/        ← drugs, categories, suppliers, purchases, stock
  sales/            ← POS, sales, sale items, returns
  reports/          ← all reports and analytics
  settings_app/     ← pharmacy settings
```

## Counter & POS Rules
- Each cashier is assigned to **one counter only** — they can only sell from their own counter
- **Superuser cannot create sales** from any counter — POS is cashier-only
- **Main Counter** cashier can view and receive pending orders from all other counters
- Dashboard counter chips are **view-only** for non-cashiers (status display only)

## Key Business Rules
- Return allowed only within **15 days** of original sale (system enforced)
- Return types: **cash refund** or **drug exchange**
- Stock is **centralized** — one pool for all counters
- Each cashier is **fixed to one counter**
- Day closing happens **every evening** — once closed, no edits allowed
- Partners can **only view** — no edit access
- Superuser has **full access** to everything

## Project Location
`D:\Pharmacy\Pharmacy_Management_System`

## How to Run
```bash
# Activate venv
venv\Scripts\activate

# Run server
python manage.py runserver
```

## Important Notes
- Python 3.12.10 — do NOT use deprecated Python 3.12 syntax
- SQLite for now, keep PostgreSQL compatibility in mind
- Bootstrap 5 for all frontend — no other CSS frameworks
- Keep offline-first in mind (may go online in future)
- Do not start coding any module without user confirmation

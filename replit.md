# Tally Prime Analytics Dashboard

## Overview

The Tally Prime Analytics Dashboard is a cloud-based SaaS platform that transforms Tally Prime accounting data into actionable business intelligence. The application fetches real-time data from Tally Prime servers via XML API, processes it through a FastAPI backend, and presents 15+ pre-built reports and dashboards through an intuitive React frontend. The platform enables AI-driven forecasting, customer segmentation, inventory tracking, and compliance monitoring, reducing manual reporting efforts by 70% while maintaining GST compliance.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Technology Stack**: React 19.2.0 with Vite 7.1.9 build tooling

The frontend uses a component-based architecture with the following design decisions:

- **UI Framework**: Tailwind CSS v4 for styling with custom Tally-themed color palette (tally-blue: #0052CC, tally-dark: #1a1d2e, tally-light: #f8f9fa)
- **Component Libraries**: 
  - Headless UI for accessible UI components
  - Heroicons and Lucide React for iconography
  - Framer Motion for smooth animations and transitions
- **Routing**: React Router DOM v7 for client-side navigation
- **Data Visualization**: Recharts library for charts, graphs, and dashboard visualizations
- **State Management**: Component-level state with React hooks (no global state library currently implemented)

**Design Pattern**: The application follows a tile-based dashboard interface inspired by Tally Prime's native interface, prioritizing customization, drag-and-drop capabilities, and mobile responsiveness. Each dashboard tile is designed as a reusable component with drill-down capabilities for detailed analysis.

### Backend Architecture

**Technology Stack**: Python FastAPI framework

The backend serves as a data transformation layer between Tally Prime and the frontend:

- **API Framework**: FastAPI for high-performance REST API endpoints with automatic OpenAPI documentation
- **Authentication**: Custom authentication module (`src/auth.py`) with role-based access control (Administrator, Manager, Viewer roles with granular permissions)
- **Tally Integration**: Custom XML API client (`src/tally_api.py`) that constructs and sends XML envelopes to Tally Prime server (default: localhost:9000)
- **Data Processing**: 
  - Analytics module (`src/analytics.py`) for ML-based forecasting using scikit-learn (RandomForestRegressor, KMeans clustering)
  - Report generation (`src/reports.py`) for transforming raw Tally data into business reports
  - Alert system (`src/alerts.py`) for threshold-based notifications (low stock, overdue payments, cash flow issues)

**Security Model**: Password hashing using SHA-256, default users stored in-memory (production would use database), Tally connection validation on login

**Alternative Considered**: Initially considered Streamlit for rapid prototyping but chose FastAPI + React for better separation of concerns, scalability, and production-grade architecture.

### Data Flow Architecture

1. **Data Fetching**: XML requests sent to Tally Prime server with specific envelopes (Sales, Purchase, Inventory, Balance Sheet, etc.)
2. **Data Transformation**: Raw XML parsed into pandas DataFrames, cached for performance
3. **Analytics Processing**: ML models applied for forecasting and pattern detection
4. **API Response**: JSON formatted data returned to frontend via REST endpoints
5. **Visualization**: React components consume API data and render using Recharts

**Caching Strategy**: Cached data fetching functions (`fetch_cached_sales_data`, `fetch_cached_inventory_data`) to reduce Tally server load and improve response times.

### Development Environment

- **Hot Module Replacement**: Vite dev server with HMR for rapid frontend development
- **CORS Configuration**: Permissive CORS middleware for development (should be restricted in production)
- **Proxy Configuration**: Vite dev server proxies `/api` requests to FastAPI backend (localhost:8000)
- **Port Allocation**: 
  - Frontend: Port 5000
  - Backend: Port 8000
  - Tally Prime: Port 9000 (default)

## External Dependencies

### Tally Prime Integration

- **Connection Method**: XML API over HTTP
- **Default Endpoint**: http://localhost:9000
- **Data Sources**:
  - Masters: Ledgers, Stock Items, Parties
  - Vouchers: Sales, Purchases, Receipts, Payments
  - Reports: Balance Sheet, P&L, Outstandings, GST Returns, Bank Reconciliation
  - Audit: Modification logs with `SVAUDITYES` flag
- **Authentication**: Connection test performed on user login to validate Tally server accessibility

### Machine Learning Libraries

- **scikit-learn**: Used for predictive analytics
  - RandomForestRegressor: Sales forecasting with 100 estimators
  - KMeans: Customer segmentation
  - StandardScaler: Feature normalization
  - LinearRegression: Trend analysis
- **pandas/numpy**: Data manipulation and numerical computations
- **Forecast Capabilities**: 30-day sales projections with confidence intervals based on historical patterns, day-of-week seasonality, and monthly trends

### Visualization & UI Libraries

- **Recharts**: Primary charting library for line charts, bar graphs, pie charts, heat maps, waterfall charts
- **Plotly**: Secondary visualization library (used in backend analytics module) for interactive graphs
- **Framer Motion**: Animation library for smooth UI transitions and tile interactions
- **Headless UI**: Accessible component primitives without imposed styling

### HTTP & API Communication

- **axios**: Frontend HTTP client for API requests
- **requests**: Python HTTP library for Tally XML API communication with 30-second timeout
- **FastAPI**: ASGI framework with automatic validation via Pydantic models

### Database Considerations

**Current State**: No database currently implemented; user data stored in-memory as default users dictionary

**Production Requirements**: The architecture is designed to integrate with PostgreSQL (mentioned in project requirements) for:
- User authentication and authorization
- Custom dashboard configurations
- Alert history and acknowledgment tracking
- Cached Tally data for offline access
- Multi-company data isolation for Enterprise tier

**Migration Path**: Drizzle ORM mentioned in context suggests future PostgreSQL integration planned, requiring schema for users, companies, alerts, custom_dashboards, and cached_reports tables.

### Monetization & Tiered Access

- **Basic Tier**: $10/month - Core reports access
- **Pro Tier**: $50/month - Advanced analytics and forecasting
- **Enterprise Tier**: Custom pricing - Multi-company support, custom integrations

Permission-based feature gating implemented in `src/auth.py` with `check_permission` and `require_permission` decorators.
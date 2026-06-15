# Institutional Fleet Management Dashboard - Technical Specification

## Overview
Web/mobile dashboard for nonprofit + government fleet clients to manage vehicle maintenance, track costs, and monitor compliance.

---

## 1. DATABASE SCHEMA

### 1.1 Institutions Table
```sql
CREATE TABLE institutions (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  org_type ENUM('nonprofit', 'government', 'educational') NOT NULL,
  phone VARCHAR(20),
  email VARCHAR(255),
  primary_contact_name VARCHAR(255),
  address_street VARCHAR(255),
  address_city VARCHAR(100),
  address_zip VARCHAR(10),
  fleet_size INT,
  retainer_monthly_usd NUMERIC(10,2),
  contract_start_date DATE,
  contract_end_date DATE,
  contract_status ENUM('active', 'inactive', 'expired') DEFAULT 'active',
  mission_statement TEXT,
  mission_donation_percent INT DEFAULT 5,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP
);
```

### 1.2 Fleet (Vehicles) Table
```sql
CREATE TABLE fleet_vehicles (
  id BIGSERIAL PRIMARY KEY,
  institution_id UUID NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
  vin VARCHAR(17) UNIQUE NOT NULL,
  make VARCHAR(50),
  model VARCHAR(50),
  year INT,
  color VARCHAR(50),
  license_plate VARCHAR(20),
  current_mileage INT,
  fuel_type ENUM('gas', 'diesel', 'hybrid', 'electric'),
  status ENUM('active', 'retired', 'in-maintenance') DEFAULT 'active',
  purchased_date DATE,
  last_service_date DATE,
  next_scheduled_maintenance DATE,
  compliance_status ENUM('compliant', 'warning', 'expired') DEFAULT 'compliant',
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP
);
```

### 1.3 Work Orders Table
```sql
CREATE TABLE work_orders (
  id BIGSERIAL PRIMARY KEY,
  institution_id UUID NOT NULL REFERENCES institutions(id),
  vehicle_id BIGINT NOT NULL REFERENCES fleet_vehicles(id),
  service_type ENUM('preventive', 'repair', 'inspection', 'emergency') NOT NULL,
  description TEXT,
  requested_by_name VARCHAR(100),
  requested_by_phone VARCHAR(20),
  requested_at TIMESTAMP DEFAULT NOW(),
  status ENUM('pending', 'assigned', 'in-progress', 'completed', 'cancelled') DEFAULT 'pending',
  priority ENUM('routine', 'urgent', 'emergency') DEFAULT 'routine',
  estimated_cost NUMERIC(10,2),
  actual_cost NUMERIC(10,2),
  labor_hours NUMERIC(5,2),
  parts_used TEXT,
  completed_at TIMESTAMP,
  mechanic_notes TEXT,
  photos_urls JSONB,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### 1.4 Invoices Table
```sql
CREATE TABLE invoices (
  id BIGSERIAL PRIMARY KEY,
  institution_id UUID NOT NULL REFERENCES institutions(id),
  invoice_number VARCHAR(50) UNIQUE,
  billing_period_start DATE,
  billing_period_end DATE,
  retainer_fee NUMERIC(10,2),
  service_charges NUMERIC(10,2),
  parts_total NUMERIC(10,2),
  discount_applied NUMERIC(10,2),
  mission_donation NUMERIC(10,2),
  total_amount NUMERIC(10,2),
  invoice_date DATE,
  due_date DATE,
  payment_status ENUM('unpaid', 'partial', 'paid') DEFAULT 'unpaid',
  payment_date DATE,
  notes TEXT,
  created_at TIMESTAMP
);
```

### 1.5 Maintenance Schedule Table
```sql
CREATE TABLE maintenance_schedules (
  id BIGSERIAL PRIMARY KEY,
  vehicle_id BIGINT NOT NULL REFERENCES fleet_vehicles(id),
  maintenance_type VARCHAR(100),
  interval_miles INT,
  interval_months INT,
  last_completed_date DATE,
  last_completed_mileage INT,
  next_due_date DATE,
  next_due_mileage INT,
  status ENUM('due', 'due_soon', 'not_due', 'overdue') DEFAULT 'not_due',
  priority INT DEFAULT 3,
  created_at TIMESTAMP
);
```

### 1.6 Emergency Dispatch Table
```sql
CREATE TABLE emergency_dispatch (
  id BIGSERIAL PRIMARY KEY,
  institution_id UUID NOT NULL,
  vehicle_id BIGINT NOT NULL REFERENCES fleet_vehicles(id),
  driver_name VARCHAR(100),
  driver_phone VARCHAR(20),
  incident_type ENUM('breakdown', 'accident', 'flat-tire', 'lockout', 'other'),
  location VARCHAR(255),
  reported_at TIMESTAMP DEFAULT NOW(),
  status ENUM('reported', 'dispatched', 'en-route', 'on-scene', 'resolved') DEFAULT 'reported',
  towing_provider VARCHAR(100),
  tow_to_location VARCHAR(255),
  completion_time TIMESTAMP,
  cost NUMERIC(10,2),
  notes TEXT,
  created_at TIMESTAMP
);
```

---

## 2. API ENDPOINTS

### Fleet Management
```
GET    /api/institutions/{id}/fleet
       - List all vehicles in institution fleet
       
POST   /api/institutions/{id}/fleet
       - Add vehicle to fleet
       
GET    /api/fleet/{vehicle_id}
       - Get vehicle details + maintenance history
       
PATCH  /api/fleet/{vehicle_id}
       - Update vehicle info (mileage, status, notes)
```

### Work Orders
```
GET    /api/institutions/{id}/work-orders
       - List work orders (filterable by status, priority)
       
POST   /api/institutions/{id}/work-orders
       - Create new work order
       
GET    /api/work-orders/{id}
       - Get work order details + photos
       
PATCH  /api/work-orders/{id}
       - Update status, add mechanic notes
       
DELETE /api/work-orders/{id}
       - Cancel work order
```

### Invoicing
```
GET    /api/institutions/{id}/invoices
       - List invoices (paginated)
       
GET    /api/invoices/{id}
       - Download invoice PDF
       
GET    /api/invoices/{id}/payment-status
       - Check payment status
```

### Analytics & Reporting
```
GET    /api/institutions/{id}/analytics/costs
       - Cost breakdown by service type, vs. retail savings
       
GET    /api/institutions/{id}/analytics/compliance
       - Compliance status dashboard
       
GET    /api/institutions/{id}/analytics/uptime
       - Fleet uptime % and maintenance compliance
       
GET    /api/institutions/{id}/analytics/mission-impact
       - Total donation amount, impact statement
```

### Emergency Dispatch
```
POST   /api/emergency-dispatch
       - Report emergency (vehicle breakdown, accident)
       - Returns incident #, ETA, dispatch team contact
       
GET    /api/emergency-dispatch/{id}
       - Track status in real-time
```

---

## 3. DASHBOARD VIEWS

### 3.1 Home / Overview
- **Fleet Health Snapshot**: X vehicles active, Y due for maintenance, Z at risk
- **Cost This Month**: $X vs. retail value $Y (savings: $Z)
- **Mission Impact**: $X donated to programs this month
- **Upcoming Maintenance**: Next 5 scheduled services

### 3.2 Fleet Management
- **Fleet Roster Table**: All vehicles, status, next maintenance, action buttons
- **Add Vehicle Form**: VIN auto-lookup, make/model/year populated
- **Maintenance Calendar**: Drag-to-schedule maintenance, color-coded by priority
- **Compliance Status**: Color-coded dashboard (green=compliant, yellow=warning, red=expired)

### 3.3 Work Orders
- **Kanban Board**: Columns = Pending → Assigned → In-Progress → Completed
- **Create Work Order**: Simple form with vehicle dropdown, service type, description
- **Work Order Detail**: Timeline of mechanic updates, parts used, photos, cost
- **Mobile Technician Integration**: Tech updates status from field (photos, notes)

### 3.4 Billing & Payments
- **Invoices List**: Filterable by date, status, amount
- **Invoice Detail**: Breakdown of retainer + services, parts list, cost vs. retail
- **Payment Options**: ACH, check, card (all available)
- **Cost Analytics**: Monthly trends, cost per vehicle, savings projection

### 3.5 Emergency Dispatch
- **Emergency Button**: Red button for immediate dispatch
- **Incident Tracking**: Real-time status, ETA, technician info, chat
- **Incident History**: Past emergencies, resolution time, cost
- **24/7 Support**: Direct phone number, chat widget

### 3.6 Reports
- **Monthly Report**: Summary of costs, maintenance, compliance, impact
- **Annual Compliance**: DOT/ADA status for entire fleet
- **Cost Justification**: Show savings vs. retail, ROI on retainer
- **Export Options**: PDF, CSV, email delivery

---

## 4. USER ROLES & PERMISSIONS

```
ADMIN (Organization manager)
  - Full access to all fleet data
  - Manage team members (drivers, maintenance coordinators)
  - Billing and contract management
  - Reports and analytics

COORDINATOR (Fleet maintenance coordinator)
  - Create/view work orders
  - Schedule maintenance
  - View invoices
  - Cannot modify contract or payments

DRIVER
  - Report breakdowns/issues
  - View vehicle assignments
  - Submit work order requests
  - Cannot view billing or other vehicles

TECHNICIAN (Already Here staff)
  - Update work order status
  - Add mechanic notes and photos
  - Close completed work orders
  - Cannot view institution billing/contracts
```

---

## 5. MOBILE APP (iOS/Android)

### Mobile Features
- **Quick Work Order**: Photo + description of issue, auto-submit
- **Maintenance Reminders**: Push notifications for upcoming services
- **Emergency Dispatch**: Immediate SOS button
- **Invoice Download**: PDF export to email
- **Real-time Tracking**: Track tow truck/service technician location

---

## 6. INTEGRATIONS

### External Systems
- **Google Maps API**: Route optimization for technicians, location tracking
- **Twilio SMS**: SMS notifications for work order status updates
- **Stripe API**: Automated billing and payment processing
- **Email Service**: Automated invoice delivery, notifications
- **PDF Generator**: Invoice and report generation

---

## 7. SECURITY & COMPLIANCE

### Data Protection
- Role-based access control (RBAC)
- End-to-end encryption for sensitive data
- Audit logs for all changes
- HIPAA compliance for senior transport programs
- PCI DSS compliance for payment processing

### Backup & Recovery
- Daily automated backups
- 30-day retention for work order history
- Disaster recovery SLA: 4-hour RTO

---

## 8. PERFORMANCE TARGETS

| Metric | Target |
|--------|--------|
| Page Load Time | <2 seconds |
| API Response | <500ms |
| Uptime | 99.5% |
| Support Response | <2 hours (business hours) |

---

## 9. TIMELINE & DEVELOPMENT PHASES

### Phase 1 (Weeks 1-3): Core Features
- Institutions & fleet management
- Work order creation & tracking
- Invoice generation
- Basic analytics

### Phase 2 (Weeks 4-6): Advanced Features
- Real-time tech dispatch
- Mobile app
- Advanced analytics & reporting
- Integration with payment systems

### Phase 3 (Weeks 7-8): Launch & Optimization
- Security audit
- Performance optimization
- User training & onboarding
- Go-live with first 3-5 institutions

---

**Spec Version**: 1.0  
**Last Updated**: 2026-06-15  
**Next Review**: 2026-06-20

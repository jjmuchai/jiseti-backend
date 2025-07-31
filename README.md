# Jiseti - Anti-Corruption Reporting Platform

## 📖 Project Overview

**Jiseti** is a comprehensive anti-corruption platform that empowers African citizens to report corruption incidents and request government intervention. The platform provides a secure, transparent, and efficient way for citizens to engage with authorities while maintaining accountability and real-time communication.

### 🎯 Mission Statement
Combat corruption across Africa by providing citizens with a digital platform to report incidents, track investigations, and hold authorities accountable through transparency and real-time communication.

---

## 🏗️ System Architecture

### Technology Stack
```
Frontend:  React 19.1.0 + Redux Toolkit + Tailwind CSS + Vite
Backend:   Flask + SQLAlchemy + PostgreSQL + JWT Authentication
Email:     SendGrid API for notifications
SMS:       Twilio API for notifications
Maps:      Google Maps API for geolocation visualization
Testing:   Jest + React Testing Library (Frontend) + Pytest (Backend)
```

### Deployment Architecture
```
Frontend (React) ←→ Backend API (Flask) ←→ PostgreSQL Database
                           ↓
                  External Services:
                  • SendGrid (Email)
                  • Twilio (SMS)
                  • Google Maps API
```

---

## 📊 Database Schema

### Complete Entity Relationship Diagram

```sql
-- Users Table
CREATE TABLE normal_users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(512) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE
);

-- Administrators Table
CREATE TABLE administrators (
    id SERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    admin_number VARCHAR(50) UNIQUE NOT NULL,
    role VARCHAR(20) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Records Table (Red-flags & Interventions)
CREATE TABLE records (
    id SERIAL PRIMARY KEY,
    type VARCHAR(20) NOT NULL CHECK (type IN ('red-flag', 'intervention')),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'under-investigation', 'resolved', 'rejected')),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    location_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    normal_user_id INTEGER REFERENCES normal_users(id) ON DELETE CASCADE,
    assigned_admin_id INTEGER REFERENCES administrators(id),
    resolution_notes TEXT,
    is_anonymous BOOLEAN DEFAULT FALSE,
    vote_count INTEGER DEFAULT 0
);

-- Media Attachments Table
CREATE TABLE media (
    id SERIAL PRIMARY KEY,
    record_id INTEGER REFERENCES records(id) ON DELETE CASCADE,
    media_type VARCHAR(10) CHECK (media_type IN ('image', 'video')),
    media_url TEXT NOT NULL,
    filename VARCHAR(255),
    file_size INTEGER,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Votes Table (Public Support System)
CREATE TABLE votes (
    id SERIAL PRIMARY KEY,
    record_id INTEGER REFERENCES records(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES normal_users(id) ON DELETE CASCADE,
    vote_type VARCHAR(10) CHECK (vote_type IN ('support', 'urgent')) DEFAULT 'support',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(record_id, user_id)
);

-- Status History Table (Audit Trail)
CREATE TABLE status_history (
    id SERIAL PRIMARY KEY,
    record_id INTEGER REFERENCES records(id) ON DELETE CASCADE,
    old_status VARCHAR(50),
    new_status VARCHAR(50),
    changed_by INTEGER REFERENCES administrators(id),
    change_reason TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Email/SMS Notifications Log
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    record_id INTEGER REFERENCES records(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES normal_users(id) ON DELETE CASCADE,
    notification_type VARCHAR(20) CHECK (notification_type IN ('email', 'sms', 'both')),
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivery_status VARCHAR(20) DEFAULT 'pending' CHECK (delivery_status IN ('pending', 'sent', 'failed')),
    external_id VARCHAR(100) -- SendGrid/Twilio message ID
);
```

---

## 🔗 Complete API Endpoints Documentation

### Authentication Endpoints

```python
# User Authentication
POST   /api/auth/signup              # User registration
POST   /api/auth/login               # User login
POST   /api/auth/logout              # User logout
POST   /api/auth/refresh             # Refresh JWT token
POST   /api/auth/forgot-password     # Password reset request
POST   /api/auth/reset-password      # Password reset confirmation
GET    /api/auth/verify-email        # Email verification

# Admin Authentication
POST   /api/admin/signup             # Admin registration
POST   /api/admin/login              # Admin login
POST   /api/admin/logout             # Admin logout

# Anonymous Reporting
POST   /api/public/report            # Anonymous report submission
GET    /api/public/report/:token     # Verify anonymous report
```

### Record Management Endpoints

```python
# User Record Operations
GET    /api/records/my               # Get user's own records (paginated)
POST   /api/records                  # Create new record
GET    /api/records/:id              # Get specific record details
PATCH  /api/records/:id              # Update record (draft only)
DELETE /api/records/:id              # Delete record (draft only)

# Public Record Viewing
GET    /api/public/records           # Get all public records (anonymous viewing)
GET    /api/public/records/:id       # Get public record details
POST   /api/records/:id/vote         # Vote/support a record
DELETE /api/records/:id/vote         # Remove vote

# Admin Record Operations
GET    /api/admin/records            # Get all records (admin view)
PATCH  /api/admin/records/:id/status # Update record status
GET    /api/admin/records/stats      # Platform statistics
POST   /api/admin/records/:id/assign # Assign record to admin
```

### Media & Geolocation Endpoints

```python
# Media Management
POST   /api/records/:id/media        # Upload media to record
DELETE /api/media/:id               # Remove media attachment
GET    /api/media/:id                # Get media details

# Geolocation Services
POST   /api/records/:id/location     # Update record location
GET    /api/locations/nearby         # Get nearby records (for maps)
GET    /api/locations/geocode        # Reverse geocoding service
```

### User Management Endpoints

```python
# User Profile
GET    /api/user/profile             # Get current user profile
PATCH  /api/user/profile             # Update user profile
DELETE /api/user/account             # Delete user account
GET    /api/user/notifications       # Get notification preferences
PATCH  /api/user/notifications       # Update notification settings

# Admin User Management
GET    /api/admin/users              # Get all users (admin only)
PATCH  /api/admin/users/:id/status   # Activate/deactivate user
GET    /api/admin/users/:id/records  # Get user's records (admin view)
```

### Notification Endpoints

```python
# Notification Management
GET    /api/notifications            # Get user's notifications
PATCH  /api/notifications/:id/read   # Mark notification as read
POST   /api/notifications/test       # Test notification delivery

# Admin Notifications
POST   /api/admin/notifications/broadcast  # Send broadcast message
GET    /api/admin/notifications/logs       # View notification logs
```

### Analytics & Reporting Endpoints

```python
# Public Statistics
GET    /api/stats/public             # Public platform statistics
GET    /api/stats/regions            # Records by geographical region

# Admin Analytics
GET    /api/admin/analytics/dashboard      # Admin dashboard stats
GET    /api/admin/analytics/trends         # Trend analysis
GET    /api/admin/analytics/performance    # Platform performance metrics
POST   /api/admin/reports/generate         # Generate custom reports
```

---

## 🖥️ Frontend Application Architecture

### Redux Store Structure

```javascript
// store/index.js
const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
    records: recordsSlice.reducer,
    ui: uiSlice.reducer,
    notifications: notificationsSlice.reducer,
    maps: mapsSlice.reducer,
    admin: adminSlice.reducer
  }
});

// store/slices/authSlice.js
const authSlice = createSlice({
  name: 'auth',
  initialState: {
    user: null,
    token: null,
    isAuthenticated: false,
    role: null, // 'user' | 'admin' | null
    loading: false,
    error: null
  },
  reducers: {
    loginStart, loginSuccess, loginFailure,
    logout, refreshToken, updateProfile
  }
});

// store/slices/recordsSlice.js
const recordsSlice = createSlice({
  name: 'records',
  initialState: {
    myRecords: [],
    publicRecords: [],
    selectedRecord: null,
    filters: { status: 'all', type: 'all' },
    pagination: { page: 1, totalPages: 1 },
    loading: false,
    error: null
  },
  reducers: {
    fetchRecordsStart, fetchRecordsSuccess,
    createRecord, updateRecord, deleteRecord,
    voteRecord, setFilters, setSelectedRecord
  }
});
```

### Component Structure

```
src/
├── components/
│   ├── common/
│   │   ├── Layout.jsx
│   │   ├── Navbar.jsx
│   │   ├── Footer.jsx
│   │   ├── Loading.jsx
│   │   ├── ErrorBoundary.jsx
│   │   └── ConfirmDialog.jsx
│   ├── auth/
│   │   ├── LoginForm.jsx
│   │   ├── RegisterForm.jsx
│   │   ├── ForgotPassword.jsx
│   │   └── ProtectedRoute.jsx
│   ├── records/
│   │   ├── RecordCard.jsx
│   │   ├── RecordForm.jsx
│   │   ├── RecordDetails.jsx
│   │   ├── RecordsList.jsx
│   │   ├── StatusBadge.jsx
│   │   └── VoteButton.jsx
│   ├── maps/
│   │   ├── GoogleMap.jsx
│   │   ├── RecordMarker.jsx
│   │   └── LocationPicker.jsx
│   ├── media/
│   │   ├── ImageUpload.jsx
│   │   ├── VideoUpload.jsx
│   │   ├── MediaPreview.jsx
│   │   └── MediaGallery.jsx
│   └── admin/
│       ├── AdminSidebar.jsx
│       ├── StatsCards.jsx
│       ├── RecordManagement.jsx
│       ├── UserManagement.jsx
│       └── AnalyticsDashboard.jsx
├── pages/
│   ├── public/
│   │   ├── LandingPage.jsx
│   │   ├── AboutPage.jsx
│   │   ├── ContactPage.jsx
│   │   ├── PublicRecords.jsx
│   │   └── AnonymousReport.jsx
│   ├── user/
│   │   ├── Dashboard.jsx
│   │   ├── MyRecords.jsx
│   │   ├── CreateRecord.jsx
│   │   ├── RecordDetails.jsx
│   │   └── Profile.jsx
│   └── admin/
│       ├── AdminDashboard.jsx
│       ├── RecordsManagement.jsx
│       ├── UserManagement.jsx
│       ├── Analytics.jsx
│       └── Settings.jsx
├── hooks/
│   ├── useAuth.js
│   ├── useRecords.js
│   ├── useGeolocation.js
│   ├── useNotifications.js
│   └── useLocalStorage.js
├── services/
│   ├── api.js
│   ├── authService.js
│   ├── recordsService.js
│   ├── mapsService.js
│   └── notificationService.js
├── utils/
│   ├── constants.js
│   ├── validators.js
│   ├── formatters.js
│   └── helpers.js
└── tests/
    ├── components/
    ├── pages/
    ├── hooks/
    ├── services/
    └── utils/
```

---

## 🎯 Detailed User Interaction Flows

### 🚀 **Flow 1: Anonymous User Visits Platform**

```
Landing Page → Browse Public Records → (Optional) Anonymous Report → View Record Details
     ↓
"Browse without account" - See all records with locations on map
"Report Red Flag" - Submit anonymous report with temporary tracking
"Sign Up" - Create account for full features
```

**Expected Behavior:**
- View corruption reports on public map
- Filter by location, type, urgency level
- Submit anonymous reports with temporary tracking token
- Receive email with tracking link (no account needed)

### 🔐 **Flow 2: User Registration & Authentication**

```
Landing Page → Register → Email Verification → Login → Dashboard
     ↓
Gmail validation → Password strength check → Welcome email → Profile setup
```

**Expected Behavior:**
- Email must be Gmail format (@gmail.com)
- Password minimum 8 characters with complexity rules
- Email verification required before full access
- Welcome email with platform tutorial
- Automatic login after verification

### 📝 **Flow 3: Creating Records (Red-flag/Intervention)**

```
Dashboard → "Create Report" → Select Type → Fill Details → Add Location → Add Media → Submit
     ↓
Real-time validation → GPS capture → Media upload → Email confirmation → Status tracking
```

**Detailed Steps:**
1. **Record Type Selection:**
   - Red-flag (corruption incident)
   - Intervention (government action needed)

2. **Form Completion:**
   - Title (required, max 200 chars)
   - Description (required, rich text editor)
   - Urgency level (low/medium/high/critical)
   - Category selection (bribery, embezzlement, infrastructure, etc.)

3. **Geolocation Integration:**
   - Auto-detect current location
   - Manual coordinate entry
   - Address search with geocoding
   - Map picker for precise location

4. **Media Attachments:**
   - Image upload (max 5 images, 10MB each)
   - Video upload (max 2 videos, 100MB each)
   - File format validation
   - Automatic thumbnail generation

5. **Submission & Confirmation:**
   - Real-time validation feedback
   - Preview before submission
   - Email confirmation sent
   - Unique tracking ID generated

### 🗺️ **Flow 4: Public Records Exploration**

```
Public Map View → Filter Records → Select Marker → View Details → Vote/Support → Share
     ↓
Interactive map → Category filters → Record details modal → Engagement actions
```

**Map Interface Features:**
- **Clustered Markers:** Group nearby records
- **Color Coding:** Status-based marker colors
- **Filter Panel:** By type, status, date range, urgency
- **Search Bar:** Location or keyword search
- **Layer Controls:** Toggle record types

**Record Details Modal:**
- Anonymous viewing (no creator identity)
- Media gallery with lightbox
- Vote count and support level
- Share functionality
- Report inappropriate content

### 👨‍💼 **Flow 5: Admin Record Management**

```
Admin Login → Dashboard Overview → Records Queue → Investigation → Status Update → Communication
     ↓
Triage new reports → Assign to investigators → Track progress → Update status → Notify users
```

**Admin Dashboard Features:**
1. **Overview Statistics:**
   - Total reports (daily/weekly/monthly)
   - Status distribution charts
   - Geographic heat map
   - Response time metrics

2. **Records Management:**
   - Queue of new reports
   - Filter by priority, location, type
   - Bulk status updates
   - Assignment to team members

3. **Investigation Tools:**
   - Add internal notes
   - Upload investigation evidence
   - Set follow-up reminders
   - Track resolution timeline

4. **Communication Center:**
   - Template responses
   - Bulk notifications
   - SMS/Email delivery status
   - User feedback collection

### 📱 **Flow 6: Real-time Notifications**

```
Status Change → Background Service → Multi-channel Delivery → User Acknowledgment
     ↓
Database trigger → Email + SMS → Push notification → Read receipts
```

**Notification Types:**
- **Status Updates:** "Under investigation", "Resolved", "Rejected"
- **Assignment Notifications:** "Your report has been assigned to [Admin]"
- **Follow-up Requests:** "Additional information needed"
- **Resolution Updates:** "Your report has been resolved - view details"

**Delivery Channels:**
- **Email:** HTML formatted with action buttons
- **SMS:** Concise text with tracking link
- **In-app:** Real-time notifications with badges
- **Push:** Browser/mobile push notifications

---

## 🔧 Backend Architecture Details

### Flask Application Structure

```python
# app.py - Main application factory
def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config.from_object(Config)
    
    # Extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    migrate.init_app(app, db)
    
    # Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(records_bp, url_prefix='/api/records')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(public_bp, url_prefix='/api/public')
    
    # Error handlers
    @app.errorhandler(404)
    @app.errorhandler(500)
    def handle_errors(error):
        return jsonify({'error': str(error)}), error.code
    
    return app

# blueprints/auth.py - Authentication routes
@auth_bp.route('/signup', methods=['POST'])
def signup():
    # Email validation (Gmail only)
    # Password strength validation
    # User creation
    # Email verification send
    # JWT token generation
    
@auth_bp.route('/login', methods=['POST'])
def login():
    # Credential validation
    # JWT token generation
    # Last login update
    # Login attempt logging

# blueprints/records.py - Record management
@records_bp.route('/', methods=['POST'])
@jwt_required()
def create_record():
    # Input validation
    # Media URL validation
    # Geolocation validation
    # Record creation
    # Media attachment
    # Email notification
    # Admin assignment (if urgent)

# blueprints/public.py - Public endpoints
@public_bp.route('/records', methods=['GET'])
def get_public_records():
    # Anonymous access
    # Privacy filtering (hide user details)
    # Pagination
    # Geographic filtering
    # Status filtering

# services/notification_service.py
class NotificationService:
    def send_status_update(self, user, record, old_status, new_status):
        # Email composition
        # SMS composition
        # Template selection
        # Multi-channel delivery
        # Delivery confirmation
        # Retry logic for failures
```

### Background Tasks & Services

```python
# services/email_service.py
class EmailService:
    def __init__(self):
        self.sendgrid = SendGridAPIClient(api_key=config.SENDGRID_API_KEY)
    
    def send_status_update_email(self, user_email, record_title, status_change):
        # HTML template rendering
        # Personalization
        # Delivery tracking
        # Bounce handling

# services/sms_service.py
class SMSService:
    def __init__(self):
        self.twilio = Client(config.TWILIO_SID, config.TWILIO_TOKEN)
    
    def send_status_update_sms(self, phone_number, message):
        # Message composition
        # Character limit handling
        # Delivery confirmation
        # Cost tracking

# services/geolocation_service.py
class GeolocationService:
    def reverse_geocode(self, latitude, longitude):
        # Google Maps API integration
        # Address resolution
        # Location validation
        # Caching for performance
    
    def validate_coordinates(self, lat, lng):
        # Coordinate range validation
        # Geographic boundary checks
        # Precision validation
```

---

## 🧪 Testing Strategy

### Frontend Testing (Jest + React Testing Library)

```javascript
// __tests__/components/RecordForm.test.jsx
describe('RecordForm', () => {
  test('validates required fields', () => {
    // Form validation testing
  });
  
  test('handles geolocation integration', () => {
    // GPS functionality testing
  });
  
  test('uploads media successfully', () => {
    // File upload testing
  });
});

// __tests__/pages/Dashboard.test.jsx
describe('User Dashboard', () => {
  test('displays user records correctly', () => {
    // Data display testing
  });
  
  test('handles record creation flow', () => {
    // User interaction testing
  });
});

// __tests__/services/api.test.js
describe('API Service', () => {
  test('handles authentication properly', () => {
    // API authentication testing
  });
  
  test('manages error responses', () => {
    // Error handling testing
  });
});
```

### Backend Testing (Pytest)

```python
# tests/test_auth.py
class TestAuthentication:
    def test_user_registration(self):
        # User signup flow testing
        
    def test_admin_login(self):
        # Admin authentication testing
        
    def test_jwt_token_validation(self):
        # Token security testing

# tests/test_records.py
class TestRecordManagement:
    def test_create_record_validation(self):
        # Input validation testing
        
    def test_status_update_permissions(self):
        # Authorization testing
        
    def test_media_attachment(self):
        # File handling testing

# tests/test_notifications.py
class TestNotifications:
    def test_email_delivery(self):
        # Email service testing
        
    def test_sms_delivery(self):
        # SMS service testing
```

---

## 🚀 Deployment & Production Setup

### Environment Configuration

```bash
# Frontend Environment (.env)
VITE_API_BASE_URL=http://localhost:5000/api
VITE_GOOGLE_MAPS_API_KEY=your_google_maps_key
VITE_APP_NAME=Jiseti
VITE_ENVIRONMENT=development

# Backend Environment (.env)
FLASK_ENV=development
DATABASE_URL=postgresql://user:password@localhost:5432/jiseti_db
JWT_SECRET_KEY=your_super_secret_jwt_key
SENDGRID_API_KEY=your_sendgrid_api_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
GOOGLE_MAPS_API_KEY=your_google_maps_key
FROM_EMAIL=noreply@jiseti.go.ke
```

### Database Migrations

```python
# alembic/versions/001_initial_schema.py
def upgrade():
    # Create all tables
    # Add initial indexes
    # Set up constraints
    # Create default admin user

def downgrade():
    # Reverse migration
```

---

## 📱 Mobile Responsiveness Requirements

### Responsive Breakpoints

```css
/* Tailwind CSS responsive design */
sm: 640px   /* Mobile landscape */
md: 768px   /* Tablet */
lg: 1024px  /* Desktop */
xl: 1280px  /* Large desktop */
2xl: 1536px /* Extra large */

/* Key responsive features needed: */
- Mobile-first design approach
- Touch-friendly button sizes (44px minimum)
- Swipe gestures for record navigation
- Collapsible navigation menu
- Optimized image loading for mobile
- GPS integration for mobile reporting
```

### Progressive Web App Features

```javascript
// service-worker.js - Offline functionality
self.addEventListener('fetch', event => {
  // Cache API responses
  // Offline record creation
  // Background sync when online
});

// manifest.json - PWA configuration
{
  "name": "Jiseti - Anti-Corruption Platform",
  "short_name": "Jiseti",
  "start_url": "/",
  "display": "standalone",
  "theme_color": "#10b981",
  "background_color": "#ffffff",
  "icons": [...]
}
```

---

## 🔒 Security Implementation

### Authentication Security

```python
# Password Security
- Minimum 8 characters
- At least 1 uppercase, 1 lowercase, 1 number, 1 special character
- Password hashing with bcrypt (cost factor 12)
- Password history (prevent reuse of last 5 passwords)

# JWT Security
- Short-lived access tokens (15 minutes)
- Refresh token rotation
- Token blacklisting on logout
- Secure HTTP-only cookies for token storage

# Rate Limiting
- Login attempts: 5 per minute per IP
- Record creation: 10 per hour per user
- Anonymous reports: 3 per hour per IP
```

### Data Privacy & Protection

```python
# Privacy Measures
- Anonymous reporting (no user tracking)
- Personal data encryption at rest
- Automatic data anonymization after resolution
- GDPR compliance for data deletion requests
- Audit logging for all admin actions

# Input Sanitization
- SQL injection prevention
- XSS protection
- File upload validation
- Media URL verification
- Geolocation boundary validation
```

---

## 📈 Performance Optimization

### Frontend Optimization

```javascript
// Code Splitting
const AdminDashboard = lazy(() => import('./pages/admin/AdminDashboard'));
const PublicRecords = lazy(() => import('./pages/public/PublicRecords'));

// Image Optimization
- Lazy loading for images
- WebP format with fallbacks
- Responsive image sizing
- CDN integration for media

// Bundle Optimization
- Tree shaking for unused code
- Component-level code splitting
- Service worker caching
- Gzip compression
```

### Backend Optimization

```python
# Database Optimization
- Indexed queries on frequently searched columns
- Connection pooling
- Query optimization and caching
- Pagination for large datasets

# API Optimization
- Response compression
- Caching headers
- Rate limiting
- Background task processing

# Media Handling
- CDN integration for file storage
- Image compression pipeline
- Video transcoding for web delivery
- Progressive loading for large files
```

---

## 🎮 User Experience Enhancements

### Interactive Features

```javascript
// Real-time Updates
- WebSocket connection for live status updates
- Push notifications for mobile browsers
- Live comment system on records
- Real-time voting and support counts

// Advanced Search & Filtering
- Full-text search across records
- Geographical radius search
- Date range filtering
- Category-based filtering
- Saved search preferences

// Social Features
- Record sharing on social media
- Public discussion threads
- Expert verification system
- Community moderation tools
```

### Accessibility Features

```javascript
// WCAG 2.1 AA Compliance
- Keyboard navigation support
- Screen reader optimization
- High contrast mode
- Font size adjustment
- Audio descriptions for media
- Multi-language support (English, Swahili, French)
```



This comprehensive documentation provides the roadmap for completing Jiseti according to all requirements while maintaining high code quality, security, and user experience standards. Each section can be implemented incrementally while maintaining a working application throughout the development process.
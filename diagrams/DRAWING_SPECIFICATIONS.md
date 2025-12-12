# Drawing Specifications for HomeGuard Diagrams

This document provides detailed specifications for recreating the HomeGuard diagrams in drawing tools like Draw.io, Lucidchart, or Visio.

## 1. Use Case Diagram Specifications

### Elements Required:
- **1 Actor**: Administrator (stick figure or icon)
- **12 Use Cases**: Rectangles with rounded corners
- **4 Packages/Groups**: Authentication, Device Management, Alert Management, Settings
- **Association Lines**: Solid lines connecting actor to use cases
- **Extend Relationships**: Dashed arrows with <<extends>> label

### Use Cases to Include:
1. UC-1: Login to Dashboard
2. UC-2: View User Profile
3. UC-3: View Device List
4. UC-4: View Device Details
5. UC-5: Block Device
6. UC-6: Unblock Device
7. UC-7: View Alerts
8. UC-8: Acknowledge Alert
9. UC-9: View Alert Statistics
10. UC-10: Receive Real-time Alert
11. UC-11: Configure Settings
12. UC-12: View Settings

### Layout:
- Actor on the left side
- System boundary rectangle in center
- Use cases grouped in packages
- Extend relationships: UC-10 extends UC-7, UC-4 extends UC-3

### Colors:
- Actor: Blue (#4A90E2)
- Authentication package: Light Blue (#E8F4F8)
- Device Management package: Light Green (#E8F5E9)
- Alert Management package: Light Orange (#FFF3E0)
- Settings package: Light Purple (#F3E5F5)

---

## 2. Activity Diagram - Login Process

### Swimlanes:
- **Frontend** (top)
- **Backend** (middle)
- **Database** (bottom)

### Start/End Nodes:
- 1 Start node (filled circle)
- Multiple End nodes (filled circle with border)

### Activities (Rectangles):
1. User navigates to login page
2. User enters email and password
3. User clicks "Login" button
4. Frontend sends POST /api/auth/login
5. Backend receives login request
6. Backend queries MongoDB for user
7. Backend verifies password using bcrypt
8. Backend creates JWT tokens
9. Backend updates last_login timestamp
10. Frontend stores tokens
11. Frontend calls GET /api/auth/me
12. Frontend stores user data
13. Frontend redirects to Dashboard

### Decision Diamonds:
1. User exists? (Yes/No)
2. Password correct? (Yes/No)
3. User is admin? (Yes/No)

### Flow:
- Sequential flow with decision points
- Error paths lead to "Display error message" and End
- Success path leads to Dashboard

### Colors:
- Normal flow: Blue (#E8F4F8)
- Error paths: Red (#FFCDD2)
- Decision points: Yellow (#FFF9C4)
- Success: Green (#C8E6C9)

---

## 3. Activity Diagram - Alert Detection

### Swimlanes:
- **Orange Pi** (left)
- **File System** (left-center)
- **Alert Monitor** (center)
- **WebSocket Manager** (right-center)
- **Push Service** (right)
- **Frontend** (far right)

### Activities:
1. Orange Pi detects anomaly
2. Write alert to alerts.json
3. Alert Monitor checks file (every 2s)
4. Read alerts.json
5. Compare alert IDs
6. Extract alert data
7. Format for WebSocket
8. Broadcast to /ws/alerts channel
9. Format for Push Notification
10. Get active subscriptions
11. Send push notifications
12. Update tracked alert IDs

### Decision Points:
1. New alerts found? (Yes/No)
2. Clients connected? (Yes/No)
3. Subscriptions exist? (Yes/No)
4. Notification sent successfully? (Yes/No)

### Parallel Paths:
- WebSocket notification path (parallel with Push notification)
- Both paths execute simultaneously

### Colors:
- Alert detection: Orange (#FFF3E0)
- WebSocket path: Light Orange (#FFE0B2)
- Push path: Light Orange (#FFE0B2)
- Decision points: Yellow (#FFF9C4)

---

## 4. Activity Diagram - Device Blocking

### Swimlanes:
- **Frontend** (top)
- **Backend** (middle)
- **Firewall Controller** (middle-bottom)
- **Database** (bottom)

### Activities:
1. Administrator clicks "Block Device"
2. Frontend sends POST /api/devices/{id}/block
3. Backend validates JWT token
4. Backend checks user role
5. Backend queries device
6. FirewallController.block_device()
7. Create nftables rule (IP)
8. Create nftables rule (MAC)
9. Store blocked device
10. Update device status to BLOCKED
11. Set is_blocked = true
12. Format device update for WebSocket
13. Broadcast to /ws/devices
14. Frontend updates UI

### Decision Points:
1. Token valid? (Yes/No)
2. User is admin? (Yes/No)
3. Device found? (Yes/No)
4. Firewall rule created? (Yes/No)

### Partitions:
- Firewall Enforcement (group activities 6-9)
- Database Update (group activities 10-11)
- Real-time Notification (group activities 12-14)

### Colors:
- Normal flow: Green (#E8F5E9)
- Error paths: Red (#FFCDD2)
- Decision points: Yellow (#FFF9C4)
- Success: Light Green (#C8E6C9)

---

## 5. State Machine Diagram - Device States

### States (Rounded Rectangles):
1. **Offline** (Gray)
   - No network activity
   - Not visible in network

2. **Active** (Green)
   - Sending/receiving data
   - Normal communication
   - Last seen < 5 minutes

3. **Idle** (Yellow)
   - Connected but inactive
   - No recent traffic
   - Last seen > 5 minutes

4. **Blocked** (Red)
   - Firewall rule active
   - nftables blocking traffic
   - is_blocked = true
   - Status = BLOCKED

### Transitions (Arrows with Labels):
- Offline → Active: "Device connects and sends traffic"
- Offline → Idle: "Device connects but no traffic"
- Active → Idle: "No traffic for 5+ minutes"
- Active → Blocked: "Administrator blocks or auto-block triggered"
- Active → Offline: "Device disconnects"
- Idle → Active: "Traffic resumes"
- Idle → Blocked: "Administrator blocks or anomaly detected"
- Idle → Offline: "Device disconnects"
- Blocked → Active: "Administrator unblocks"
- Blocked → Offline: "Device disconnects"

### Initial State:
- [*] → Offline

### Colors:
- Offline: Light Gray (#D3D3D3)
- Active: Light Green (#C8E6C9)
- Idle: Light Yellow (#FFF9C4)
- Blocked: Light Coral (#FFCDD2)

---

## 6. Sequence Diagram - Alert Flow

### Participants (Lifelines):
1. Administrator
2. Orange Pi Monitoring
3. alerts.json File
4. Alert Monitor Service
5. WebSocket Manager
6. Push Notification Service
7. Frontend Dashboard
8. MongoDB

### Messages (Arrows):
1. Orange Pi → File: "Write new alert to alerts.json"
2. Monitor → File: "Check file modification (every 2s)"
3. File → Monitor: "File modified"
4. Monitor → File: "Read alerts.json"
5. File → Monitor: "Return alert data"
6. Monitor → Monitor: "Compare alert IDs"
7. Monitor → WS: "Send alert data"
8. WS → Frontend: "Broadcast to /ws/alerts channel"
9. Monitor → Push: "Send alert for push notification"
10. Push → DB: "Get active subscriptions"
11. DB → Push: "Return subscriptions list"
12. Admin → Frontend: "Views alert in dashboard"
13. Frontend → Admin: "Display alert details"
14. Admin → Frontend: "Clicks Acknowledge"
15. Frontend → DB: "PATCH /api/alerts/{id}/acknowledge"
16. DB → Frontend: "Confirmation"

### Activation Boxes:
- Show activation for: File, WS, Frontend, Push, DB during message processing

### Loops:
- Loop: "For each subscription" around push notification sending

### Notes:
- "Alert Detection" over OrangePi-File
- "File Monitoring" over Monitor-File
- "WebSocket Notification" over Monitor-Frontend
- "Push Notification" over Monitor-DB
- "User Interaction" over Admin-DB

### Colors:
- Messages: Blue (#4A90E2)
- Activation boxes: Light Blue (#E8F4F8)
- Notes: Yellow (#FFF9C4)

---

## General Drawing Guidelines

### Fonts:
- Use Arial or similar sans-serif font
- Title: 14-16pt Bold
- Labels: 10-12pt Regular
- Notes: 9-10pt Italic

### Line Styles:
- Solid lines: Associations, normal flow
- Dashed lines: Extend relationships, optional flows
- Arrows: Show direction of flow/interaction

### Spacing:
- Maintain consistent spacing between elements
- Group related elements together
- Use alignment guides for clean appearance

### Export Settings:
- Resolution: 300 DPI for print
- Format: PNG or SVG for documents
- Background: White or transparent

### Tools-Specific Notes:

**Draw.io / diagrams.net:**
- Use UML shapes library
- Enable snap-to-grid
- Use layers for organization

**Lucidchart:**
- Use UML template
- Enable smart connectors
- Use containers for grouping

**Visio:**
- Use UML Model Diagram template
- Enable shape-to-shape connections
- Use containers for swimlanes

---

## Checklist for Each Diagram

- [ ] All required elements included
- [ ] Correct colors applied
- [ ] Labels and text clear and readable
- [ ] Proper relationships/connections shown
- [ ] Decision points clearly marked
- [ ] Start/End nodes present
- [ ] Consistent styling throughout
- [ ] Legend/key included if needed
- [ ] Title and diagram number included


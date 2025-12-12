# HomeGuard System Diagrams

This folder contains all diagrams for the HomeGuard project report, provided in multiple formats for flexibility.

## 🎯 Quick Start - Alternative Tools

**Don't want to use PlantUML?** Check out **[ALTERNATIVE_TOOLS.md](./ALTERNATIVE_TOOLS.md)** for:
- **Draw.io** (Recommended - Best quality, free, no registration)
- **Mermaid Live Editor** (Code-based, similar to PlantUML)
- **Lucidchart** (Professional templates)
- And 7+ more alternatives!

**Quick Links:**
- 🌐 [Draw.io - Create Diagrams Online](https://app.diagrams.net/)
- 🌐 [Mermaid Live Editor](https://mermaid.live/)
- 🌐 [PlantText - PlantUML Online](https://www.planttext.com/)

## 📋 Diagram List

### 1. Use Case Diagram
- **File**: `01_UseCase_Diagram.puml` / `01_UseCase_Diagram.mmd`
- **Purpose**: Shows all use cases and the Administrator actor
- **Shows**: 12 use cases organized into Authentication, Device Management, Alert Management, and Settings

### 2. Activity Diagrams

#### 2.1 Login Process
- **File**: `02_Activity_Login.puml` / `02_Activity_Login.mmd`
- **Purpose**: Detailed workflow of user authentication
- **Shows**: Complete login flow from user input to dashboard access

#### 2.2 Alert Detection and Notification
- **File**: `03_Activity_AlertDetection.puml` / `03_Activity_AlertDetection.mmd`
- **Purpose**: Flow of alert detection and multi-channel notification
- **Shows**: File monitoring, WebSocket broadcasting, and push notification delivery

#### 2.3 Device Blocking Workflow
- **File**: `04_Activity_DeviceBlocking.puml` / `04_Activity_DeviceBlocking.mmd`
- **Purpose**: Complete process of blocking a device
- **Shows**: Authentication, firewall rule creation, database update, and real-time notification

### 3. State Machine Diagram
- **File**: `05_StateMachine_DeviceStates.puml` / `05_StateMachine_DeviceStates.mmd`
- **Purpose**: Device state transitions
- **Shows**: Offline → Active → Idle → Blocked states and transitions

### 4. Sequence Diagram
- **File**: `06_Sequence_AlertFlow.puml` / `06_Sequence_AlertFlow.mmd`
- **Purpose**: Interaction sequence for alert detection and notification
- **Shows**: Component interactions from Orange Pi to Frontend

## 🛠️ How to Use

### PlantUML Files (.puml)
1. **Online**: Use [PlantUML Online Server](http://www.plantuml.com/plantuml/uml/)
2. **VS Code**: Install "PlantUML" extension
3. **IntelliJ**: Install PlantUML plugin
4. **Command Line**: Install PlantUML and run `plantuml diagram.puml`

### Mermaid Files (.mmd)
1. **Online**: Use [Mermaid Live Editor](https://mermaid.live/)
2. **VS Code**: Install "Markdown Preview Mermaid Support" extension
3. **GitHub/GitLab**: Mermaid diagrams render automatically in markdown
4. **Documentation**: Can be embedded in markdown files

### Drawing Tools
See `DRAWING_SPECIFICATIONS.md` for detailed specifications to recreate these diagrams in:
- Draw.io / diagrams.net
- Lucidchart
- Microsoft Visio
- Other UML tools

## 📊 Diagram Descriptions

### Use Case Diagram
The use case diagram illustrates all interactions between the Administrator and the HomeGuard system. It shows 12 primary use cases organized into four functional groups:
- **Authentication**: Login and profile viewing
- **Device Management**: Viewing, blocking, and unblocking devices
- **Alert Management**: Viewing, acknowledging, and receiving alerts
- **Settings**: System configuration

### Activity Diagrams
Activity diagrams show the detailed step-by-step workflows for key system operations:

**Login Process**: Demonstrates the complete authentication flow including credential validation, JWT token generation, and session establishment.

**Alert Detection**: Shows how the system monitors for new alerts, processes them, and delivers notifications through multiple channels (WebSocket, Push, Browser).

**Device Blocking**: Illustrates the security enforcement workflow from user action through firewall rule creation to real-time status updates.

### State Machine Diagram
The state machine diagram models device lifecycle states:
- **Offline**: Device not connected to network
- **Active**: Device actively communicating
- **Idle**: Device connected but inactive
- **Blocked**: Device blocked by firewall rules

Transitions show how devices move between states based on network activity, user actions, and security events.

### Sequence Diagram
The sequence diagram shows the temporal flow of alert detection and notification, illustrating interactions between:
- Orange Pi monitoring scripts
- File system (alerts.json)
- Alert Monitor service
- WebSocket Manager
- Push Notification Service
- Frontend Dashboard
- MongoDB

## 📝 Notes

- All diagrams are based on the actual HomeGuard implementation
- Diagrams follow UML 2.5 standards where applicable
- Color coding is consistent across diagrams:
  - Blue: Authentication/System
  - Green: Device Management
  - Orange: Alerts
  - Purple: Settings
  - Red: Errors/Blocked states
  - Yellow: Decision points

## 🔄 Updates

When updating diagrams:
1. Update both PlantUML and Mermaid versions
2. Update this README if new diagrams are added
3. Update DRAWING_SPECIFICATIONS.md if structure changes


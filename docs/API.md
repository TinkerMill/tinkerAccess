# Rust Server API & Database Structure

*Note: This documentation describes the new Rust server (`tinker-access-server-rs`) implementation. It is intended to replace the original Python server.*

## Database Layout (SQLite via SeaORM)

The application uses a SQLite database with a schema defined by the SeaORM entities in the source code.

### Tables

#### `user`
*Defined in `src/users.rs`*
*   `id` (Integer, Primary Key): Unique user ID.
*   `name` (Text): User's full name.
*   `code` (Text): The RFID badge code.
*   `status` (Text): User's standing ('A', 'I', 'S').

#### `device`
*Defined in `src/devices.rs`*
*   `id` (Integer, Primary Key): Unique device ID.
*   `name` (Text): Display name of the device.
*   `all_users` (Boolean): If true, all active users can access this device.
*   `lockout` (Integer): Current state of the device (0: Unlimited, 1: Limited, 2: Locked).
*   `lockout_start` (Time): Start time for limited access.
*   `lockout_end` (Time): End time for limited access.

#### `device_access`
*Defined in `src/devices.rs`*
*   `user_id` (Integer, Foreign Key): Links to `user.id`.
*   `device_id` (Integer, Foreign Key): Links to `device.id`.
*   `trainer` (Boolean): If true, this user is a trainer for this device.

#### `newuser`
*Defined in `src/newusers.rs`*
*   `id` (Integer, Primary Key)
*   `code` (Text): The unknown badge code scanned.
*   `device_id` (Integer, Foreign Key): The device where the scan occurred.

#### `log`
*   **Note:** This table is part of the original Python server schema but is **not yet implemented** in the Rust version. The `get_device_usage_summary` function is a placeholder.

---

## Hardware Client API (WebSocket)

The Rust server replaces the old HTTP API with a modern WebSocket-based protocol for real-time, bidirectional communication with hardware clients.

| Item | Description |
| :--- | :--- |
| **Endpoint** | `/ws` |
| **Handler** | `websocket_dispatcher.rs` |
| **Protocol** | JSON messages conforming to the `TAEvent` and `TACommand` enums. |

### Events (Client -> Server)
*Defined in `src/messages/events.rs`*

| Event | Purpose |
| :--- | :--- |
| `EventReportCard` | Sent when an RFID badge is swiped. Contains the `card_id`. |
| `EventReportBinary` | Sent when a binary input changes (e.g., machine power on/off). |
| `GetStateCmd` | Sent by a client on startup to request its initial state from the server. |

### Commands (Server -> Client)
*Defined in `src/messages/commands.rs`*

| Command | Purpose |
| :--- | :--- |
| `SetStateCmd` | Instructs the client to change its state (e.g., turn a relay on/off). |
| `SetDisplayCmd` | Sends text to be displayed on the client's LCD screen. |
| `SetLedCmd` | Instructs the client to set the color of its status LED. |

---

## Web Application Routes (Leptos)

The server provides a web-based administrative interface built with the Leptos framework.

| Route | Component | Purpose |
| :--- | :--- | :--- |
| `/` | `HomePage` | A placeholder welcome page. |
| `/admin/interface/user` | `ShowUsers` | Lists Active and Suspended users. |
| `/admin/interface/inactiveuser` | `ShowUsers` | Lists Inactive users. |
| `/admin/interface/newuser` | `ShowNewUsers` | Lists unknown badge scans pending registration. |
| `/admin/interface/devices` | `ShowDevices` | Lists all devices and their lockout status. |
| `/admin/interface/deviceAccess/:id` | `ShowDeviceAccess` | Manages which users have access to a specific device. |

---

## Server Functions (RPC from Web UI)

These are backend Rust functions that can be called directly from the frontend UI code.

| Function | Location | Purpose |
| :--- | :--- | :--- |
| `get_users_by_status` | `src/users.rs` | Fetches users from the database based on their status. |
| `set_status_user` | `src/users.rs` | Updates a user's status (Active, Inactive, Suspended). |
| `get_new_users` | `src/newusers.rs` | Fetches all records from the `newuser` table. |
| `add_new_user_to_users` | `src/newusers.rs` | *(Not Implemented)* Intended to create a new user from a `newuser` record. |
| `trash_new_user` | `src/newusers.rs` | *(Not Implemented)* Intended to delete a `newuser` record. |
| `get_devices` | `src/devices.rs` | Fetches all devices from the database. |
| `set_lockout_status` | `src/devices.rs` | Updates a device's lockout status and times. |
| `get_device_access` | `src/devices.rs` | Fetches all users with access to a specific device. |
| `get_device_usage_summary` | `src/devices.rs` | *(Not Implemented)* Intended to generate a tool usage report. |
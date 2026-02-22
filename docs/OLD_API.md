# Old Python Server API & Database Structure

*Note: This documentation is based on `server.py` found in the root of the repository. It serves as the functional specification for the Rust replacement.*

## Configuration (`server.cfg`)
The server requires a `server.cfg` file (checked in `/opt/tinkeraccess/` or local dir) with the following settings:
*   `password`: Admin interface password.
*   `db`: Path to SQLite database.
*   `slackurl`: Webhook URL for Slack notifications.
*   `webcam_username` / `webcam_password`: For fetching snapshots from device cameras.
*   `imgur_client_id`: For uploading webcam snapshots.
*   `[webcam_urls]`: Section mapping device names to camera URLs.

## Database Layout (SQLite)

The application uses a SQLite database (`db.db` or configured path). 
*Note: The `init_db` function in `server.py` references a `schema.sql` file for initialization.*

### Tables

#### `user`
Stores member information.
*   `id` (Integer, Primary Key): Unique user ID.
*   `name` (Text): User's full name.
*   `code` (Text): The RFID badge code associated with the user.
*   `status` (Text): User's standing.
    *   `'A'`: Active
    *   `'I'`: Inactive
    *   `'S'`: Suspended (often used for 24h access toggles).

#### `device`
Stores hardware device configuration (e.g., Lasers, Saws).
*   `id` (Integer, Primary Key): Unique device ID.
*   `name` (Text): Display name of the device.
*   `allUsers` (Boolean/Integer): If true (1), all active users can access this device without specific training.
*   `lockout` (Integer): Current state of the device.
    *   `0`: Unlimited (24 Hrs)
    *   `1`: Limited Hours
    *   `2`: Locked Out
*   `lockout_start` (Text): Start time for limited access (e.g., "HH:MM").
*   `lockout_end` (Text): End time for limited access (e.g., "HH:MM").

#### `deviceAccess`
Join table linking Users to Devices they are trained on.
*   `user` (Integer, Foreign Key): Links to `user.id`.
*   `device` (Integer, Foreign Key): Links to `device.id`.
*   `time` (Integer): Access time granted (default 100).
*   `trainer` (Boolean): If true, this user is authorized to train others on this device.

#### `newuser`
Temporary holding table for unknown badge scans.
*   `id` (Integer, Primary Key)
*   `code` (Text): The unknown badge code scanned.
*   `deviceID` (Integer, Foreign Key): The device where the scan occurred.

#### `log`
*   `message` (Text): Log message (e.g., `login:<deviceid>:<userid>` or `logout:<deviceid>:<userid>`).
*   `Timestamp` (Datetime): Timestamp of the event.

---

## Hardware Client API (HTTP)

The hardware clients communicate via HTTP GET requests.

| Function | Route | Python Function | Description |
| :--- | :--- | :--- | :--- |
| **Login / Check Access** | `/device/<deviceid>/code/<code>` | `deviceCode` | **Core Logic:**<br>1. Checks Device Lockout Status.<br>2. **Locked (2):** Deny.<br>3. **Unlimited (0):**<br>   - *All Users Device:* Grant if User Status is 'A' or 'S'.<br>   - *Restricted Device:* Grant if User Status is 'A' or 'S' AND exists in `deviceAccess`.<br>4. **Limited (1):**<br>   - Checks current time against `lockout_start`/`end`.<br>   - *During Restricted Time:* Grant ONLY if User Status is 'S' (24hr access).<br>   - *Outside Restricted Time:* Same as Unlimited (0).<br><br>**Side Effects:**<br>- If denied/unknown: Adds badge to `newuser` table.<br>- If granted: Logs `login` event, posts to Slack (with optional webcam img). |
| **Logout** | `/device/<deviceid>/logout/<uid>` | `deviceLogout` | Logs a user out of a device. Posts to Slack. |

---

## Web Application Routes (Flask)

The server is a Flask application serving Server-Side Rendered HTML (Jinja2 templates).

### Authentication
| Route | Python Function | Description |
| :--- | :--- | :--- |
| `/` | `defaultRoute` | Login page. |
| `/checkLogin/<user>/<password>` | `checkLogin` | Validates password against config. |

### User Management
| Route | Python Function | Description |
| :--- | :--- | :--- |
| `/admin/interface/user` | `adminInterface` | Lists active and suspended users. |
| `/admin/interface/inactiveuser` | `inactiveUserInterface` | Lists inactive users. |
| `/admin/interface/newuser` | `newUserInterface` | Lists unknown badge scans. |
| `/admin/addUser/<userid>/name/<name>` | `addUser` | Moves a new user to active users. |
| `/admin/delNewUser/<userid>` | `delNewUser` | Deletes a record from the `newuser` table. |
| `/admin/delUser/<userid>` | `delUser` | Deletes a user permanently. |
| `/admin/activateUser/<userid>` | `activateUser` | Reactivates an inactive user. |
| `/admin/deactivateUser/<userid>` | `deactivateUser` | Deactivates a user. |
| `/admin/toggle24Hr/user/<userid>` | `toggle24HrAccess` | Toggles 'S' status (24hr access). |
| `/admin/loadcsv` (POST) | `loadCSV` | Bulk imports users from CSV. |

### Device Management
| Route | Python Function | Description |
| :--- | :--- | :--- |
| `/admin/interface/devices` | `deviceInterface` | Lists devices and status. |
| `/admin/deviceUnlimitedHr/<deviceid>` | `deviceUnlimitedHr` | Sets lockout to 0 (Unlimited). |
| `/admin/deviceLimitedHr/<deviceid>` | `deviceLimitedHr` | Sets lockout to 1 (Limited). |
| `/admin/deviceLockout/<deviceid>` | `deviceLockout` | Sets lockout to 2 (Locked). |
| `/admin/deviceLockoutTimes/<deviceid>/time/<start>/<end>` | `deviceLockoutTimes` | Sets lockout hours. |

### Access Control (User <-> Device)
| Route | Python Function | Description |
| :--- | :--- | :--- |
| `/admin/interface/deviceAccess/<deviceid>` | `deviceAccessInterface` | Shows users for a device. |
| `/admin/interface/userAccess/<userid>` | `userAccessInterface` | Shows devices for a user. |
| `/admin/addUserAccess/<userid>/<deviceid>` | `addUserAccess` | Grants user access to device. |
| `/admin/delUserAccess/<userid>/<deviceid>` | `delUserAccess` | Revokes user access. |
| `/admin/addTrainer/<userid>/<deviceid>` | `addUserTrainerAccess` | Makes user a trainer. |
| `/admin/removeTrainer/<userid>/<deviceid>` | `delUserTrainerAccess` | Removes trainer status. |
| `/admin/marioStar/<trainerid>/<trainerBadge>/<deviceid>/<userBadge>` | `marioStarMode` | Trainer "star mode" to instantly train a user. |

### Reporting
| Route | Python Function | Description |
| :--- | :--- | :--- |
| `/toolSummary` | `toolSummaryInterface` | Tool usage statistics. |
| `/admin/interface/log` | `viewLog` | Raw log view. |
| `/admin/interface/csv` | `csvHTMLInterface` | CSV upload interface. |

### UI Modals (HTML Fragments)
| Route | Python Function | Description |
| :--- | :--- | :--- |
| `/admin/interface/inactiveuser/modal/deluser/...` | `delUserModal` | Confirmation modal for deleting a user. |
| `/admin/interface/inactiveuser/modal/useractive/...` | `userActiveModal` | Modal when reactivating a user who has a name conflict. |
| `/admin/interface/newuser/modal/useractive/...` | `newuserActiveModal` | Modal when adding a new user who has a name conflict. |
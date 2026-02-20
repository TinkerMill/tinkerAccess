# Tinker Access Server API

This application uses [Leptos Server Functions](https://book.leptos.dev/server/25_server_functions.html). These functions are Rust functions that can be called from the client code, but execute on the server. Leptos automatically creates HTTP API endpoints for them.

By default, these are exposed as `POST` requests at `/api/<function_name>`. Arguments are passed as URL-encoded form data or JSON, and results are returned as JSON.

## Devices API

Defined in `src/devices.rs`.

### `get_devices`
Retrieves a list of all devices configured in the system.

*   **Endpoint**: `/api/get_devices`
*   **Parameters**: None
*   **Returns**: `Result<Vec<device::Model>, ServerFnError>`
    *   List of device database models.

### `set_lockout_status`
Updates the lockout status of a specific device.

*   **Endpoint**: `/api/set_lockout_status`
*   **Parameters**:
    *   `device_id` (`i64`): The ID of the device to update.
    *   `new_lockout` (`i32`): The new status.
        *   `0`: Unlimited (24 Hrs)
        *   `1`: Limited Hours
        *   `2`: Locked Out
*   **Returns**: `Result<device::Model, ServerFnError>`
    *   The updated device model.

### `get_users_for_device`
Retrieves all users associated with a specific device, including their access details.

*   **Endpoint**: `/api/get_users_for_device`
*   **Parameters**:
    *   `device_id` (`i64`): The ID of the device.
*   **Returns**: `Result<Vec<(device::Model, Option<device_access::Model>, Option<user::Model>)>, ServerFnError>`
    *   A list of tuples containing the device, the access record (if any), and the user record (if any).

### `get_device_usage_summary`
*Current Status: Not Implemented*

Intended to retrieve usage statistics for devices within a date range.

*   **Endpoint**: `/api/get_device_usage_summary`
*   **Parameters**:
    *   `start_time` (Query Param, optional): Start date string.
    *   `end_time` (Query Param, optional): End date string.
*   **Returns**: `Result<Vec<(entities::device::Model, DeviceUsageData)>, ServerFnError>`

## Users API

Defined in `src/users.rs`.

### `get_users`
Retrieves a list of users, optionally filtered by their status.

*   **Endpoint**: `/api/get_users`
*   **Parameters**:
    *   `status_filter` (`Option<Vec<String>>`): A list of status codes to include (e.g., `["A", "S"]`). If `None`, returns all users.
*   **Returns**: `Result<Vec<user::Model>, ServerFnError>`

### `set_status_user`
Updates the status of a specific user.

*   **Endpoint**: `/api/set_status_user`
*   **Parameters**:
    *   `user_id` (`i64`): The ID of the user.
    *   `new_status` (`String`): The new status code.
        *   `"A"`: Active
        *   `"I"`: Inactive
        *   `"S"`: Suspended (often used for 24h access toggles in UI logic)
*   **Returns**: `Result<user::Model, ServerFnError>`

## New Users API

Defined in `src/newusers.rs`.

### `get_newusers`
Retrieves a list of "new" users (likely scanned badges not yet assigned to a profile) and the device they scanned at.

*   **Endpoint**: `/api/get_newusers`
*   **Parameters**: None
*   **Returns**: `Result<Vec<(newuser::Model, Option<device::Model>)>, ServerFnError>`
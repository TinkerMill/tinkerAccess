use crate::components::*;
use entities::device;
use leptos::prelude::*;
use leptos::IntoView;

#[server]
pub async fn get_devices() -> Result<Vec<device::Model>, ServerFnError> {
    use entities::device::Entity as Device;
    use sea_orm::prelude::*;
    use sea_orm::{DatabaseConnection, EntityTrait};
    let conn_pool = expect_context::<DatabaseConnection>();
    match Device::find().all(&conn_pool).await {
        Ok(user_list) => Ok(user_list),
        Err(e) => Err(ServerFnError::ServerError(e.to_string())),
    }
}

#[server]
pub async fn set_lockout_status(
    device_id: i64,
    new_lockout: i32,
) -> Result<device::Model, ServerFnError> {
    use sea_orm::entity::prelude::*;
    use sea_orm::ActiveValue::{NotSet, Set, Unchanged};
    use sea_orm::{DatabaseConnection, EntityTrait, QueryOrder};
    let conn_pool = expect_context::<DatabaseConnection>();
    match device::Entity::find_by_id(device_id).one(&conn_pool).await {
        Ok(Some(device)) => {
            let mut updated_device: device::ActiveModel = device.into();
            updated_device.lockout = Set(Some(new_lockout.to_owned()));
            match updated_device.update(&conn_pool).await {
                Ok(device) => Ok(device),
                Err(e) => Err(ServerFnError::ServerError(e.to_string())),
            }
        }
        Ok(None) => Err(ServerFnError::ServerError(
            "Device does not exist in DB".to_string(),
        )),
        Err(e) => Err(ServerFnError::ServerError(e.to_string())),
    }
}

#[component]
pub fn ShowDevices() -> impl IntoView {
    view! {
        <table class="table  table-hover">
          <thead>
            <tr>
              <th>Devices</th>
              <th>Authorized Users</th>
              <th>Timed Access</th>
              <th>Limited Hours</th>
            </tr>
          </thead>
          <tbody>
          <Await future=get_devices() children=|devices| {
            let (devices, set_device) = signal(devices.clone().unwrap());
            view! {
                <For each=move || devices.get() key=|device| device.id.clone() let:device>
                <DeviceRow this_device=device />
                </For>
            }
      } />

          </tbody>
        </table>
    }
}

async fn set_device_lockout_client(
    device_id: i64,
    lockout_status: i32,
    set_device: WriteSignal<device::Model>,
) {
    use leptos::reactive::prelude::*;
    set_device.set(set_lockout_status(device_id, lockout_status).await.unwrap());
}

fn get_lockout_value(this_device: device::Model) -> String {
    match this_device.lockout {
        Some(0) => "radioUnlimited".to_string(),
        Some(1) => "radioLimited".to_string(),
        Some(2) => "radioLockout".to_string(),
        Some(_) => "test".to_string(),
        None => "test".to_string(),
    }
}

#[component]
pub fn DeviceRow(this_device: device::Model) -> impl IntoView {
    let (this_device, set_device) = signal(this_device.clone());

    let set_device_lockout_client =
        Action::new(|input: &(i64, i32, WriteSignal<device::Model>)| {
            // the input is a reference, but we need the Future to own it
            // this is important: we need to clone and move into the Future
            // so it has a 'static lifetime
            let input = input.clone();
            async move { set_device_lockout_client(input.0, input.1, input.2).await }
        });

    let lockout_signal = signal(get_lockout_value(this_device.get()));

    // Device columns:
    //   [0] - id
    //   [1] - name
    //   [2] - allUsers
    //   [3] - lockout
    //   [4] - lockoutStart
    //   [5] - lockoutEnd
    //
    //
    view! {
      <tr>
        <td style:text-decoration=move || if this_device.get().lockout.unwrap() == 2 { "line-through" } else { "" } >{ move || this_device.get().name.unwrap_or("Unnamed".to_string()) }</td>
        <Show when=move || this_device.get().all_users.unwrap() == false fallback=|| view! {
            <td><span class="glyphicon glyphicon-user" aria-hidden="true"></span> All</td>
        }>
            <td>
                <button type="button" class="btn btn-default" onclick="location.href='/admin/interface/deviceAccess/{ item.id }'">
                    <span class="glyphicon glyphicon-pencil" aria-hidden="true"></span>
                </button>
            </td>
       </Show>
       <td>
       <fieldset>
        <div class="custom-control custom-checkbox">
            <input class="custom-control-input" type="radio" id="radioUnlimited" value="radioUnlimited" bind:group=lockout_signal on:click=move |_| { set_device_lockout_client.dispatch((this_device.get().id, 0, set_device)); }  />
            <label class="custom-control-label" for="radioUnlimited">24 Hrs</label>
            <span inner_html=move || "&nbsp;".to_string() />
            <input class="custom-control-input" type="radio" id="radioLimited" value="radioLimited" bind:group=lockout_signal on:click=move |_| { set_device_lockout_client.dispatch((this_device.get().id, 1, set_device)); }  />
            <label class="custom-control-label" for="radioLimited">Limited Hrs</label>
        </div>
        <div class="custom-control custom-checkbox">
            <input class="custom-control-input" type="radio" id="radioLockout" value="radioLockout" bind:group=lockout_signal on:click=move |_| { set_device_lockout_client.dispatch((this_device.get().id, 2, set_device)); }  />
            <label class="custom-control-label" for="radioLockout">Locked Out</label>
        </div>
       </fieldset>
       </td>
        <td>
            <Show when=move || this_device.get().lockout.unwrap_or(0) == 1 >
            <p></p>
                <table class="text">
                <tbody>
                    <tr>
                        <td>
                          <span>"Locked out between"</span>
                          // <span "&nbsp;"</span>
                          <span inner_html=move || "&nbsp;".to_string() />
                        </td>
                        <td>
                            <div class="input-group bootstrap-timepicker timepicker" style="width: 130px;">
                                // <input id=move || format!("startTime_{}", this_device.get().id) type="text" class="form-control input-small" />
                                <input id=move || format!("startTime_{}", this_device.get().id) type="time" class="form-control input-small" />
                                <span class="input-group-addon"><i class="glyphicon glyphicon-time"></i></span>
                            </div>
                        </td>
                        <td><span inner_html=move || "&nbsp;".to_string() /><span>and</span><span inner_html=move || "&nbsp;".to_string()  /></td>
                        <td>
                            <div class="input-group bootstrap-timepicker timepicker" style="width: 130px;">
                                <input id=move || format!("endTime_{}", this_device.get().id) type="time" class="form-control input-small" />
                                <span class="input-group-addon"><i class="glyphicon glyphicon-time"></i></span>
                            </div>
                        </td>
                        <td><span inner_html=move || "&nbsp;&nbsp;&nbsp;".to_string() /></td>
                        <td>
                            <div class="btn-group" role="group" aria-label="buttonGroup">
                                <button type="button" id=move || format!("cancelBtn_{}", this_device.get().id) class="btn btn-default" onclick="location.href='/admin/interface/devices'" disabled >
                                    <span class="glyphicon glyphicon-remove" aria-hidden="true" ></span>
                                </button>
                                <button type="button" id=move || format!("acceptBtn_{}", this_device.get().id) class="btn btn-default" onclick={ } disabled>
                                    <span class="glyphicon glyphicon-ok" aria-hidden="true" ></span>
                                </button>
                            </div>
                        </td>
                    </tr>
                </tbody>
                </table>
            </Show>
        </td>
      </tr>

    }
}

use std::collections::HashMap;
use std::time::Duration;

use crate::components::*;
use chrono::prelude::*;
use entities::device;
use entities::device_access;
use entities::user;
use leptos::prelude::*;
use leptos::IntoView;
use leptos_router::hooks::use_params_map;
use serde::{Deserialize, Serialize};

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
                <a href=format!("/admin/interface/deviceAccess/{}", this_device.get().id) >
                    <button type="button" class="btn btn-default" >
                        <span class="glyphicon glyphicon-pencil" aria-hidden="true"></span>
                    </button>
                </a>
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

#[server]
pub async fn get_users_for_device(
    device_id: i64,
) -> Result<
    Vec<(
        device::Model,
        Option<device_access::Model>,
        Option<user::Model>,
    )>,
    ServerFnError,
> {
    use entities::device::Entity as Device;
    use entities::links::DeviceToUser;
    use entities::user::Entity as User;
    use sea_orm::prelude::*;
    use sea_orm::{DatabaseConnection, DbBackend, EntityTrait, QueryTrait};
    let conn_pool = expect_context::<DatabaseConnection>();
    let sql_query = Device::find_by_id(device_id)
        .find_also_related(device_access::Entity)
        .and_also_related(user::Entity);
    match sql_query.all(&conn_pool).await {
        Ok(user_list) => Ok(user_list),
        Err(e) => Err(ServerFnError::ServerError(e.to_string())),
    }
}

#[component]
pub fn ShowDeviceAccess() -> impl IntoView {
    let params = use_params_map();
    let device_id = params.read().get("id").unwrap().parse().unwrap();

    view! {
      <Await future=get_users_for_device(device_id) children=|users| {
        let (users, set_users) = signal(users.clone().unwrap());
        view! {
          <div class="page-header">
            <h1>TinkerAccess Device Access Interface</h1>
            <p class="lead">User access list for device <b>{ users.get()[0].0.name.clone() }</b></p>
          </div>
          <table class="table  table-hover">
            <thead>
              <tr>
                <th>User</th>
                <th>Badge Code</th>
                <th>Trainer</th>
                <th>Edit</th>
              </tr>
            </thead>
            <tbody>
                <For each=move || {users.get().into_iter().filter(|(_,useraccess,user)| user.is_some() && useraccess.is_some()).map(|(_,useraccess,user)| (user.unwrap(),useraccess.unwrap())).collect::<Vec<(user::Model,device_access::Model)>>() } key=|(user,_)| user.id.clone() let:user>
                  <tr>
                    <td><span class="glyphicon glyphicon-user" aria-hidden="true"></span> { user.0.name.clone() }</td>
                    <td>{{ user.0.code.clone() }}</td>
                    <td><Show when=move || user.1.trainer.unwrap_or(false) ><span class="glyphicon glyphicon-ok" aria-hidden="true"></span></Show></td>
                    <td>
                      <button type="button" class="btn btn-default" onclick="location.href='/admin/interface/userAccess/{ user.0.id }'">
                        <span class="glyphicon glyphicon-pencil" aria-hidden="true"></span>
                      </button>
                    </td>
                  </tr>
                </For>
            </tbody>
          </table>
        }
        } />
    }
}

#[derive(Serialize, Deserialize, Clone)]
pub struct DeviceUsageData {
    device: entities::device::Model,
    login_count: u32,
    logout_count: u32,
    total_time: Duration,
    leaderboard: Vec<(entities::user::Model, Summary)>,
}

// @app.route("/toolSummary")
// @app.route("/toolSummary/<start_date>")
// @app.route("/toolSummary/<start_date>/<end_date>")
// def toolSummaryInterface(start_date=None, end_date=None):
//   # calculate default start and end dates
//   if start_date is None:
//     today = datetime.datetime.now()
//     # Fix for December - properly handle year rollover for previous month
//     prev_month = (today.month - 1) or 12  # If month is 1, prev_month becomes 12
//     prev_year = today.year - (today.month == 1)  # Subtract 1 from year if current month is January
//     start_date = datetime.datetime(prev_year, prev_month, 1)
//   else:
//     start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")

//   if end_date is None:
//     # Fix for December - properly handle year rollover for next month
//     next_month = (start_date.month % 12) + 1  # If month is 12, next_month becomes 1
//     next_year = start_date.year + (start_date.month == 12)  # Add 1 to year if current month is December
//     end_day = min(start_date.day, monthrange(next_year, next_month)[1])
//     end_date = datetime.datetime(next_year, next_month, end_day)
//   else:
//     end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

//   tool_summary = genToolSummary(start_date, end_date)
//   return render_template('toolUse.html', tools = tool_summary,
//           start = start_date.strftime("%Y-%m-%d"),
//           end = end_date.strftime("%Y-%m-%d"))

#[derive(Serialize, Deserialize, Clone)]
pub struct Summary {
    logins: u32,
    total_time: Duration,
}
impl Summary {
    fn add_logout(&mut self, time: Duration) {
        self.logins += 1;
        self.total_time += time;
    }
}

#[server]
pub async fn get_device_usage_summary(
) -> Result<Vec<(entities::device::Model, DeviceUsageData)>, ServerFnError> {
    use sea_orm::prelude::*;
    use sea_orm::ColumnTrait;
    use sea_orm::Condition;
    use sea_orm::{DatabaseConnection, EntityTrait};
    let conn_pool = expect_context::<DatabaseConnection>();
    let params = use_params_map();
    let start_time: Result<NaiveDateTime, chrono::ParseError> =
        match params.read().get("start_time") {
            Some(date_str) => date_str.parse::<NaiveDateTime>(),
            None => Ok(Utc::now().naive_local()),
        };
    let end_time: Result<NaiveDateTime, chrono::ParseError> = match params.read().get("end_time") {
        Some(date_str) => date_str.parse::<NaiveDateTime>(),
        None => Ok((Utc::now() + chrono::Duration::days(30)).naive_local()),
    };
    let logs = match entities::log::Entity::find()
        .filter(
            Condition::all()
                .add(entities::log::Column::Timestamp.gt(start_time.unwrap()))
                .add(entities::log::Column::Timestamp.lt(end_time.unwrap())),
        )
        .all(&conn_pool)
        .await
    {
        Ok(user_list) => Ok(user_list),
        Err(e) => Err(ServerFnError::ServerError(e.to_string())),
    };
    let mut open_logins = HashMap::<(u32, u32), entities::log::Model>::new();
    // let tool_summary = HashMap::<u32, ToolSummary>::new();
    // let user_summary = HashMap::<(u32, u32), ToolSummary>::new();
    Ok(())
}

#[component]
pub fn ShowDeviceUsageSummary() -> impl IntoView {
    view! {
        <div class="page-header">
            <h1>Tool Usage Summary</h1>
            <p class="lead">
                <form id="daterange" onsubmit="datesubmit()">
                    <input type="text" class="datepicker" id="start" value="{ start_time  }" /> &mdash;
                    <input type="text" class="datepicker" id="end" value="{{ end_time }}" />
                    <input type="submit" value="Go" />
                </form>
            </p>
        </div>

        <Await future=get_device_usage_summary() children=|usage_data| {
            usage_data.clone().unwrap().into_iter().map(|(device,summary)| {
                let (summary, _) = signal(summary);
                view! {
                    <h2>{ device.name.unwrap() }</h2>
                    <ul>
                        <li>Logins: { summary.get().login_count.clone() } </li>
                        <li>Logouts: { summary.get().logout_count.clone() } </li>
                        <li>Total time: { format!("{:?}", summary.get().total_time.clone()) } </li>
                    </ul>
                    Usage leaderboard:
                    <ol>
                        <For each=move || summary.get().leaderboard.clone() key=|user| user.0.id let:user >
                            <li>{ user.0.name.clone() }, { user.1.logins.clone() } </li>
                        </For>
                    </ol>
                }
            }).collect_view()

        } />
    }
}

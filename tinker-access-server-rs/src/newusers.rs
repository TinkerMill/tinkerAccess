use crate::components::*;
use entities::device;
use entities::newuser;
use entities::user;
use leptos::prelude::*;
use leptos::IntoView;

#[server]
pub async fn get_newusers() -> Result<Vec<(newuser::Model, Option<device::Model>)>, ServerFnError> {
    use entities::newuser::Entity as NewUser;
    use sea_orm::prelude::*;
    use sea_orm::{DatabaseConnection, EntityTrait, QueryOrder};
    let conn_pool = expect_context::<DatabaseConnection>();
    match NewUser::find()
        .find_also_related(device::Entity)
        .all(&conn_pool)
        .await
    {
        Ok(user_list) => Ok(user_list),
        Err(e) => Err(ServerFnError::ServerError(e.to_string())),
    }
}

#[component]
pub fn ShowNewUsers() -> impl IntoView {
    let title = "TinkerAccess User Admin Interface".to_string();
    let snippit = r#"List of active users : <small><a href="/admin/interface/csv"><span class="glyphicon glyphicon-upload" aria-hidden="true" ></span></a></small> "#.to_string();
    view! {
      <PageTitle title=title snippit=snippit/>
      <table class="table  table-hover">
        <thead>
          <tr>
            <th>Badge Code</th>
            <th>Device</th>
            <th>Name</th>
            <th>Edit</th>
          </tr>
        </thead>
        <tbody>
          <Await future=get_newusers() children=|newusers| {
            let (newusers, _set_newusers) = signal(newusers.clone().unwrap());
            view! {
              <For each=move || newusers.get() key=|newuser| newuser.0.id.clone() let:newuser>
                <NewUserRow this_newuser_device=newuser />
              </For>
            }
          }/>
        </tbody>
      </table>
    }
}

#[component]
pub fn NewUserRow(this_newuser_device: (newuser::Model, Option<device::Model>)) -> impl IntoView {
    let (this_newuser, _set_newuser) = signal(this_newuser_device.0);
    let (this_device, _set_device) = signal(this_newuser_device.1);

    view! {
          <tr>
            <td><span class="glyphicon glyphicon-user" aria-hidden="true"></span> { move || this_newuser.get().code.unwrap_or("None".to_string()).clone().to_string() }</td>
            <td>{ move || match this_device.get() {
              None => "None".to_string(),
              Some(device) => match device.name {
                None => "None".to_string(),
                Some(device_name) => device_name.clone().to_string(),
              }

            } }</td>
            <td>
              <input type="text" id={ move || "text_".to_string() + &this_newuser.get().code.unwrap_or("None".to_string()).clone() } />
            </td>
            <td>
              <div class="btn-group" role="group" aria-label="...">
                <button type="button" class="btn btn-default" > // Add onclick for AddUsers
                  <span class="glyphicon glyphicon-plus" aria-hidden="true"></span>
                </button>

                <button type="button" class="btn btn-default" > // Add onclick for delNewUser
                  <span class="glyphicon glyphicon-trash" aria-hidden="true"></span>
                </button>

              </div>

            </td>
          </tr>
    }
}

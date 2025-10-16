use crate::components::*;
use entities::user;
use leptos::prelude::*;
use leptos::IntoView;

#[server]
pub async fn get_users(
    status_filter: Option<Vec<String>>,
) -> Result<Vec<user::Model>, ServerFnError> {
    use entities::user::Entity as User;
    use sea_orm::prelude::*;
    use sea_orm::{DatabaseConnection, EntityTrait, QueryOrder};
    let conn_pool = expect_context::<DatabaseConnection>();
    match if status_filter.is_some() {
        User::find()
            .filter(<User as sea_orm::EntityTrait>::Column::Status.is_in(status_filter.unwrap()))
    } else {
        User::find()
    }
    .all(&conn_pool)
    .await
    {
        Ok(user_list) => Ok(user_list),
        Err(e) => Err(ServerFnError::ServerError(e.to_string())),
    }
}

#[server]
pub async fn set_status_user(
    user_id: i64,
    new_status: String,
) -> Result<user::Model, ServerFnError> {
    use sea_orm::entity::prelude::*;
    use sea_orm::ActiveValue::{NotSet, Set, Unchanged};
    use sea_orm::{DatabaseConnection, EntityTrait, QueryOrder};
    let conn_pool = expect_context::<DatabaseConnection>();
    leptos::logging::log!("Server deactivating user {}", user_id);
    match user::Entity::find_by_id(user_id).one(&conn_pool).await {
        Ok(Some(user)) => {
            let mut updated_user: user::ActiveModel = user.into();
            // Really!? We're using a single character to store user status?!
            // TODO: Do someting. ANYTHING other than this....
            updated_user.status = Set(Some(new_status.to_owned()));

            match updated_user.update(&conn_pool).await {
                Ok(user) => Ok(user),
                Err(e) => Err(ServerFnError::ServerError(e.to_string())),
            }
        }
        Ok(None) => Err(ServerFnError::ServerError(
            "User does not exist in DB".to_string(),
        )),
        Err(e) => Err(ServerFnError::ServerError(e.to_string())),
    }
}

async fn set_status_user_client(
    user_id: i64,
    new_status: String,
    set_user: WriteSignal<user::Model>,
) {
    use leptos::reactive::prelude::*;
    leptos::logging::log!("Deactivating user {}", user_id);
    set_user.set(set_status_user(user_id, new_status).await.unwrap());
}

#[component]
pub fn ShowUsers(status_filter: Option<Vec<String>>) -> impl IntoView {
    let title = "TinkerAccess User Admin Interface".to_string();
    let snippit = r#"List of active users : <small><a href="/admin/interface/csv"><span class="glyphicon glyphicon-upload" aria-hidden="true" ></span></a></small> "#.to_string();
    view! {
      <PageTitle title=title snippit=snippit/>
      <table class="table  table-hover">
        <thead>
          <tr>
            <th>User</th>
            <th>Badge Code</th>
            <th>24 Hr Access</th>
            <th>Edit</th>
          </tr>
        </thead>
        <tbody>
          <Await future=get_users(status_filter) children=|users| {
            let (users, _set_users) = signal(users.clone().unwrap());
            view! {
              <For each=move || users.get() key=|user| user.id.clone() let:user>
                <UserRow this_user=user />
              </For>
            }
          }/>
        </tbody>
      </table>
    }
}

#[component]
pub fn UserRow(this_user: user::Model) -> impl IntoView {
    let (this_user, set_user) = signal(this_user);

    view! {
          <tr>
            <td><span class="glyphicon glyphicon-user" aria-hidden="true"></span> { move || this_user.get().name.clone() }</td>
            <td>{ move || this_user.get().code.clone() }</td>
            <td inner_html=move || { if this_user.get().status.unwrap() == "S" { r#"<span class="glyphicon glyphicon-ok" aria-hidden="true"></span>"#.to_string() } else {"".to_string()} } > </td>
            <td>
              <div class="btn-group" role="group" aria-label="...">
                <UserStatusButtons this_user=this_user set_user=set_user />
                <button type="button" class="btn btn-default" onclick="location.href='/admin/interface/userAccess/{ user.id }'"><span class="glyphicon glyphicon-pencil" aria-hidden="true"></span></button>
              </div>
            </td>
          </tr>
    }
}

#[component]
pub fn UserStatusButtons(
    this_user: ReadSignal<user::Model>,
    set_user: WriteSignal<user::Model>,
) -> impl IntoView {
    let set_status_user_client = Action::new(|input: &(i64, String, WriteSignal<user::Model>)| {
        // the input is a reference, but we need the Future to own it
        // this is important: we need to clone and move into the Future
        // so it has a 'static lifetime
        let input = input.clone();
        async move { set_status_user_client(input.0, input.1, input.2).await }
    });
    let toggle_status = move |_| {
        let new_status = if this_user.get().status.unwrap() == "I".to_string() {
            "A".to_string()
        } else {
            "I".to_string()
        };
        set_status_user_client.dispatch((this_user.get().id, new_status, set_user));
    };
    let toggle_24h = move |_| {
        let new_status = if this_user.get().status.unwrap() == "A".to_string() {
            "S".to_string()
        } else {
            "A".to_string()
        };
        set_status_user_client.dispatch((this_user.get().id, new_status, set_user));
    };
    view! {
        <button type="button" class="btn btn-default" style:display=move || if this_user.get().status.unwrap() == "I".to_string() { "none" } else { "" }  on:click=toggle_24h >
          <span class="glyphicon glyphicon-time" aria-hidden="true"></span>
        </button>
        <button type="button" class="btn btn-default" on:click=toggle_status>
          <span class="glyphicon" class:glyphicon-play=move || this_user.get().status.unwrap() == "I".to_string()  class:glyphicon-pause=move || this_user.get().status.unwrap() != "I".to_string() aria-hidden="true"></span>
        </button>
    }
}

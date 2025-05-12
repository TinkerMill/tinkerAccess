use crate::components::*;
use entities::user;
use leptos::prelude::*;
use leptos::IntoView;

#[server]
pub async fn get_users() -> Result<Vec<user::Model>, ServerFnError> {
    use sea_orm::{DatabaseConnection, EntityTrait, QueryOrder};
    let conn_pool = expect_context::<DatabaseConnection>();
    match user::Entity::find().all(&conn_pool).await {
        Ok(user_list) => Ok(user_list),
        Err(e) => Err(ServerFnError::ServerError(e.to_string())),
    }
}

#[server]
pub async fn deactivate_user(user_id: i64) -> Result<user::Model, ServerFnError> {
    use sea_orm::entity::prelude::*;
    use sea_orm::ActiveValue::{NotSet, Set, Unchanged};
    use sea_orm::{DatabaseConnection, EntityTrait, QueryOrder};
    let conn_pool = expect_context::<DatabaseConnection>();
    leptos::logging::log!("Server deactivating user {}", user_id);
    match user::Entity::find_by_id(user_id).one(&conn_pool).await {
        Ok(Some(user)) => {
            let mut deactivated_user: user::ActiveModel = user.into();
            // Really!? We're using a single character to store user status?!
            // TODO: Do someting. ANYTHING other than this....
            deactivated_user.status = Set(Some("I".to_owned()));

            match deactivated_user.update(&conn_pool).await {
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

async fn deactivate_user_client(user_id: i64, set_user: WriteSignal<user::Model>) {
    use leptos::reactive::prelude::*;
    leptos::logging::log!("Deactivating user {}", user_id);
    set_user.set(deactivate_user(user_id).await.unwrap());
}

#[component]
pub fn ShowUsers() -> impl IntoView {
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
          <Await future=get_users() children=|users| {
            let (users, _set_users) = signal(users.clone().unwrap());
            view! {
              <For each=move || users.get() key=|user| user.id.clone() let:user>
                <UserRow this_user=user />;
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
    let deactivate_user = Action::new(|input: &(i64, WriteSignal<user::Model>)| {
        // the input is a reference, but we need the Future to own it
        // this is important: we need to clone and move into the Future
        // so it has a 'static lifetime
        let input = input.clone();
        async move { deactivate_user_client(input.0, input.1).await }
    });

    view! {
          <tr>
            <td><span class="glyphicon glyphicon-user" aria-hidden="true"></span> { move || this_user.get().name.clone() }</td>
            <td>{ move || this_user.get().code.clone() }</td>
            <td><span class="glyphicon glyphicon-ok" aria-hidden="true"></span></td>
            <td></td>
            <td>
              <div class="btn-group" role="group" aria-label="...">
                <button type="button" class="btn btn-default" on:click=move |_| { deactivate_user.dispatch((this_user.get().id, set_user)); } ><span class="glyphicon glyphicon-pause" aria-hidden="true"></span></button>
                <button type="button" class="btn btn-default" onclick="location.href='/admin/interface/userAccess/{ user.id }'"><span class="glyphicon glyphicon-pencil" aria-hidden="true"></span></button>
              </div>

            </td>
          </tr>
    }
}

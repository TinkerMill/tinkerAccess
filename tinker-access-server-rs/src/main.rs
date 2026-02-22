use anyhow::Result;
#[cfg(feature = "ssr")]
use axum::Router;
#[cfg(feature = "ssr")]
use axum::{
    extract::ws::{Message, WebSocket, WebSocketUpgrade},
    response::IntoResponse,
    routing::get,
};

#[cfg(feature = "ssr")]
#[tokio::main]
async fn main() -> Result<()> {
    use leptos::logging::log;
    use leptos::prelude::*;
    use leptos_axum::{generate_route_list, LeptosRoutes};
    use tinker_access_server_rs::app::*;
    use tinker_access_server_rs::setup::*;
    use tinker_access_server_rs::websocket_dispatcher::websocket_handler;

    let conf = get_configuration(None).unwrap();
    let addr = conf.leptos_options.site_addr;
    let leptos_options = conf.leptos_options;
    // Generate the list of routes in your Leptos App
    let routes = generate_route_list(App);
    let orm_handle = db_setup().await?;

    let app = Router::new()
        .leptos_routes_with_context(
            &leptos_options,
            routes,
            move || provide_context(orm_handle.clone()),
            {
                let leptos_options = leptos_options.clone();
                move || shell(leptos_options.clone())
            },
        )
        .fallback(leptos_axum::file_and_error_handler(shell))
        .with_state(leptos_options)
        .route("/ws", axum::routing::get(websocket_handler)); // Registering the handler

    // run our app with hyper
    // `axum::Server` is a re-export of `hyper::Server`
    log!("listening on http://{}", &addr);
    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();

    axum::serve(listener, app.into_make_service())
        .await
        .unwrap();
    Ok(())
}

#[cfg(not(feature = "ssr"))]
pub fn main() {
    console_error_panic_hook::set_once();
    // no client-side main function
    // unless we want this to work with e.g., Trunk for pure client-side testing
    // see lib.rs for hydration function instead
}

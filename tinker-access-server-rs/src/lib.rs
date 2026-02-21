#[cfg(feature = "ssr")]
use sea_orm::DatabaseConnection;
#[cfg(feature = "ssr")]
use axum::extract::FromRef;

pub mod app;
pub mod components;
pub mod devices;
pub mod newusers;
pub mod setup;
pub mod users;

#[cfg(feature = "ssr")]
pub mod websocket_dispatcher;

#[cfg(feature = "ssr")]
pub mod messages;

#[cfg(feature = "hydrate")]
#[wasm_bindgen::prelude::wasm_bindgen]
pub fn hydrate() {
    use crate::app::*;
    console_error_panic_hook::set_once();
    leptos::mount::hydrate_body(App);
}

#[cfg(feature = "ssr")]
#[derive(FromRef, Clone)]
pub struct AppState {
    pub orm_handle: DatabaseConnection,
    pub leptos_options: leptos::prelude::LeptosOptions,
}

/// sets up the API endpoints for the automated access to the service 
#[cfg(feature = "ssr")]
pub fn api_router() -> axum::Router<AppState> {
    use axum::{routing::get, Router};

    Router::new()
        .route("/api/health", get(|| async { "Server is running!" }))
}

/// Builds the frontend UI
#[cfg(feature = "ssr")]
pub fn build_app(
    app_state: AppState,
    routes: Vec<leptos_axum::AxumRouteListing>) -> axum::Router<AppState> {
    use leptos::prelude::*;
    use leptos_axum::LeptosRoutes;
    use crate::app::*;

    let routes_state = app_state.clone();
    let fallback_state = app_state.clone();

    api_router()
        .leptos_routes_with_context(
            &routes_state,
            routes,
            move || provide_context(routes_state.orm_handle.clone()),
            move || shell(routes_state.leptos_options.clone()),
        )
        .fallback(leptos_axum::file_and_error_handler(move |_| {shell(fallback_state.leptos_options.clone())}))
        .with_state(app_state)
}

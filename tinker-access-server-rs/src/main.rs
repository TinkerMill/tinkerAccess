use anyhow::Result;

#[cfg(feature = "ssr")]
#[tokio::main]
async fn main() -> Result<()> {
    use leptos::logging::log;
    use leptos::prelude::*;
    use leptos_axum::generate_route_list;
    use tinker_access_server_rs::app::*;
    use tinker_access_server_rs::setup::*;
    use tinker_access_server_rs::build_app;

    let conf = get_configuration(None).unwrap();
    let addr = conf.leptos_options.site_addr;
    let leptos_options = conf.leptos_options;
    // Generate the list of routes in your Leptos App
    let routes = generate_route_list(App);
    let orm_handle = db_setup().await?;

    let app = build_app(leptos_options, routes, orm_handle);

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

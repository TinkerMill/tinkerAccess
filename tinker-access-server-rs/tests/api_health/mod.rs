#[cfg(feature = "ssr")]
#[tokio::test]
async fn health_check_works() {
    use axum::{
        body::Body,
        http::{Request, StatusCode},
    };
    use leptos::prelude::*;
    use leptos_axum::generate_route_list;
    use sea_orm::Database;
    use tinker_access_server_rs::app::*;
    use tinker_access_server_rs::build_app;
    use tower::ServiceExt;

    let conf = get_configuration(Some("Cargo.toml")).unwrap();
    let leptos_options = conf.leptos_options;
    let routes = generate_route_list(App);
    let orm_handle = Database::connect("sqlite::memory:").await.unwrap();

    let app = build_app(leptos_options, routes, orm_handle);

    let response = app
        .oneshot(Request::builder().uri("/api/health").body(Body::empty()).unwrap())
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);
    let body = axum::body::to_bytes(response.into_body(), usize::MAX)
        .await
        .unwrap();
    assert_eq!(&body[..], b"Server is running!");
}
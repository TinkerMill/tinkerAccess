use crate::devices::*;
use crate::newusers::*;
use crate::users::*;
use leptos::prelude::*;
use leptos_meta::{provide_meta_context, MetaTags, Stylesheet, Title};
use leptos_router::{
    components::{Route, Router, Routes},
    hooks::use_location,
    path, StaticSegment,
};

pub fn shell(options: LeptosOptions) -> impl IntoView {
    view! {
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="utf-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1"/>
                <AutoReload options=options.clone() />
                <HydrationScripts options/>
                <MetaTags/>
            </head>
            <body>
                <App/>
            </body>
        </html>
    }
}

#[component]
pub fn NavBar() -> impl IntoView {
    view! {
      <ul class="nav nav-pills">
        <NavBarLink path="/admin/interface/user".to_string() title="Users".to_string() />
        <NavBarLink path="/admin/interface/inactiveuser".to_string() title="Inactive Users".to_string() />
        <NavBarLink path="/admin/interface/newuser".to_string() title="New Users".to_string() />
        <NavBarLink path="/admin/interface/devices".to_string() title="Devices".to_string() />
        <NavBarLink path="/admin/interface/toolSummary".to_string() title="Tool Usage Summary".to_string() />
      </ul>
    }
}

#[component]
pub fn NavBarLink(path: String, title: String) -> impl IntoView {
    let current_path = || use_location().pathname.get();
    view! {
        <li role="presentation" class:active=move || current_path().clone() == path.clone() ><a href={path.clone()}>{title}</a></li>
    }
}

#[component]
pub fn App() -> impl IntoView {
    // Provides context that manages stylesheets, titles, meta tags, etc.
    provide_meta_context();

    view! {
        // injects a stylesheet into the document <head>
        // id=leptos means cargo-leptos will hot-reload this stylesheet
        <Stylesheet id="leptos" href="/pkg/tinker-access-server-rs.css"/>


        // content for this welcome page
        <Router>
            <main>
                <Routes fallback=|| "Page not found.".into_view()>
                    <Route path=path!("/admin/interface/user") view=move || {let active_filter = Some(vec!["A".to_string(), "S".to_string()]);  view!{<NavBar /><ShowUsers status_filter=active_filter />} } />
                    <Route path=path!("/admin/interface/inactiveuser") view=move || { let inactive_filter = Some(vec!["I".to_string()]); view!{<NavBar /><ShowUsers status_filter=inactive_filter />} }/>
                    <Route path=path!("/admin/interface/newuser") view=move || { view! { <NavBar /><ShowNewUsers /> } } />
                    <Route path=path!("/admin/interface/devices") view=move || { view! { <NavBar /><ShowDevices /> } } />
                    <Route path=path!("/admin/interface/deviceAccess/:id") view=move || { view! { <NavBar /><ShowDeviceAccess /> } } />
                    <Route path=StaticSegment("") view=HomePage/>
                </Routes>
            </main>
        </Router>
    }
}

/// Renders the home page of your application.
#[component]
fn HomePage() -> impl IntoView {
    // Creates a reactive value to update the button
    let count = RwSignal::new(0);
    let on_click = move |_| *count.write() += 1;

    view! {
        <h1>"Welcome to Leptos!"</h1>
        <button on:click=on_click>"Click Me: " {count}</button>
    }
}

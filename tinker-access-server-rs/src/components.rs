use leptos::prelude::*;

#[component]
pub fn PageTitle(title: String, snippit: String) -> impl IntoView {
    view! {
      <div class="page-header">
        <h1>{title}</h1>
        <p class="lead" inner_html=snippit />
      </div>
    }
}

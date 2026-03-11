<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Admin | Interactive Guide</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Merriweather:wght@700&family=Noto+Sans:wght@400;600;700&family=Open+Sans:wght@400;600;700&display=swap"
      rel="stylesheet"
    />
    <link rel="stylesheet" href="/static/brand.css?v={{ asset_v }}" />
    <link rel="stylesheet" href="/static/app.css?v={{ asset_v }}" />
  </head>
  <body class="admin-page theme-surface-page">
    <main class="admin-shell">
      <header class="theme-header">
        <a href="/" class="theme-brand">
          <img src="/static/kaplan-pathways-logo.svg" alt="Kaplan International Pathways" />
        </a>
        <nav class="theme-nav" aria-label="Primary">
          <a href="/builder">Builder</a>
          <a href="/showcase/all">Showcase</a>
          <a href="/admin">Admin</a>
        </nav>
      </header>

      <header class="admin-header">
        <div>
          <div class="admin-kicker">Admin Dashboard</div>
          <h1>Project Control Panel</h1>
          <p>Manage routes and demos from one place.</p>
        </div>
        {% if is_admin %}
        <form method="post" action="/admin/logout">
          <button class="btn ghost" type="submit">Log out</button>
        </form>
        {% endif %}
      </header>

      {% if not is_admin %}
      <section class="admin-login-card">
        <h2>Admin Access</h2>
        <p>Enter dashboard password.</p>
        {% if error %}
        <div class="admin-error">{{ error }}</div>
        {% endif %}
        <form class="admin-login-form" method="post" action="/admin/login">
          <input type="password" name="password" placeholder="Password" required />
          <button class="btn primary" type="submit">Open Dashboard</button>
        </form>
      </section>
      {% else %}
      <section class="admin-grid">
        <article class="admin-card">
          <h2>Available Paths</h2>
          <div class="admin-path-list">
            {% for item in paths %}
            <a class="admin-path-row" href="{{ item.path }}" target="_blank" rel="noopener noreferrer">
              <span>{{ item.label }}</span>
              <code>{{ item.path }}</code>
            </a>
            {% endfor %}
          </div>
        </article>

        <article class="admin-card admin-card-wide">
          <h2>All Demos</h2>
          {% if demos %}
          <div class="admin-demo-list">
            {% for demo in demos %}
            <div class="admin-demo-row">
              <div class="admin-demo-meta">
                <div class="admin-demo-title">{{ demo.title }}</div>
                <div class="admin-demo-sub">{{ demo.slug }} &middot; {{ demo.status }} &middot; Updated {{ demo.updatedAt }}</div>
                <div class="admin-demo-links">
                  <a href="{{ demo.builderPath }}">Edit in Builder</a>
                  <a href="{{ demo.demoPath }}" target="_blank" rel="noopener noreferrer">Open Demo</a>
                  <a href="{{ demo.analyticsPath }}" target="_blank" rel="noopener noreferrer">Analytics</a>
                  <a href="{{ demo.apiPath }}" target="_blank" rel="noopener noreferrer">API JSON</a>
                </div>
              </div>
              <form method="post" action="/admin/demos/{{ demo.id }}/delete" onsubmit="return confirm('Delete this demo? This cannot be undone.');">
                <button class="btn ghost admin-delete" type="submit">Delete</button>
              </form>
            </div>
            {% endfor %}
          </div>
          {% else %}
          <div class="admin-empty">No demos found.</div>
          {% endif %}
        </article>
      </section>
      {% endif %}
    </main>
  </body>
</html>

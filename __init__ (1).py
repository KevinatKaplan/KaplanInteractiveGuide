<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Analytics | {{ demo.title }}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Merriweather:wght@700&family=Noto+Sans:wght@400;600;700&family=Open+Sans:wght@400;600;700&display=swap"
      rel="stylesheet"
    />
    <link rel="stylesheet" href="/static/brand.css?v={{ asset_v }}" />
    <link rel="stylesheet" href="/static/app.css?v={{ asset_v }}" />
  </head>
  <body class="analytics-page theme-surface-page">
    <main class="analytics-shell">
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

      <header class="analytics-header">
        <div>
          <div class="analytics-kicker">Demo Analytics</div>
          <h1>{{ summary.title }}</h1>
          <p>{{ summary.slug }}</p>
        </div>
        <div class="analytics-actions">
          <a class="btn ghost" href="/demo/{{ summary.slug }}" target="_blank" rel="noopener noreferrer">Open Demo</a>
          <a class="btn ghost" href="/api/analytics/{{ summary.slug }}/summary" target="_blank" rel="noopener noreferrer"
            >View JSON</a
          >
          <a class="btn primary" href="/api/analytics/{{ summary.slug }}/events.csv">Export CSV</a>
        </div>
      </header>

      <section class="analytics-cards">
        <article class="analytics-card">
          <div class="analytics-label">Views</div>
          <div class="analytics-value">{{ summary.views }}</div>
        </article>
        <article class="analytics-card">
          <div class="analytics-label">Starts</div>
          <div class="analytics-value">{{ summary.starts }}</div>
        </article>
        <article class="analytics-card">
          <div class="analytics-label">Completes</div>
          <div class="analytics-value">{{ summary.completes }}</div>
        </article>
        <article class="analytics-card">
          <div class="analytics-label">Completion Rate</div>
          <div class="analytics-value">{{ summary.completionRate }}%</div>
        </article>
        <article class="analytics-card">
          <div class="analytics-label">Feedback Responses</div>
          <div class="analytics-value">{{ summary.feedbackCount }}</div>
        </article>
        <article class="analytics-card">
          <div class="analytics-label">Avg Feedback Score</div>
          <div class="analytics-value">
            {% if summary.feedbackAverageScore is not none %}
              {{ summary.feedbackAverageScore }} / 5
            {% else %}
              -
            {% endif %}
          </div>
        </article>
      </section>

      <section class="analytics-panel">
        <h2>Step Drop-off</h2>
        <div class="analytics-table">
          <div class="analytics-row analytics-head">
            <span>Step</span>
            <span>Reached</span>
            <span>Completed</span>
            <span>Drop-off</span>
            <span>Reach Rate</span>
          </div>
          {% for row in summary.stepDropoff %}
          <div class="analytics-row">
            <span>{{ row.index + 1 }}. {{ row.title }}</span>
            <span>{{ row.reached }}</span>
            <span>{{ row.completed }}</span>
            <span>{{ row.dropoff }}</span>
            <span>{{ row.reachRate }}%</span>
          </div>
          <div class="analytics-progress">
            <div class="analytics-progress-fill" style="width: {{ row.reachRate }}%"></div>
          </div>
          {% endfor %}
        </div>
      </section>

      <section class="analytics-panel">
        <h2>Feedback Comments</h2>
        {% if summary.feedbackComments %}
        <div class="analytics-comments">
          {% for item in summary.feedbackComments %}
          <article class="analytics-comment">
            <div class="analytics-comment-meta">Score: {{ item.score if item.score is not none else "-" }} / 5</div>
            <p>{{ item.text }}</p>
          </article>
          {% endfor %}
        </div>
        {% else %}
        <div class="analytics-empty">No feedback comments yet.</div>
        {% endif %}
      </section>
    </main>
  </body>
</html>

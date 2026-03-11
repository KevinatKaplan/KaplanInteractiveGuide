<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Demo Player</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Merriweather:wght@700&family=Noto+Sans:wght@400;600;700&family=Open+Sans:wght@400;600;700&display=swap"
      rel="stylesheet"
    />
    <link rel="stylesheet" href="/static/brand.css?v={{ asset_v }}" />
    <link rel="stylesheet" href="/static/app.css?v={{ asset_v }}" />
  </head>
  <body class="player theme-surface-page" data-slug="{{ slug }}">
    <div id="player-root" class="player-runtime">
      <section id="intro-screen" class="intro-screen hidden" aria-label="Demo introduction">
        <div class="intro-content">
          <div class="intro-eyebrow">Interactive Demo</div>
          <h1 id="intro-title" class="intro-title"></h1>
          <p id="intro-body" class="intro-body"></p>
          <div class="intro-meta">
            <span id="intro-chapters">0 chapters</span>
            <span id="intro-steps">0 steps</span>
          </div>
          <div class="intro-actions">
            <button id="intro-start" class="btn primary" type="button">Start Interactive Demo</button>
            <button id="intro-skip" class="btn ghost" type="button">Skip Intro</button>
          </div>
        </div>
        <div class="intro-preview-shell">
          <img id="intro-preview-image" class="intro-preview-media hidden" alt="Demo preview image" />
          <video
            id="intro-preview-video"
            class="intro-preview-media hidden"
            playsinline
            muted
            loop
            preload="metadata"
          ></video>
          <div id="intro-preview-placeholder" class="intro-preview-placeholder hidden">HTML walkthrough preview</div>
        </div>
      </section>

      <main id="frame-viewport" class="frame-viewport">
        <div id="frame-layout" class="frame-layout">
          <aside id="chapter-sidebar" class="chapter-sidebar hidden">
            <div class="chapter-sidebar-head">
              <div class="chapter-sidebar-title">Outline</div>
            </div>
            <div id="chapter-nav" class="chapter-nav hidden" aria-label="Chapters"></div>
          </aside>

          <div class="frame-center">
            <div id="frame-holder" class="frame-holder">
              <div id="frame-content" class="frame-content">
                <div id="player-loading" class="player-loading">Loading step...</div>

                <img id="player-image" class="media-layer hidden" alt="Demo screenshot" />
                <video id="player-video" class="media-layer hidden" playsinline preload="metadata"></video>
                <iframe
                  id="player-iframe"
                  class="media-layer hidden"
                  title="Demo HTML preview"
                  loading="lazy"
                ></iframe>

                <div id="overlay-layer" class="overlay-layer">
                  <button
                    id="player-hotspot"
                    type="button"
                    class="player-hotspot hidden variant-dot"
                    aria-label="Go to next step"
                    aria-haspopup="dialog"
                    aria-controls="player-tooltip"
                  >
                    <span class="hotspot-zoom-layer" aria-hidden="true"></span>
                  </button>
                </div>

                <a id="badge-slot" class="badge-slot hidden" target="_blank" rel="noopener noreferrer"></a>

                <div id="end-screen" class="end-screen hidden">
                  <h2>Demo complete</h2>
                  <p>You have finished this walkthrough.</p>
                  <button id="restart-end" class="btn primary">Restart</button>
                </div>

                <div id="feedback-modal" class="feedback-modal hidden" role="dialog" aria-labelledby="feedback-title" aria-modal="true">
                  <div class="feedback-card">
                    <div class="feedback-kicker">Feedback</div>
                    <h3 id="feedback-title">How useful was this demo?</h3>
                    <p>Rate your experience and leave an optional comment.</p>
                    <div id="feedback-rating" class="feedback-rating" role="radiogroup" aria-label="Feedback rating">
                      <button type="button" class="feedback-score-btn" data-score="1">1</button>
                      <button type="button" class="feedback-score-btn" data-score="2">2</button>
                      <button type="button" class="feedback-score-btn" data-score="3">3</button>
                      <button type="button" class="feedback-score-btn" data-score="4">4</button>
                      <button type="button" class="feedback-score-btn" data-score="5">5</button>
                    </div>
                    <textarea id="feedback-text" rows="3" maxlength="1200" placeholder="Optional feedback"></textarea>
                    <div id="feedback-status" class="feedback-status"></div>
                    <div class="feedback-actions">
                      <button id="feedback-skip" class="btn ghost" type="button">Skip</button>
                      <button id="feedback-submit" class="btn primary" type="button" disabled>Submit</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <div class="toolbar-wrap">
        <div class="toolbar-scrim"></div>
        <div id="player-toolbar" class="player-toolbar" role="toolbar" aria-label="Demo controls">
          <div class="player-toolbar-left">
            <button id="toggle-chapters" class="btn ghost hidden" type="button">Hide Outline</button>
            <button id="prev-step" class="btn ghost" type="button">Prev</button>
            <button id="next-step" class="btn ghost" type="button">Next</button>
            <button id="open-new-tab" class="btn ghost" type="button">Open In New Tab</button>
            <button id="fullscreen-toggle" class="btn ghost desktop-only" type="button">Fullscreen</button>
          </div>
          <div id="progress" class="progress">0 / 0</div>
          <div class="player-toolbar-right">
            <button id="restart" class="btn ghost" type="button">Restart</button>
          </div>
        </div>
      </div>
      <div id="tooltip-portal" class="tooltip-portal">
        <div id="player-arrow" class="player-arrow hidden" aria-hidden="true"></div>
        <div id="player-tooltip" class="player-tooltip hidden" role="dialog" aria-live="polite">
          <div class="tooltip-arrow" id="tooltip-arrow"></div>
          <div class="tooltip-kicker">Step</div>
          <div id="tooltip-title" class="tooltip-title"></div>
          <div id="tooltip-body" class="tooltip-body"></div>
          <div id="tooltip-hint" class="tooltip-hint">Click the highlighted area to continue</div>
          <div class="tooltip-nav">
            <button id="tooltip-prev" class="btn ghost" type="button">Back</button>
            <button id="tooltip-next" class="btn primary" type="button">Next</button>
          </div>
        </div>
      </div>
    </div>

    <script type="module" src="/static/player.js?v={{ asset_v }}"></script>
  </body>
</html>

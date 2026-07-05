(function () {
  // EDIT ME: point this at your posts.json once it's hosted (see README).
  var POSTS_URL = "https://atstizzle.github.io/my-blog/posts.json";
  var CONTAINER_ID = "soro-blog";

  function escapeHtml(str) {
    var div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function formatDate(iso) {
    var d = new Date(iso);
    return d.toLocaleDateString(undefined, {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }

  function render(container, posts) {
    if (!posts.length) {
      container.innerHTML = "<p>No posts yet — check back soon.</p>";
      return;
    }

    var html = '<div class="ai-blog-list">';
    posts.forEach(function (post, i) {
      html += [
        '<article class="ai-blog-post" data-index="' + i + '">',
        "<h2>" + escapeHtml(post.title) + "</h2>",
        '<p class="ai-blog-meta">' + formatDate(post.date) + "</p>",
        '<p class="ai-blog-excerpt">' + escapeHtml(post.meta_description) + "</p>",
        '<div class="ai-blog-body" style="display:none;">' + post.body_html + "</div>",
        '<button class="ai-blog-toggle">Read more</button>',
        "</article>",
      ].join("");
    });
    html += "</div>";
    container.innerHTML = html;

    container.querySelectorAll(".ai-blog-toggle").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var article = btn.closest(".ai-blog-post");
        var body = article.querySelector(".ai-blog-body");
        var open = body.style.display !== "none";
        body.style.display = open ? "none" : "block";
        btn.textContent = open ? "Read more" : "Show less";
      });
    });
  }

  function init() {
    var container = document.getElementById(CONTAINER_ID);
    if (!container) return;

    container.innerHTML = "<p>Loading posts…</p>";

    fetch(POSTS_URL, { cache: "no-store" })
      .then(function (res) {
        if (!res.ok) throw new Error("Failed to load posts (" + res.status + ")");
        return res.json();
      })
      .then(function (posts) {
        render(container, posts);
      })
      .catch(function (err) {
        container.innerHTML = "<p>Couldn't load posts right now.</p>";
        console.error(err);
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

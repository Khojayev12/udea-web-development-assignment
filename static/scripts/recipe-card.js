document.addEventListener("DOMContentLoaded", () => {
  const favoriteButtons = document.querySelectorAll(".recipe-card__favorite");
  const csrfToken =
    document.querySelector('meta[name="csrf-token"]')?.getAttribute("content") || "";

  const handleFavorite = async (event) => {
    event.preventDefault();
    event.stopPropagation();
    const button = event.currentTarget;
    const recipeId = button.dataset.recipeId;
    if (!recipeId) {
      return;
    }

    const isLiked = button.dataset.liked === "true";
    const method = isLiked ? "DELETE" : "POST";

    try {
      const response = await fetch(`/api/recipes/${recipeId}/favorite`, {
        method,
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
        },
      });

      const data = await response.json().catch(() => ({}));

      if (response.status === 401) {
        const redirectUrl = data.redirect || "/login";
        window.location.href = redirectUrl;
        return;
      }

      if (response.ok && typeof data.liked === "boolean") {
        if (data.liked) {
          button.classList.add("is-liked");
          button.dataset.liked = "true";
          button.setAttribute("aria-pressed", "true");
        } else {
          button.classList.remove("is-liked");
          button.dataset.liked = "false";
          button.setAttribute("aria-pressed", "false");
        }
      }
    } catch (err) {
      console.error("Failed to like recipe", err);
    }
  };

  favoriteButtons.forEach((btn) => {
    btn.addEventListener("click", handleFavorite);
  });
});

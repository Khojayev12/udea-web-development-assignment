(() => {
  const forms = document.querySelectorAll("[data-search-form]");
  if (!forms.length) {
    return;
  }

  const debounce = (fn, delay = 200) => {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), delay);
    };
  };

  const renderSuggestions = (container, results) => {
    if (!container) return;
    container.innerHTML = "";
    if (!results.length) {
      container.classList.remove("is-visible");
      return;
    }
    const list = document.createElement("div");
    list.className = "search-suggestions__list";
    results.forEach((item) => {
      const row = document.createElement("a");
      row.className = "search-suggestions__item";
      row.href = `/recipe/${item.id}`;
      row.textContent = item.title || "Recipe";
      list.appendChild(row);
    });
    container.appendChild(list);
    container.classList.add("is-visible");
  };

  forms.forEach((form) => {
    const input = form.querySelector("[data-search-input]");
    const suggestions = form.parentElement?.querySelector("[data-search-suggestions]");
    if (!input) return;

    const fetchSuggestions = debounce(async () => {
      const query = input.value.trim();
      if (!query) {
        renderSuggestions(suggestions, []);
        return;
      }
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=6`);
        if (!res.ok) {
          renderSuggestions(suggestions, []);
          return;
        }
        const data = await res.json();
        renderSuggestions(suggestions, Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Search request failed", err);
        renderSuggestions(suggestions, []);
      }
    }, 200);

    input.addEventListener("input", fetchSuggestions);
    input.addEventListener("focus", fetchSuggestions);

    document.addEventListener("click", (evt) => {
      if (!suggestions) return;
      if (!suggestions.contains(evt.target) && !form.contains(evt.target)) {
        renderSuggestions(suggestions, []);
      }
    });
  });
})();

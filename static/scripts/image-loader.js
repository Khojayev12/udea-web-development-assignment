document.addEventListener("DOMContentLoaded", () => {
  const lazyImages = Array.from(document.querySelectorAll("[data-lazy-image]"));

  const onLoad = (img) => {
    img.classList.add("is-loaded");
  };

  lazyImages.forEach((img) => {
    if (img.complete) {
      onLoad(img);
    } else {
      img.addEventListener("load", () => onLoad(img), { once: true });
      img.addEventListener(
        "error",
        () => {
          img.classList.add("is-error");
        },
        { once: true }
      );
    }
  });
});

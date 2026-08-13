/* Two small page behaviours every product gets from the theme.
 *
 * 1. --site-header-offset: the real rendered height of the sticky header,
 *    published as a CSS variable so any element that sticks below it (a
 *    sidebar, a table of contents) can clear it without guessing. The
 *    header's height depends on the product's logo size, so it has to be
 *    measured, not hardcoded.
 *
 * 2. A dependency-free lightbox. Every image inside rich text (.prose) and
 *    anything marked data-lightbox opens full-screen on click, and closes
 *    on click, Escape or the close button. Features opt content images in
 *    by rendering them inside .prose or adding the attribute.
 */
(function () {
    "use strict";

    function publishHeaderOffset() {
        var header = document.querySelector(".site-header");
        var offset = header ? header.offsetHeight + 16 : 88;
        document.documentElement.style.setProperty(
            "--site-header-offset", offset + "px"
        );
    }
    window.addEventListener("resize", publishHeaderOffset);
    publishHeaderOffset();

    var overlay = null;

    function closeLightbox() {
        if (overlay) overlay.remove();
        overlay = null;
        document.removeEventListener("keydown", onKey);
    }

    function onKey(e) {
        if (e.key === "Escape") closeLightbox();
    }

    function openLightbox(src, alt) {
        closeLightbox();
        overlay = document.createElement("div");
        overlay.className = "lightbox";
        overlay.innerHTML =
            '<button class="lightbox__close" aria-label="Close">&times;</button>' +
            '<img class="lightbox__img" alt="">';
        var img = overlay.querySelector(".lightbox__img");
        img.src = src;
        img.alt = alt || "";
        overlay.addEventListener("click", closeLightbox);
        document.addEventListener("keydown", onKey);
        document.body.appendChild(overlay);
    }

    document.addEventListener("click", function (e) {
        var img = e.target.closest(
            ".prose img, img[data-lightbox], [data-lightbox] img"
        );
        if (!img) return;
        // An image that is itself a link keeps its link.
        if (img.closest("a")) return;
        e.preventDefault();
        openLightbox(img.currentSrc || img.src, img.alt);
    });
})();

/* Two small page behaviours every product gets from the theme.
 *
 * 1. --site-header-offset: the real rendered height of the sticky header,
 *    published as a CSS variable so any element that sticks below it (a
 *    sidebar, a table of contents) can clear it without guessing. The
 *    header's height depends on the product's logo size, so it has to be
 *    measured, not hardcoded.
 *
 * 2. A dependency-free lightbox with a slideshow. Every image inside rich
 *    text (.prose), anything marked data-lightbox, and every image inside a
 *    gallery (a .gallery-grid or any element marked data-lightbox-gallery)
 *    opens large over a darkened page. Inside a gallery the reader moves
 *    with the arrows on screen, the arrow keys, a swipe or a click on the
 *    picture, and can start a slideshow (play/pause, space bar) that
 *    advances every few seconds. Escape, the close button or a click on the
 *    dark backdrop close it. When the thumbnail is wrapped in a link to the
 *    full-size image, that link is what opens (never in a new tab), so the
 *    markup degrades to a plain image link without JavaScript.
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

    var IMAGE_HREF = /\.(jpe?g|png|gif|webp|avif|svg)(\?.*)?$/i;
    var SLIDE_MS = 4000;
    var ICONS = {
        close: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
        prev: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="15 18 9 12 15 6"/></svg>',
        next: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="9 18 15 12 9 6"/></svg>',
        play: '<svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><polygon points="6 4 20 12 6 20 6 4"/></svg>',
        pause: '<svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>'
    };

    var overlay = null;
    var items = [];
    var index = 0;
    var timer = null;
    var touchX = null;
    var galleryEl = null;

    /* The full-size source of a thumbnail: the wrapping link when it points
       at an image, else the image itself. */
    function sourceOf(img) {
        var link = img.closest("a");
        if (link && link.getAttribute("href") && IMAGE_HREF.test(link.getAttribute("href"))) {
            return link.href;
        }
        return img.currentSrc || img.src;
    }

    function captionOf(img) {
        var fig = img.closest("figure");
        var cap = fig ? fig.querySelector("figcaption") : null;
        return (cap && cap.textContent.trim()) || img.getAttribute("alt") || img.getAttribute("title") || "";
    }

    function galleryOf(img) {
        return img.closest("[data-lightbox-gallery], .gallery-grid");
    }

    function collect(img) {
        galleryEl = galleryOf(img);
        var imgs = galleryEl ? galleryEl.querySelectorAll("img") : [img];
        items = [];
        index = 0;
        Array.prototype.forEach.call(imgs, function (el) {
            if (el === img) index = items.length;
            items.push({ src: sourceOf(el), caption: captionOf(el) });
        });
    }

    /* Re-read the open gallery (a page of photos was appended by infinite
       scroll); the current picture keeps its position. */
    function refresh() {
        if (!overlay || !galleryEl) return;
        var current = items[index] ? items[index].src : null;
        var imgs = galleryEl.querySelectorAll("img");
        items = [];
        Array.prototype.forEach.call(imgs, function (el) {
            items.push({ src: sourceOf(el), caption: captionOf(el) });
        });
        for (var i = 0; i < items.length; i++) {
            if (items[i].src === current) { index = i; break; }
        }
        var counter = overlay.querySelector(".lightbox__counter");
        if (counter) counter.textContent = items.length > 1 ? (index + 1) + " / " + items.length : "";
    }

    function stopSlideshow() {
        if (timer) clearInterval(timer);
        timer = null;
        if (overlay) {
            var b = overlay.querySelector(".lightbox__play");
            if (b) { b.innerHTML = ICONS.play; b.setAttribute("aria-pressed", "false"); b.setAttribute("aria-label", b.getAttribute("data-play-label")); }
            overlay.classList.remove("is-playing");
        }
    }

    function startSlideshow() {
        stopSlideshow();
        // A gallery may set its own pace (data-slideshow-ms, admin-editable
        // in the media settings); otherwise the theme default applies.
        var ms = parseInt(galleryEl && galleryEl.getAttribute("data-slideshow-ms"), 10) || SLIDE_MS;
        timer = setInterval(function () { show(index + 1); }, ms);
        var b = overlay.querySelector(".lightbox__play");
        if (b) { b.innerHTML = ICONS.pause; b.setAttribute("aria-pressed", "true"); b.setAttribute("aria-label", b.getAttribute("data-pause-label")); }
        overlay.classList.add("is-playing");
    }

    function closeLightbox() {
        stopSlideshow();
        if (overlay) overlay.remove();
        overlay = null;
        items = [];
        document.removeEventListener("keydown", onKey);
        document.body.classList.remove("lightbox-open");
    }

    function preload(i) {
        if (items.length < 2) return;
        var n = (i + items.length) % items.length;
        var im = new Image();
        im.src = items[n].src;
    }

    function show(i) {
        if (!overlay || !items.length) return;
        if (i >= items.length && galleryEl && galleryEl.getAttribute("data-gallery-next")) {
            // Past the last loaded photo: let the page fetch more (it calls
            // next() when they arrive) instead of wrapping around now.
            galleryEl.dispatchEvent(new CustomEvent("splent:lightbox:end", { bubbles: true }));
            return;
        }
        index = (i + items.length) % items.length;
        var item = items[index];
        var img = overlay.querySelector(".lightbox__img");
        img.src = item.src;
        img.alt = item.caption;
        var cap = overlay.querySelector(".lightbox__caption");
        cap.textContent = item.caption;
        cap.hidden = !item.caption;
        var counter = overlay.querySelector(".lightbox__counter");
        counter.textContent = items.length > 1 ? (index + 1) + " / " + items.length : "";
        preload(index + 1);
        preload(index - 1);
    }

    function onKey(e) {
        if (e.key === "Escape") { closeLightbox(); }
        else if (e.key === "ArrowRight") { stopSlideshow(); show(index + 1); }
        else if (e.key === "ArrowLeft") { stopSlideshow(); show(index - 1); }
        else if (e.key === " " && items.length > 1) { e.preventDefault(); timer ? stopSlideshow() : startSlideshow(); }
    }

    function labels() {
        /* Translated labels come from the shell through data attributes on
           <body>; the English fallback keeps the control usable everywhere. */
        var b = document.body.dataset;
        return {
            close: b.lightboxClose || "Close",
            prev: b.lightboxPrev || "Previous",
            next: b.lightboxNext || "Next",
            play: b.lightboxPlay || "Start slideshow",
            pause: b.lightboxPause || "Pause slideshow"
        };
    }

    function openLightbox(img, opts) {
        closeLightbox();
        collect(img);
        var L = labels();
        var multi = items.length > 1;
        overlay = document.createElement("div");
        overlay.className = "lightbox" + (multi ? " lightbox--gallery" : "");
        overlay.setAttribute("role", "dialog");
        overlay.setAttribute("aria-modal", "true");
        overlay.innerHTML =
            '<div class="lightbox__bar">' +
                '<span class="lightbox__counter" aria-live="polite"></span>' +
                (multi ? '<button type="button" class="lightbox__btn lightbox__play" aria-pressed="false" aria-label="' + L.play + '" data-play-label="' + L.play + '" data-pause-label="' + L.pause + '">' + ICONS.play + '</button>' : '') +
                '<button type="button" class="lightbox__btn lightbox__close" aria-label="' + L.close + '">' + ICONS.close + '</button>' +
            '</div>' +
            (multi ? '<button type="button" class="lightbox__btn lightbox__nav lightbox__nav--prev" aria-label="' + L.prev + '">' + ICONS.prev + '</button>' : '') +
            '<figure class="lightbox__figure"><img class="lightbox__img" alt=""><figcaption class="lightbox__caption" hidden></figcaption></figure>' +
            (multi ? '<button type="button" class="lightbox__btn lightbox__nav lightbox__nav--next" aria-label="' + L.next + '">' + ICONS.next + '</button>' : '');

        overlay.addEventListener("click", function (e) {
            var t = e.target;
            if (t.closest(".lightbox__close")) { closeLightbox(); return; }
            if (t.closest(".lightbox__play")) { timer ? stopSlideshow() : startSlideshow(); return; }
            if (t.closest(".lightbox__nav--prev")) { stopSlideshow(); show(index - 1); return; }
            if (t.closest(".lightbox__nav--next") || t.closest(".lightbox__img")) {
                if (multi) { stopSlideshow(); show(index + 1); } else { closeLightbox(); }
                return;
            }
            if (t.closest(".lightbox__caption") || t.closest(".lightbox__bar")) return;
            closeLightbox();
        });
        overlay.addEventListener("touchstart", function (e) { touchX = e.changedTouches[0].clientX; }, { passive: true });
        overlay.addEventListener("touchend", function (e) {
            if (touchX === null || !multi) return;
            var dx = e.changedTouches[0].clientX - touchX;
            touchX = null;
            if (Math.abs(dx) > 40) { stopSlideshow(); show(dx < 0 ? index + 1 : index - 1); }
        }, { passive: true });

        document.addEventListener("keydown", onKey);
        document.body.appendChild(overlay);
        document.body.classList.add("lightbox-open");
        show(index);
        var closeBtn = overlay.querySelector(".lightbox__close");
        if (closeBtn) closeBtn.focus();
        if (opts && opts.play && multi) startSlideshow();
    }

    /* Small public surface for pages that drive the lightbox themselves
       (a gallery's "Slideshow" button, infinite scroll appending photos). */
    window.splentLightbox = {
        open: openLightbox,
        close: closeLightbox,
        next: function () { show(index + 1); },
        prev: function () { show(index - 1); },
        refresh: refresh
    };

    document.addEventListener("click", function (e) {
        var img = e.target.closest(
            ".prose img, img[data-lightbox], [data-lightbox] img, [data-lightbox-gallery] img, .gallery-grid img"
        );
        if (!img) return;
        var link = img.closest("a");
        // An image that links somewhere else keeps its link; a link to the
        // full-size picture is what the lightbox opens.
        if (link && !(link.getAttribute("href") && IMAGE_HREF.test(link.getAttribute("href")))) return;
        e.preventDefault();
        openLightbox(img);
    });
})();

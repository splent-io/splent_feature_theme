/* Countdown to a moment, shell-owned so every feature that announces a date
 * (the home hero, an edition, a call for papers) renders the same markup and
 * none ships its own timer.
 *
 * Markup contract, one or many per page:
 *
 *   <div class="countdown" data-target="2026-11-03T09:00:00">
 *     <span data-d></span> <span data-h></span> <span data-m></span> <span data-s></span>
 *   </div>
 *
 * data-target is an ISO date-time read as local time when it carries no
 * zone. Once the moment has passed the counter stays at zero.
 */
(function () {
    "use strict";

    function pad(n) {
        return String(n).padStart(2, "0");
    }

    function start(el) {
        var target = new Date(el.dataset.target).getTime();
        if (isNaN(target)) {
            return;
        }
        var d = el.querySelector("[data-d]");
        var h = el.querySelector("[data-h]");
        var m = el.querySelector("[data-m]");
        var s = el.querySelector("[data-s]");

        function tick() {
            var left = target - Date.now();
            if (left < 0) {
                left = 0;
            }
            if (d) { d.textContent = Math.floor(left / 86400000); }
            if (h) { h.textContent = pad(Math.floor(left % 86400000 / 3600000)); }
            if (m) { m.textContent = pad(Math.floor(left % 3600000 / 60000)); }
            if (s) { s.textContent = pad(Math.floor(left % 60000 / 1000)); }
        }

        tick();
        setInterval(tick, 1000);
    }

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll(".countdown[data-target]").forEach(start);
    });
})();

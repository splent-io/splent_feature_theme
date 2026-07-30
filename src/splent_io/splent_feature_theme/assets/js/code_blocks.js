/* Reading chrome for code blocks: the language, and a button that copies.
 *
 * Added here rather than by the server for one reason: neither is part of
 * what the page says. A stored body is markdown that outlives this design,
 * and burying a toolbar inside the rendered HTML would mean migrating every
 * page the day the toolbar changes. The renderer emits
 * <pre><code class="language-bash">, this dresses it, and the day it stops
 * running the page is still a page with readable code in it.
 *
 * In the theme rather than in a content feature because any feature that
 * renders markdown gets code blocks, and none of them should each ship
 * their own copy button.
 */
(function () {
    "use strict";

    // What the label should say. Pygments and markdown-it both go by the
    // author's word, which is an alias as often as not, so the ones people
    // actually write are spelled out and everything else is shown as typed.
    var NAMES = {
        bash: "Bash",
        sh: "Shell",
        shell: "Shell",
        console: "Consola",
        zsh: "Zsh",
        python: "Python",
        py: "Python",
        yaml: "YAML",
        yml: "YAML",
        json: "JSON",
        xml: "XML",
        html: "HTML",
        css: "CSS",
        js: "JavaScript",
        javascript: "JavaScript",
        ts: "TypeScript",
        java: "Java",
        c: "C",
        cpp: "C++",
        ruby: "Ruby",
        groovy: "Groovy",
        php: "PHP",
        sql: "SQL",
        latex: "LaTeX",
        dockerfile: "Dockerfile",
        docker: "Dockerfile",
        ini: "INI",
        toml: "TOML",
        diff: "Diff",
        makefile: "Makefile",
    };

    var TEXTS = {
        copy: { es: "Copiar", en: "Copy" },
        copied: { es: "Copiado", en: "Copied" },
        failed: { es: "No se pudo copiar", en: "Could not copy" },
    };

    function say(key) {
        // The page already declares its language; using it here keeps the
        // button in step with the switcher without a second source.
        var lang = (document.documentElement.lang || "es").slice(0, 2);
        var entry = TEXTS[key];
        return entry[lang] || entry.en;
    }

    function languageOf(code) {
        var match = /(?:^|\s)language-([\w+#-]+)/.exec(code.className || "");
        if (!match) {
            return null;
        }
        var raw = match[1].toLowerCase();
        // "text" is what somebody writes for terminal output. It is not a
        // language and labelling it as one would be inventing structure.
        if (raw === "text" || raw === "txt" || raw === "plaintext") {
            return null;
        }
        return NAMES[raw] || match[1];
    }

    function copy(text) {
        if (navigator.clipboard && window.isSecureContext) {
            return navigator.clipboard.writeText(text);
        }
        // Plain HTTP is the ordinary case behind a university proxy, and
        // the modern API is unavailable there. This is the fallback that
        // still works, kept off the main path.
        return new Promise(function (resolve, reject) {
            var scratch = document.createElement("textarea");
            scratch.value = text;
            scratch.setAttribute("readonly", "");
            scratch.style.position = "fixed";
            scratch.style.opacity = "0";
            document.body.appendChild(scratch);
            scratch.select();
            try {
                document.execCommand("copy") ? resolve() : reject();
            } catch (error) {
                reject(error);
            } finally {
                document.body.removeChild(scratch);
            }
        });
    }

    function enhance(pre) {
        var code = pre.querySelector("code");
        if (!code || pre.parentNode.classList.contains("code-block")) {
            return;
        }

        var language = languageOf(code);

        var figure = document.createElement("figure");
        figure.className = "code-block" + (language ? "" : " code-block--bare");
        pre.parentNode.insertBefore(figure, pre);

        var bar = document.createElement("figcaption");
        bar.className = "code-block__bar";

        var label = document.createElement("span");
        label.className = "code-block__lang";
        label.textContent = language || "";
        bar.appendChild(label);

        var button = document.createElement("button");
        button.type = "button";
        button.className = "code-block__copy";
        button.textContent = say("copy");
        bar.appendChild(button);

        figure.appendChild(bar);
        figure.appendChild(pre);

        var restore = null;
        button.addEventListener("click", function () {
            copy(code.innerText).then(
                function () {
                    button.textContent = say("copied");
                    button.classList.add("is-done");
                },
                function () {
                    button.textContent = say("failed");
                }
            );
            // Announced, not only coloured: a reader using a screen reader
            // gets no feedback at all from a button that turns green.
            button.setAttribute("aria-live", "polite");
            clearTimeout(restore);
            restore = setTimeout(function () {
                button.textContent = say("copy");
                button.classList.remove("is-done");
            }, 2000);
        });
    }

    function init() {
        var blocks = document.querySelectorAll(".cms-public pre");
        Array.prototype.forEach.call(blocks, enhance);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();

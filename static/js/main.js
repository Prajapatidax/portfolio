/**
 * Main Portfolio Client Script
 * Dax Prajapati Portfolio
 */

document.addEventListener("DOMContentLoaded", () => {
    // Current Year
    const yearEl = document.getElementById("year");
    if (yearEl) {
        yearEl.textContent = new Date().getFullYear();
    }

    // Mobile Menu Toggle
    const menuToggle = document.getElementById("menu-toggle");
    const mobileMenu = document.getElementById("mobile-menu");
    const menuIcon = document.getElementById("menu-icon");
    const closeIcon = document.getElementById("close-icon");

    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener("click", () => {
            const isHidden = mobileMenu.classList.contains("hidden");
            if (isHidden) {
                mobileMenu.classList.remove("hidden");
                if (menuIcon) menuIcon.classList.add("hidden");
                if (closeIcon) closeIcon.classList.remove("hidden");
            } else {
                mobileMenu.classList.add("hidden");
                if (menuIcon) menuIcon.classList.remove("hidden");
                if (closeIcon) closeIcon.classList.add("hidden");
            }
        });
    }

    // Preloader Animation
    const preloader = document.getElementById("preloader");
    const loaderText = document.getElementById("loader-text");
    if (preloader && loaderText) {
        const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890";
        const targetText = loaderText.getAttribute("data-text") || "PRAJAPATI DAX.DEV";
        let iteration = 0;

        const interval = setInterval(() => {
            loaderText.innerText = targetText
                .split("")
                .map((letter, index) => {
                    if (index < iteration) {
                        return targetText[index];
                    }
                    return chars[Math.floor(Math.random() * chars.length)];
                })
                .join("");

            if (iteration >= targetText.length) {
                clearInterval(interval);
                setTimeout(() => {
                    preloader.style.opacity = "0";
                    setTimeout(() => {
                        preloader.style.display = "none";
                    }, 400);
                }, 300);
            }
            iteration += 1 / 3;
        }, 25);
    }

    // Scroll Reveal Observer
    const reveals = document.querySelectorAll(".reveal");
    if (reveals.length > 0 && "IntersectionObserver" in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("active");
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12 });

        reveals.forEach((el) => observer.observe(el));
    }
});

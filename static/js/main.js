/**
 * Main Portfolio Client Script
 * Dax Prajapati Portfolio
 */

function initMainApp() {
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

    // Preloader Dismissal Safeguard
    const preloader = document.getElementById("preloader");
    if (preloader && preloader.style.display !== "none") {
        preloader.style.opacity = "0";
        setTimeout(() => {
            preloader.style.display = "none";
        }, 200);
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
}

// Safely execute whether DOM is already parsed or still loading
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initMainApp);
} else {
    initMainApp();
}

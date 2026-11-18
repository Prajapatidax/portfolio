/**
 * UI Design Showcase Interactivity
 */

(function () {
    const SELECTED_KEY = "prajapati_selected_designs";

    function getSelectedDesigns() {
        try {
            const raw = localStorage.getItem(SELECTED_KEY);
            return raw ? JSON.parse(raw) : [];
        } catch (e) {
            return [];
        }
    }

    function saveSelectedDesigns(designs) {
        try {
            localStorage.setItem(SELECTED_KEY, JSON.stringify(designs));
        } catch (e) {
            console.warn("Could not save selected designs:", e);
        }
        updateUI();
    }

    function toggleDesign(designId, designName) {
        let list = getSelectedDesigns();
        const existingIndex = list.findIndex((item) => (typeof item === "object" ? item.id === designId : item === designId));

        if (existingIndex >= 0) {
            list.splice(existingIndex, 1);
        } else {
            list.push({ id: designId, name: designName });
        }

        saveSelectedDesigns(list);
    }

    function updateUI() {
        const list = getSelectedDesigns();
        const count = list.length;
        const selectedIds = list.map((item) => (typeof item === "object" ? item.id : item));

        // Update card buttons
        document.querySelectorAll("[data-design-select-btn]").forEach((btn) => {
            const id = btn.getAttribute("data-design-id");
            const isSelected = selectedIds.includes(id);

            if (isSelected) {
                btn.classList.add("bg-blue-600", "text-white", "border-blue-600");
                btn.classList.remove("bg-white", "text-gray-700", "border-gray-200");
                btn.innerHTML = `<span class="material-symbols-outlined !text-[18px]">check_circle</span> Selected`;
            } else {
                btn.classList.remove("bg-blue-600", "text-white", "border-blue-600");
                btn.classList.add("bg-white", "text-gray-700", "border-gray-200");
                btn.innerHTML = `<span class="material-symbols-outlined !text-[18px]">add_circle</span> Select Design`;
            }
        });

        // Update sticky floating bottom bar
        const stickyBar = document.getElementById("sticky-quote-bar");
        const countBadge = document.getElementById("selected-designs-count");
        if (stickyBar && countBadge) {
            countBadge.textContent = count;
            if (count > 0) {
                stickyBar.classList.add("active");
            } else {
                stickyBar.classList.remove("active");
            }
        }
    }

    // Expose toggle globally
    window.toggleShowcaseDesign = function (designId, designName) {
        toggleDesign(designId, designName);
    };

    window.getSelectedDesignObjects = function () {
        return getSelectedDesigns();
    };

    document.addEventListener("DOMContentLoaded", () => {
        updateUI();

        // Attach event listeners to all select buttons
        document.querySelectorAll("[data-design-select-btn]").forEach((btn) => {
            btn.addEventListener("click", (e) => {
                e.preventDefault();
                const id = btn.getAttribute("data-design-id");
                const name = btn.getAttribute("data-design-name");
                toggleDesign(id, name);
            });
        });

        // Category filter buttons
        const filterPills = document.querySelectorAll("[data-category-filter]");
        const designCards = document.querySelectorAll("[data-design-card]");

        filterPills.forEach((pill) => {
            pill.addEventListener("click", () => {
                const targetSlug = pill.getAttribute("data-category-filter");

                filterPills.forEach((p) => {
                    p.classList.remove("bg-blue-600", "text-white");
                    p.classList.add("bg-gray-100", "text-gray-700");
                });
                pill.classList.remove("bg-gray-100", "text-gray-700");
                pill.classList.add("bg-blue-600", "text-white");

                designCards.forEach((card) => {
                    const cardCat = card.getAttribute("data-category-slug");
                    if (targetSlug === "all" || cardCat === targetSlug) {
                        card.style.display = "block";
                        card.classList.add("reveal", "active");
                    } else {
                        card.style.display = "none";
                    }
                });
            });
        });
    });
})();

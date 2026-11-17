/**
 * Multi-Step Customization & Quotation Request Wizard
 * Relative URL communication with Flask backend
 */

(function () {
    let currentStep = 1;
    const totalSteps = 6;

    const wizardState = {
        project_type: "Portfolio Website",
        selected_designs: [],
        customization: {
            primary_color: "#2563EB",
            secondary_color: "#0F172A",
            theme_mode: "light",
            typography_preference: "Plus Jakarta Sans + Inter",
            animation_preference: "Smooth & Subtle",
            layout_preference: "Modern Grid",
            platform_preference: "desktop-first",
        },
        features: [
            "Responsive design",
            "Contact forms",
            "SEO optimization",
            "Animations",
        ],
        customer_name: "",
        customer_email: "",
        customer_phone: "",
        project_name: "",
        project_description: "",
        timeline: "2-3 Weeks",
        budget_range: "₹10,000–₹25,000",
        reference_website: "",
    };

    function init() {
        // Load any previously selected designs from showcase
        try {
            const raw = localStorage.getItem("prajapati_selected_designs");
            if (raw) {
                const list = JSON.parse(raw);
                wizardState.selected_designs = list.map((item) => (typeof item === "object" ? item.id : item));
            }
        } catch (e) {}

        renderStep(1);
        bindStep1();
        bindStep2();
        bindStep3();
        bindStep4();
        bindStep5();
        bindStep6();
    }

    function goToStep(step) {
        if (step < 1 || step > totalSteps) return;

        // Step validation
        if (step > currentStep) {
            if (!validateStep(currentStep)) return;
        }

        currentStep = step;
        renderStep(currentStep);

        const wizardRoot = document.getElementById("quotation-wizard-root");
        if (wizardRoot) {
            wizardRoot.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    }

    function validateStep(step) {
        const errorContainer = document.getElementById(`step-${step}-error`);
        if (errorContainer) errorContainer.innerHTML = "";

        if (step === 1) {
            if (!wizardState.project_type) {
                showError(step, "Please select a project type to continue.");
                return false;
            }
        } else if (step === 5) {
            const name = document.getElementById("input-customer-name")?.value.trim();
            const email = document.getElementById("input-customer-email")?.value.trim();
            const projName = document.getElementById("input-project-name")?.value.trim();
            const projDesc = document.getElementById("input-project-desc")?.value.trim();

            if (!name || name.length < 2) {
                showError(5, "Please enter your full name (minimum 2 characters).");
                return false;
            }
            if (!email || !/^[\w\.-]+@([\w-]+\.)+[\w-]{2,10}$/.test(email)) {
                showError(5, "Please enter a valid email address.");
                return false;
            }
            if (!projName || projName.length < 2) {
                showError(5, "Please give your project a name or title.");
                return false;
            }
            if (!projDesc || projDesc.length < 10) {
                showError(5, "Please describe what you want to build (at least 10 characters).");
                return false;
            }

            // Sync with state
            wizardState.customer_name = name;
            wizardState.customer_email = email;
            wizardState.customer_phone = document.getElementById("input-customer-phone")?.value.trim() || "";
            wizardState.project_name = projName;
            wizardState.project_description = projDesc;
            wizardState.reference_website = document.getElementById("input-reference-website")?.value.trim() || "";
            wizardState.budget_range = document.getElementById("select-budget-range")?.value || "₹10,000–₹25,000";
            wizardState.timeline = document.getElementById("select-timeline")?.value || "2-3 Weeks";
        }
        return true;
    }

    function showError(step, message) {
        const errorContainer = document.getElementById(`step-${step}-error`);
        if (errorContainer) {
            errorContainer.innerHTML = `
                <div class="p-3 mb-4 text-xs font-semibold text-red-700 bg-red-50 rounded-xl border border-red-200 flex items-center gap-2">
                    <span class="material-symbols-outlined !text-[18px]">error</span> ${message}
                </div>`;
        }
    }

    function renderStep(step) {
        // Toggle step panels
        for (let i = 1; i <= totalSteps; i++) {
            const panel = document.getElementById(`wizard-step-panel-${i}`);
            if (panel) {
                if (i === step) {
                    panel.classList.remove("hidden");
                } else {
                    panel.classList.add("hidden");
                }
            }
        }

        // Update progress bar
        const progressFill = document.getElementById("wizard-progress-bar-fill");
        const progressText = document.getElementById("wizard-step-indicator-text");
        if (progressFill) {
            const percent = ((step - 1) / (totalSteps - 1)) * 100;
            progressFill.style.width = `${percent}%`;
        }
        if (progressText) {
            progressText.textContent = `Step ${step} of ${totalSteps}`;
        }

        // If step 2, update selected designs list
        if (step === 2) {
            updateStep2Display();
        }

        // If step 6, build review summary
        if (step === 6) {
            buildReviewSummary();
        }
    }

    // Step 1: Project Type
    function bindStep1() {
        const cards = document.querySelectorAll("[data-project-type-card]");
        cards.forEach((card) => {
            card.addEventListener("click", () => {
                const type = card.getAttribute("data-project-type");
                wizardState.project_type = type;

                cards.forEach((c) => {
                    c.classList.remove("border-blue-600", "bg-blue-50/50");
                    c.classList.add("border-gray-200", "bg-white");
                });
                card.classList.remove("border-gray-200", "bg-white");
                card.classList.add("border-blue-600", "bg-blue-50/50");
            });
        });

        document.getElementById("btn-step1-next")?.addEventListener("click", () => goToStep(2));
    }

    // Step 2: Select Design
    function bindStep2() {
        document.getElementById("btn-step2-prev")?.addEventListener("click", () => goToStep(1));
        document.getElementById("btn-step2-next")?.addEventListener("click", () => goToStep(3));

        // Design chips toggle in step 2
        document.querySelectorAll("[data-wizard-design-chip]").forEach((chip) => {
            chip.addEventListener("click", () => {
                const dId = chip.getAttribute("data-wizard-design-chip");
                const idx = wizardState.selected_designs.indexOf(dId);
                if (idx >= 0) {
                    wizardState.selected_designs.splice(idx, 1);
                    chip.classList.remove("bg-blue-600", "text-white");
                    chip.classList.add("bg-gray-100", "text-gray-700");
                } else {
                    wizardState.selected_designs.push(dId);
                    chip.classList.remove("bg-gray-100", "text-gray-700");
                    chip.classList.add("bg-blue-600", "text-white");
                }
                updateStep2Display();
            });
        });
    }

    function updateStep2Display() {
        const countSpan = document.getElementById("step-2-selected-count");
        if (countSpan) {
            countSpan.textContent = wizardState.selected_designs.length;
        }
        document.querySelectorAll("[data-wizard-design-chip]").forEach((chip) => {
            const dId = chip.getAttribute("data-wizard-design-chip");
            if (wizardState.selected_designs.includes(dId)) {
                chip.classList.remove("bg-gray-100", "text-gray-700");
                chip.classList.add("bg-blue-600", "text-white");
            } else {
                chip.classList.remove("bg-blue-600", "text-white");
                chip.classList.add("bg-gray-100", "text-gray-700");
            }
        });
    }

    // Step 3: Customize Design
    function bindStep3() {
        document.getElementById("btn-step3-prev")?.addEventListener("click", () => goToStep(2));
        document.getElementById("btn-step3-next")?.addEventListener("click", () => goToStep(4));

        // Primary Color Picker
        const primaryPicker = document.getElementById("custom-primary-color");
        if (primaryPicker) {
            primaryPicker.addEventListener("input", (e) => {
                wizardState.customization.primary_color = e.target.value;
            });
        }

        // Secondary Color Picker
        const secondaryPicker = document.getElementById("custom-secondary-color");
        if (secondaryPicker) {
            secondaryPicker.addEventListener("input", (e) => {
                wizardState.customization.secondary_color = e.target.value;
            });
        }

        // Theme Mode
        document.querySelectorAll("[data-theme-option]").forEach((opt) => {
            opt.addEventListener("click", () => {
                const mode = opt.getAttribute("data-theme-option");
                wizardState.customization.theme_mode = mode;
                document.querySelectorAll("[data-theme-option]").forEach((o) => {
                    o.classList.remove("border-blue-600", "bg-blue-50");
                    o.classList.add("border-gray-200", "bg-white");
                });
                opt.classList.remove("border-gray-200", "bg-white");
                opt.classList.add("border-blue-600", "bg-blue-50");
            });
        });

        // Typography Preference
        const typoSelect = document.getElementById("select-typography");
        if (typoSelect) {
            typoSelect.addEventListener("change", (e) => {
                wizardState.customization.typography_preference = e.target.value;
            });
        }

        // Animation Preference
        const animSelect = document.getElementById("select-animation");
        if (animSelect) {
            animSelect.addEventListener("change", (e) => {
                wizardState.customization.animation_preference = e.target.value;
            });
        }

        // Layout Preference
        const layoutSelect = document.getElementById("select-layout");
        if (layoutSelect) {
            layoutSelect.addEventListener("change", (e) => {
                wizardState.customization.layout_preference = e.target.value;
            });
        }

        // Platform First
        document.querySelectorAll("[data-platform-option]").forEach((opt) => {
            opt.addEventListener("click", () => {
                const plat = opt.getAttribute("data-platform-option");
                wizardState.customization.platform_preference = plat;
                document.querySelectorAll("[data-platform-option]").forEach((o) => {
                    o.classList.remove("border-blue-600", "bg-blue-50");
                    o.classList.add("border-gray-200", "bg-white");
                });
                opt.classList.remove("border-gray-200", "bg-white");
                opt.classList.add("border-blue-600", "bg-blue-50");
            });
        });
    }

    // Step 4: Required Features
    function bindStep4() {
        document.getElementById("btn-step4-prev")?.addEventListener("click", () => goToStep(3));
        document.getElementById("btn-step4-next")?.addEventListener("click", () => goToStep(5));

        document.querySelectorAll("[data-feature-chip]").forEach((chip) => {
            chip.addEventListener("click", () => {
                const feat = chip.getAttribute("data-feature-chip");
                const idx = wizardState.features.indexOf(feat);
                if (idx >= 0) {
                    wizardState.features.splice(idx, 1);
                    chip.classList.remove("bg-blue-600", "text-white", "border-blue-600");
                    chip.classList.add("bg-white", "text-gray-700", "border-gray-200");
                } else {
                    wizardState.features.push(feat);
                    chip.classList.remove("bg-white", "text-gray-700", "border-gray-200");
                    chip.classList.add("bg-blue-600", "text-white", "border-blue-600");
                }
            });
        });
    }

    // Step 5: Project & Customer Details
    function bindStep5() {
        document.getElementById("btn-step5-prev")?.addEventListener("click", () => goToStep(4));
        document.getElementById("btn-step5-next")?.addEventListener("click", () => goToStep(6));
    }

    // Step 6: Review and Submit
    function bindStep6() {
        document.getElementById("btn-step6-prev")?.addEventListener("click", () => goToStep(5));

        // Submit Button
        const submitBtn = document.getElementById("btn-submit-quotation");
        if (submitBtn) {
            submitBtn.addEventListener("click", submitQuotation);
        }
    }

    function buildReviewSummary() {
        const reviewContainer = document.getElementById("review-summary-content");
        if (!reviewContainer) return;

        const cust = wizardState.customization;
        const designs = wizardState.selected_designs.length > 0 ? wizardState.selected_designs.join(", ") : "Standard Custom Architecture";
        const feats = wizardState.features.length > 0 ? wizardState.features.join(", ") : "Standard Core Features";

        reviewContainer.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div class="bg-gray-50 p-4 rounded-2xl border border-gray-100">
                    <div class="flex justify-between items-center mb-1">
                        <span class="text-xs font-bold text-gray-400 uppercase tracking-wider">Project Scope</span>
                        <button type="button" onclick="window.goToWizardStep(1)" class="text-xs text-blue-600 font-bold hover:underline">Edit</button>
                    </div>
                    <p class="font-extrabold text-gray-900 text-base">${wizardState.project_name || "Untitled Project"}</p>
                    <p class="text-gray-600 mt-0.5"><span class="font-medium">Type:</span> ${wizardState.project_type}</p>
                    <p class="text-gray-600"><span class="font-medium">Budget:</span> <span class="font-bold text-blue-600">${wizardState.budget_range}</span></p>
                    <p class="text-gray-600"><span class="font-medium">Timeline:</span> ${wizardState.timeline}</p>
                </div>

                <div class="bg-gray-50 p-4 rounded-2xl border border-gray-100">
                    <div class="flex justify-between items-center mb-1">
                        <span class="text-xs font-bold text-gray-400 uppercase tracking-wider">Contact Info</span>
                        <button type="button" onclick="window.goToWizardStep(5)" class="text-xs text-blue-600 font-bold hover:underline">Edit</button>
                    </div>
                    <p class="font-extrabold text-gray-900 text-base">${wizardState.customer_name || "N/A"}</p>
                    <p class="text-gray-600 mt-0.5"><span class="font-medium">Email:</span> ${wizardState.customer_email}</p>
                    <p class="text-gray-600"><span class="font-medium">Phone:</span> ${wizardState.customer_phone || "Not provided"}</p>
                    ${wizardState.reference_website ? `<p class="text-gray-600 truncate"><span class="font-medium">Ref Site:</span> ${wizardState.reference_website}</p>` : ""}
                </div>

                <div class="bg-gray-50 p-4 rounded-2xl border border-gray-100 md:col-span-2">
                    <div class="flex justify-between items-center mb-1">
                        <span class="text-xs font-bold text-gray-400 uppercase tracking-wider">Selected Design & Styling</span>
                        <button type="button" onclick="window.goToWizardStep(3)" class="text-xs text-blue-600 font-bold hover:underline">Edit</button>
                    </div>
                    <p class="text-gray-800 font-medium mb-1"><span class="font-bold">Design References:</span> ${designs}</p>
                    <div class="flex flex-wrap items-center gap-3 mt-2 text-xs">
                        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white border border-gray-200">
                            <span class="w-3 h-3 rounded-full border border-gray-300" style="background-color: ${cust.primary_color}"></span>
                            Primary: ${cust.primary_color}
                        </span>
                        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white border border-gray-200">
                            <span class="w-3 h-3 rounded-full border border-gray-300" style="background-color: ${cust.secondary_color}"></span>
                            Secondary: ${cust.secondary_color}
                        </span>
                        <span class="px-2.5 py-1 rounded-full bg-white border border-gray-200 font-medium">Theme: ${cust.theme_mode}</span>
                        <span class="px-2.5 py-1 rounded-full bg-white border border-gray-200 font-medium">Platform: ${cust.platform_preference}</span>
                    </div>
                </div>

                <div class="bg-gray-50 p-4 rounded-2xl border border-gray-100 md:col-span-2">
                    <div class="flex justify-between items-center mb-1">
                        <span class="text-xs font-bold text-gray-400 uppercase tracking-wider">Selected Features</span>
                        <button type="button" onclick="window.goToWizardStep(4)" class="text-xs text-blue-600 font-bold hover:underline">Edit</button>
                    </div>
                    <p class="text-gray-700 text-xs leading-relaxed">${feats}</p>
                </div>
            </div>
        `;
    }

    async function submitQuotation() {
        const submitBtn = document.getElementById("btn-submit-quotation");
        const statusBox = document.getElementById("submission-status-box");

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg> Submitting Request...
            `;
        }

        if (statusBox) statusBox.innerHTML = "";

        try {
            // RELATIVE URL: Never hardcode localhost or production domain!
            const response = await fetch("/api/quotation", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(wizardState),
            });

            const result = await response.json();

            if (response.ok && result.status === "success") {
                // Clear selections from storage
                localStorage.removeItem("prajapati_selected_designs");

                // Display Confirmation Screen
                renderConfirmationScreen(result);
            } else {
                let errorMsg = result.message || "Failed to submit quotation. Please check your inputs.";
                if (result.errors) {
                    const errorList = Object.values(result.errors).join("<br>");
                    errorMsg += `<br><span class="font-normal text-xs">${errorList}</span>`;
                }
                if (statusBox) {
                    statusBox.innerHTML = `
                        <div class="p-4 mb-4 text-sm font-semibold text-red-700 bg-red-50 rounded-2xl border border-red-200">
                            ${errorMsg}
                        </div>`;
                }
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = `Submit Quotation Request <span class="material-symbols-outlined !text-[18px]">send</span>`;
                }
            }
        } catch (err) {
            console.error("Submission error:", err);
            if (statusBox) {
                statusBox.innerHTML = `
                    <div class="p-4 mb-4 text-sm font-semibold text-red-700 bg-red-50 rounded-2xl border border-red-200">
                        A network error occurred. Please verify your connection and try again.
                    </div>`;
            }
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = `Submit Quotation Request <span class="material-symbols-outlined !text-[18px]">send</span>`;
            }
        }
    }

    function renderConfirmationScreen(result) {
        const panel = document.getElementById("quotation-wizard-card");
        if (!panel) return;

        const refId = result.reference_id || "QT-CONFIRMED";

        panel.innerHTML = `
            <div class="text-center py-10 px-4">
                <div class="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner">
                    <span class="material-symbols-outlined !text-[44px]">check_circle</span>
                </div>
                <span class="text-xs font-bold text-green-600 uppercase tracking-widest bg-green-50 px-3 py-1 rounded-full border border-green-200">Request Confirmed</span>
                <h2 class="text-3xl font-extrabold text-gray-900 mt-4 mb-2">Your project request has been received successfully.</h2>
                <p class="text-gray-600 max-w-lg mx-auto text-sm mb-6">
                    Thank you for reaching out! I will review your design preferences, requirements, and provide a tailored proposal within 24–48 hours.
                </p>

                <div class="max-w-md mx-auto bg-gray-50 border border-gray-200 rounded-3xl p-6 mb-8 text-left shadow-sm">
                    <div class="flex items-center justify-between pb-4 border-b border-gray-200">
                        <span class="text-xs font-bold text-gray-500 uppercase tracking-wider">Reference ID</span>
                        <div class="flex items-center gap-2">
                            <span class="font-mono font-black text-lg text-blue-600 tracking-wider">${refId}</span>
                            <button type="button" onclick="navigator.clipboard.writeText('${refId}'); alert('Reference ID copied to clipboard!');" class="p-1 rounded hover:bg-gray-200 text-gray-500" title="Copy Reference ID">
                                <span class="material-symbols-outlined !text-[16px]">content_copy</span>
                            </button>
                        </div>
                    </div>
                    <div class="pt-4 space-y-2 text-xs text-gray-600">
                        <div class="flex justify-between">
                            <span class="text-gray-400 font-medium">Customer:</span>
                            <span class="font-semibold text-gray-800">${wizardState.customer_name}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400 font-medium">Email:</span>
                            <span class="font-semibold text-gray-800">${wizardState.customer_email}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400 font-medium">Project:</span>
                            <span class="font-semibold text-gray-800">${wizardState.project_name}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400 font-medium">Estimated Budget:</span>
                            <span class="font-bold text-blue-600">${wizardState.budget_range}</span>
                        </div>
                    </div>
                </div>

                <div class="flex items-center justify-center gap-4 flex-wrap">
                    <a href="/" class="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm px-6 py-3 rounded-full transition-all shadow-md">
                        Back to Home
                    </a>
                    <a href="/projects" class="bg-gray-100 hover:bg-gray-200 text-gray-800 font-semibold text-sm px-6 py-3 rounded-full transition-all">
                        Explore My Projects
                    </a>
                </div>
            </div>
        `;
    }

    // Expose jump step for "Edit" buttons in Step 6
    window.goToWizardStep = function (step) {
        goToStep(step);
    };

    document.addEventListener("DOMContentLoaded", init);
})();

/**
 * Admin Dashboard Management Scripts
 */

document.addEventListener("DOMContentLoaded", () => {
    // Quotation Details Modal
    const detailModal = document.getElementById("quotation-detail-modal");
    const detailContent = document.getElementById("quotation-detail-content");

    window.viewQuotationDetails = async function (quoteId) {
        if (!detailModal || !detailContent) return;

        detailContent.innerHTML = `
            <div class="py-12 text-center text-gray-500">
                <svg class="animate-spin h-6 w-6 text-blue-600 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                Loading quotation details...
            </div>
        `;
        detailModal.classList.remove("hidden");

        try {
            const res = await fetch(`/admin/quotations/${quoteId}`);
            const data = await res.json();

            if (res.ok && data.status === "success") {
                const q = data.quotation;
                const designs = q.selected_designs.map(d => `<span class="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-md border border-blue-100 font-semibold">${d.design_name} (${d.design_id})</span>`).join(" ") || "None";
                const features = q.features.map(f => `<span class="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded-md">${f}</span>`).join(" ") || "None";
                const notes = q.notes.map(n => `<div class="bg-amber-50 border border-amber-200 rounded-xl p-3 text-xs text-amber-900 mb-2"><div class="flex justify-between font-bold mb-1"><span>${n.admin_name}</span><span>${n.created_at}</span></div><p>${n.note_text}</p></div>`).join("") || "<p class='text-xs text-gray-400'>No internal notes yet.</p>";
                const history = q.history.map(h => `<li class="text-xs text-gray-600 mb-1.5"><span class="font-bold text-gray-900">${h.created_at}:</span> ${h.comments}</li>`).join("") || "<li class='text-xs text-gray-400'>No history recorded.</li>";

                detailContent.innerHTML = `
                    <div class="space-y-4 text-sm">
                        <div class="flex justify-between items-start pb-3 border-b border-gray-100">
                            <div>
                                <span class="text-xs font-bold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-full uppercase tracking-wider">${q.reference_id}</span>
                                <h3 class="text-xl font-extrabold text-gray-900 mt-2">${q.project_name}</h3>
                                <p class="text-xs text-gray-500">Submitted on ${q.created_at}</p>
                            </div>
                            <span class="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${getStatusBadgeClass(q.status)}">${q.status.replace('_', ' ')}</span>
                        </div>

                        <div class="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded-2xl">
                            <div>
                                <span class="text-xs text-gray-400 uppercase font-bold">Customer</span>
                                <p class="font-bold text-gray-900">${q.customer_name}</p>
                                <p class="text-xs text-gray-600">${q.customer_email}</p>
                                <p class="text-xs text-gray-600">${q.customer_phone || "No phone"}</p>
                            </div>
                            <div>
                                <span class="text-xs text-gray-400 uppercase font-bold">Project Details</span>
                                <p class="text-gray-900 font-semibold">${q.project_type}</p>
                                <p class="text-xs text-gray-600 font-medium">Budget: <span class="text-blue-600 font-bold">${q.budget_range}</span></p>
                                <p class="text-xs text-gray-600">Timeline: ${q.timeline}</p>
                            </div>
                        </div>

                        <div>
                            <span class="text-xs text-gray-400 uppercase font-bold">Project Description</span>
                            <div class="bg-white border border-gray-200 p-3 rounded-xl mt-1 text-xs text-gray-700 whitespace-pre-line leading-relaxed max-h-40 overflow-y-auto">
                                ${q.project_description}
                            </div>
                        </div>

                        <div>
                            <span class="text-xs text-gray-400 uppercase font-bold">Selected Design References</span>
                            <div class="flex flex-wrap gap-1.5 mt-1">${designs}</div>
                        </div>

                        <div>
                            <span class="text-xs text-gray-400 uppercase font-bold">Requested Features</span>
                            <div class="flex flex-wrap gap-1.5 mt-1">${features}</div>
                        </div>

                        <!-- Update Status Form -->
                        <div class="pt-4 border-t border-gray-100">
                            <h4 class="text-xs font-bold text-gray-900 uppercase tracking-wider mb-2">Update Quotation Status</h4>
                            <form action="/admin/quotations/${q.id}/status" method="POST" class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                <div>
                                    <label class="block text-xs font-medium text-gray-600 mb-1">Status</label>
                                    <select name="status" class="w-full text-xs rounded-xl border border-gray-200 p-2 focus:ring-2 focus:ring-blue-500">
                                        <option value="new" ${q.status === 'new' ? 'selected' : ''}>New</option>
                                        <option value="under_review" ${q.status === 'under_review' ? 'selected' : ''}>Under Review</option>
                                        <option value="quotation_sent" ${q.status === 'quotation_sent' ? 'selected' : ''}>Quotation Sent</option>
                                        <option value="accepted" ${q.status === 'accepted' ? 'selected' : ''}>Accepted</option>
                                        <option value="rejected" ${q.status === 'rejected' ? 'selected' : ''}>Rejected</option>
                                    </select>
                                </div>
                                <div>
                                    <label class="block text-xs font-medium text-gray-600 mb-1">Proposed Quote (₹)</label>
                                    <input type="text" name="proposed_amount" value="${q.proposed_amount || ''}" placeholder="e.g. ₹25,000" class="w-full text-xs rounded-xl border border-gray-200 p-2 focus:ring-2 focus:ring-blue-500">
                                </div>
                                <div>
                                    <label class="block text-xs font-medium text-gray-600 mb-1">Estimated Delivery</label>
                                    <input type="text" name="estimated_delivery" value="${q.estimated_delivery || ''}" placeholder="e.g. 14 Days" class="w-full text-xs rounded-xl border border-gray-200 p-2 focus:ring-2 focus:ring-blue-500">
                                </div>
                                <div class="sm:col-span-3 flex justify-end">
                                    <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs px-4 py-2 rounded-xl transition-colors">
                                        Save Status Changes
                                    </button>
                                </div>
                            </form>
                        </div>

                        <!-- Add Internal Note -->
                        <div class="pt-4 border-t border-gray-100">
                            <h4 class="text-xs font-bold text-gray-900 uppercase tracking-wider mb-2">Internal Admin Notes</h4>
                            <div class="mb-3">${notes}</div>
                            <form action="/admin/quotations/${q.id}/note" method="POST" class="flex gap-2">
                                <input type="text" name="note_text" placeholder="Write internal note..." required class="flex-1 text-xs rounded-xl border border-gray-200 p-2 focus:ring-2 focus:ring-blue-500">
                                <button type="submit" class="bg-gray-800 hover:bg-black text-white font-bold text-xs px-3 py-2 rounded-xl transition-colors">
                                    Add Note
                                </button>
                            </form>
                        </div>

                        <!-- Audit History -->
                        <div class="pt-4 border-t border-gray-100">
                            <h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Audit History</h4>
                            <ul class="list-disc pl-4 space-y-1">${history}</ul>
                        </div>
                    </div>
                `;
            } else {
                detailContent.innerHTML = `<div class="p-4 text-center text-red-600 font-semibold text-sm">Failed to load quotation details.</div>`;
            }
        } catch (e) {
            detailContent.innerHTML = `<div class="p-4 text-center text-red-600 font-semibold text-sm">Error connecting to server.</div>`;
        }
    };

    window.closeQuotationDetailModal = function () {
        if (detailModal) detailModal.classList.add("hidden");
    };

    function getStatusBadgeClass(status) {
        switch (status) {
            case "new":
                return "bg-blue-100 text-blue-800";
            case "under_review":
                return "bg-amber-100 text-amber-800";
            case "quotation_sent":
                return "bg-purple-100 text-purple-800";
            case "accepted":
                return "bg-emerald-100 text-emerald-800";
            case "rejected":
                return "bg-red-100 text-red-800";
            default:
                return "bg-gray-100 text-gray-800";
        }
    }

    // Modal click-outside dismissal
    if (detailModal) {
        detailModal.addEventListener("click", (e) => {
            if (e.target === detailModal) {
                window.closeQuotationDetailModal();
            }
        });
    }
});

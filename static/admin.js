function formatInr(value) {
  return `Rs. ${Number(value || 0).toLocaleString("en-IN")}`;
}

const orderStatuses = ["pending", "awaiting_staff", "paid", "processing", "completed", "cancelled", "refunded"];
let adminOrdersCache = [];
let adminFeedbackCache = [];

function feedbackStarsHtml(rating) {
  const value = Math.max(0, Math.min(5, Number(rating) || 0));
  return Array.from({ length: 5 }, (_, index) => `<span class="fb-star ${index < value ? "filled" : ""}">&#9733;</span>`).join("");
}

function renderAdminFeedback() {
  const container = document.getElementById("adminFeedback");
  if (!container) return;
  container.innerHTML = adminFeedbackCache.length ? adminFeedbackCache.map(entry => `
    <div class="order-row admin-feedback-row" data-feedback="${entry.id}">
      <div>
        <strong>${clean(entry.playerName)}</strong>
        <span class="feedback-stars">${feedbackStarsHtml(entry.rating)}</span>
        <span>${clean(entry.message || "")}</span>
      </div>
      <button class="admin-feedback-remove" type="button" data-remove-feedback="${entry.id}">Remove</button>
    </div>
  `).join("") : "<p>No feedback submitted yet.</p>";
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, { ...options, headers: { "Content-Type": "application/json", ...(options.headers || {}) } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Request failed.");
  return data;
}

function clean(text) {
  return String(text || "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
}

function statusLabel(status) {
  return String(status || "").replace(/_/g, " ").replace(/\b\w/g, char => char.toUpperCase());
}

function renderAdminOrders() {
  const search = String(document.getElementById("orderSearch")?.value || "").toLowerCase().trim();
  const status = String(document.getElementById("orderStatusFilter")?.value || "");
  const orders = adminOrdersCache.filter(order => {
    const haystack = `${order.orderId} ${order.discordUsername} ${order.minecraftIgn || ""}`.toLowerCase();
    return (!search || haystack.includes(search)) && (!status || order.status === status);
  });

  document.getElementById("adminOrders").innerHTML = orders.length ? orders.slice(0, 200).map(order => `
    <div class="order-row admin-order-row" data-order="${clean(order.orderId)}">
      <div>
        <strong>${clean(order.orderId)}</strong>
        <span>${clean(order.discordUsername)} | ${clean(order.minecraftIgn || "No Minecraft linked")}</span>
        <span>Coupon: ${clean(order.coupon || "None")} | Discount: ${formatInr(order.discount)}</span>
      </div>
      <div class="admin-order-actions">
        <strong>${formatInr(order.finalTotal)}</strong>
        <select data-status-for="${clean(order.orderId)}">
          ${orderStatuses.map(item => `<option value="${item}" ${item === order.status ? "selected" : ""}>${statusLabel(item)}</option>`).join("")}
        </select>
        <button class="ghost-action" type="button" data-update-order="${clean(order.orderId)}">Update</button>
        <a class="ghost-action" href="/orders/${encodeURIComponent(order.orderId)}">View</a>
      </div>
    </div>
  `).join("") : "<p>No matching orders.</p>";
}

async function loadAdmin() {
  try {
    const overview = await requestJson("/api/admin/overview");
    document.getElementById("adminStats").innerHTML = [
      ["Users", overview.totalUsers],
      ["Products", overview.totalProducts],
      ["Pending Orders", overview.pendingOrders],
      ["Completed Orders", overview.completedOrders],
      ["Revenue", formatInr(overview.revenue)],
      ["Coupons", overview.coupons],
      ["Admins", overview.admins],
    ].map(([label, value]) => `<article><h3>${label}</h3><p>${value}</p></article>`).join("");
    adminOrdersCache = await requestJson("/api/admin/orders");
    renderAdminOrders();
    adminFeedbackCache = await requestJson("/api/admin/feedback");
    renderAdminFeedback();
    const logs = await requestJson("/api/admin/audit-logs");
    document.getElementById("auditLogs").innerHTML = logs.length ? logs.map(log => `<div class="order-row"><div><strong>${log.action}</strong><span>${log.details || ""}</span></div></div>`).join("") : "<p>No audit logs yet.</p>";
  } catch (error) {
    document.getElementById("adminStats").innerHTML = `<article><h3>Admin locked</h3><p>${error.message}</p></article>`;
  }
}

document.getElementById("bootstrapAdmin").addEventListener("click", async () => {
  try {
    const data = await requestJson("/api/admin/bootstrap", { method: "POST" });
    document.getElementById("adminMessage").textContent = data.message;
    loadAdmin();
  } catch (error) {
    document.getElementById("adminMessage").textContent = error.message;
  }
});

document.getElementById("createInvite").addEventListener("click", async () => {
  try {
    const data = await requestJson("/api/admin/invites", { method: "POST", body: JSON.stringify({ expires_in_hours: 72 }) });
    document.getElementById("adminMessage").textContent = `Invite code: ${data.code}`;
  } catch (error) {
    document.getElementById("adminMessage").textContent = error.message;
  }
});

document.getElementById("couponForm").addEventListener("submit", async event => {
  event.preventDefault();
  const form = new FormData(event.target);
  const listFromField = name => String(form.get(name) || "")
    .split(",")
    .map(item => item.trim())
    .filter(Boolean);
  const numberOrNull = name => {
    const value = String(form.get(name) || "").trim();
    return value ? Number(value) : null;
  };
  try {
    await requestJson("/api/admin/coupons", {
      method: "POST",
      body: JSON.stringify({
        code: form.get("code"),
        label: form.get("label"),
        coupon_type: form.get("couponType"),
        value: Number(form.get("value")),
        enabled: form.get("enabled") === "on",
        minimum_purchase: Number(form.get("minimumPurchase") || 0),
        max_uses: numberOrNull("maxUses"),
        max_uses_per_user: numberOrNull("maxUsesPerUser"),
        applicable_products: listFromField("applicableProducts"),
        applicable_categories: listFromField("applicableCategories")
      })
    });
    document.getElementById("adminMessage").textContent = "Coupon created.";
    event.target.reset();
    event.target.querySelector('[name="enabled"]').checked = true;
    loadAdmin();
  } catch (error) {
    document.getElementById("adminMessage").textContent = error.message;
  }
});

document.getElementById("orderSearch")?.addEventListener("input", renderAdminOrders);
document.getElementById("orderStatusFilter")?.addEventListener("change", renderAdminOrders);

document.getElementById("adminOrders").addEventListener("click", async event => {
  const button = event.target.closest("[data-update-order]");
  if (!button) return;
  const orderId = button.dataset.updateOrder;
  const select = document.querySelector(`[data-status-for="${CSS.escape(orderId)}"]`);
  try {
    await requestJson(`/api/admin/orders/${encodeURIComponent(orderId)}/status`, {
      method: "PUT",
      body: JSON.stringify({ status: select.value, note: "Updated from admin panel." })
    });
    document.getElementById("adminMessage").textContent = `Order ${orderId} updated.`;
    loadAdmin();
  } catch (error) {
    document.getElementById("adminMessage").textContent = error.message;
  }
});

document.getElementById("adminFeedback")?.addEventListener("click", async event => {
  const button = event.target.closest("[data-remove-feedback]");
  if (!button) return;
  const feedbackId = button.dataset.removeFeedback;
  if (!window.confirm("Remove this feedback? This cannot be undone.")) return;
  try {
    await requestJson(`/api/admin/feedback/${encodeURIComponent(feedbackId)}`, { method: "DELETE" });
    adminFeedbackCache = adminFeedbackCache.filter(entry => String(entry.id) !== String(feedbackId));
    renderAdminFeedback();
    document.getElementById("adminMessage").textContent = "Feedback removed.";
  } catch (error) {
    document.getElementById("adminMessage").textContent = error.message;
  }
});

loadAdmin();

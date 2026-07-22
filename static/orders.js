function formatInr(value) {
  return `Rs. ${Number(value || 0).toLocaleString("en-IN")}`;
}

function formatDate(value) {
  return value ? new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "-";
}

function clean(text) {
  return String(text || "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
}

async function loadOrders() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("created")) {
    document.getElementById("orderNotice").textContent = `Order successfully created. Order ID: ${params.get("created")} | Status: Pending`;
  }
  const response = await fetch("/api/orders", { cache: "no-store" });
  if (response.status === 401) {
    window.location.href = "/login";
    return;
  }
  const orders = await response.json();
  document.getElementById("ordersList").innerHTML = orders.length ? orders.map(order => `
    <a class="order-row" href="/orders/${clean(order.orderId)}">
      <div><strong>${clean(order.orderId)}</strong><span>${formatDate(order.createdAt)}</span></div>
      <div><span>${clean(order.status)}</span><strong>${formatInr(order.finalTotal)}</strong></div>
    </a>
  `).join("") : `<p class="empty-cart">No orders yet.</p>`;
}

loadOrders();

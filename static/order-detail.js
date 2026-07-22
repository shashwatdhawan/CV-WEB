function formatInr(value) {
  return `Rs. ${Number(value || 0).toLocaleString("en-IN")}`;
}

function clean(text) {
  return String(text || "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
}

async function loadOrder() {
  const orderId = decodeURIComponent(window.location.pathname.split("/").pop());
  const response = await fetch(`/api/orders/${encodeURIComponent(orderId)}`, { cache: "no-store" });
  if (response.status === 401) {
    window.location.href = "/login";
    return;
  }
  const order = await response.json();
  document.getElementById("orderDetail").innerHTML = `
    <p class="eyebrow">Order</p>
    <h1>${clean(order.orderId)}</h1>
    <p class="profile-muted">Status: ${clean(order.status)}</p>
    <div class="future-grid">
      <article><h3>Discord</h3><p>${clean(order.discordUsername)}</p></article>
      <article><h3>Minecraft</h3><p>${clean(order.minecraftIgn || "Not linked")}</p></article>
      <article><h3>Coupon</h3><p>${clean(order.coupon || "None")}</p></article>
    </div>
    <div class="orders-list">
      ${order.items.map(item => `<div class="order-row"><div><strong>${clean(item.name)}</strong><span>Qty ${item.quantity}</span></div><strong>${formatInr(item.lineTotal)}</strong></div>`).join("")}
    </div>
    <div class="cart-total">
      <span>Subtotal</span><strong>${formatInr(order.subtotal)}</strong>
      <span>Discount</span><strong>${formatInr(order.discount)}</strong>
      <span>Total</span><strong>${formatInr(order.finalTotal)}</strong>
    </div>
    <a class="primary-action" href="/orders">Back to Orders</a>
  `;
}

loadOrder();

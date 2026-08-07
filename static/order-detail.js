function formatInr(value) {
  return `Rs. ${Number(value || 0).toLocaleString("en-IN")}`;
}

function clean(text) {
  return String(text || "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
}

async function refreshTicketStatus(orderId) {
  const message = document.getElementById("ticketActionMessage");
  const button = document.getElementById("ticketActionButton");
  const refreshButton = document.getElementById("refreshTicketButton");

  message.textContent = "Checking Discord ticket status...";
  refreshButton.disabled = true;

  try {
    const response = await fetch(`/api/orders/${encodeURIComponent(orderId)}/ticket-status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Could not refresh ticket status.");

    if (data.ticketChannelUrl) {
      button.disabled = false;
      button.textContent = "Open Discord Ticket";
      button.onclick = () => window.open(data.ticketChannelUrl, "_blank", "noopener,noreferrer");
      message.textContent = "Your private Discord ticket is ready.";
      return;
    }

    if (data.requiresJoin && data.joinUrl) {
      button.disabled = false;
      button.textContent = "Join Discord Server";
      button.onclick = () => window.open(data.joinUrl, "_blank", "noopener,noreferrer");
      message.textContent = "Join the Discord server, then click Refresh Ticket.";
      return;
    }

    button.disabled = true;
    button.textContent = "Ticket Pending";
    message.textContent = data.message || "Ticket is still being created. Please contact staff if it takes too long.";
  } catch (error) {
    button.disabled = true;
    button.textContent = "Ticket Pending";
    message.textContent = error.message;
  } finally {
    refreshButton.disabled = false;
  }
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
    <div class="ticket-action-card">
      <div>
        <p class="panel-label">Discord Ticket</p>
        <h2>Purchase Support Ticket</h2>
        <p class="profile-muted" id="ticketActionMessage">${order.ticketChannelUrl ? "Your private Discord ticket is ready." : "Ticket is still being created..."}</p>
      </div>
      <div class="ticket-action-buttons">
        <button class="primary-action" id="ticketActionButton" type="button" ${order.ticketChannelUrl ? "" : "disabled"}>${order.ticketChannelUrl ? "Open Discord Ticket" : "Ticket Pending"}</button>
        <button class="ghost-action" id="refreshTicketButton" type="button">Refresh Ticket</button>
      </div>
    </div>
    <a class="primary-action" href="/orders">Back to Orders</a>
  `;

  const button = document.getElementById("ticketActionButton");
  if (button && order.ticketChannelUrl) {
    button.addEventListener("click", () => window.open(order.ticketChannelUrl, "_blank", "noopener,noreferrer"));
  }
  document.getElementById("refreshTicketButton").addEventListener("click", () => refreshTicketStatus(order.orderId));
  if (!order.ticketChannelUrl) {
    refreshTicketStatus(order.orderId);
  }
}

loadOrder();

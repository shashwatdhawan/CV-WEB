function formatInr(value) {
  return `Rs. ${Number(value || 0).toLocaleString("en-IN")}`;
}

function clean(text) {
  return String(text || "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
}

function setText(id, value) {
  document.getElementById(id).textContent = value || "-";
}

async function loadOrderSuccess() {
  const parts = window.location.pathname.split("/");
  const orderId = decodeURIComponent(parts[2] || "");
  const response = await fetch(`/api/orders/${encodeURIComponent(orderId)}`, { cache: "no-store" });
  if (response.status === 401) {
    window.location.href = "/login";
    return;
  }
  const order = await response.json();
  if (!response.ok) throw new Error(order.detail || "Could not load order.");

  setText("successOrderId", order.orderId);
  setText("successDetailOrderId", order.orderId);
  setText("successStatus", order.status);
  setText("successMinecraft", order.minecraftIgn || "Not linked");
  setText("successDiscord", order.discordUsername);
  setText("successTotal", formatInr(order.finalTotal));

  document.getElementById("successItems").innerHTML = order.items.length ? order.items.map(item => `
    <div class="order-row">
      <div><strong>${clean(item.name)}</strong><span>Qty ${item.quantity}</span></div>
      <strong>${formatInr(item.lineTotal)}</strong>
    </div>
  `).join("") : `<p class="empty-cart">No items found.</p>`;

  const openTicketButton = document.getElementById("openTicketButton");
  const successMessage = document.getElementById("successMessage");
  if (order.ticketChannelUrl) {
    openTicketButton.disabled = false;
    openTicketButton.textContent = "Open Discord Ticket";
    openTicketButton.onclick = () => window.open(order.ticketChannelUrl, "_blank", "noopener,noreferrer");
    successMessage.textContent = "Your private Discord ticket is ready.";
  } else {
    await refreshTicketStatus(false);
  }
}

async function refreshTicketStatus(showChecking = true) {
  const parts = window.location.pathname.split("/");
  const orderId = decodeURIComponent(parts[2] || "");
  const openTicketButton = document.getElementById("openTicketButton");
  const successMessage = document.getElementById("successMessage");
  const refreshButton = document.getElementById("refreshOrderButton");

  if (showChecking) {
    successMessage.textContent = "Checking ticket status...";
  }
  refreshButton.disabled = true;

  try {
    const response = await fetch(`/api/orders/${encodeURIComponent(orderId)}/ticket-status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Could not refresh ticket status.");

    if (data.ticketChannelUrl) {
      openTicketButton.disabled = false;
      openTicketButton.textContent = "Open Discord Ticket";
      openTicketButton.onclick = () => window.open(data.ticketChannelUrl, "_blank", "noopener,noreferrer");
      successMessage.textContent = "Your private Discord ticket is ready.";
      return;
    }

    if (data.requiresJoin && data.joinUrl) {
      openTicketButton.disabled = false;
      openTicketButton.textContent = "Join Discord Server";
      openTicketButton.onclick = () => window.open(data.joinUrl, "_blank", "noopener,noreferrer");
      successMessage.textContent = "Join the Discord server first, then click Refresh Status.";
      return;
    }

    openTicketButton.disabled = true;
    openTicketButton.textContent = "Ticket is still being created...";
    successMessage.textContent = data.message || "Order created successfully. Our Discord ticket could not be created automatically. Please contact staff.";
  } finally {
    refreshButton.disabled = false;
  }
}

document.getElementById("refreshOrderButton").addEventListener("click", () => {
  refreshTicketStatus().catch(error => {
    document.getElementById("successMessage").textContent = error.message;
  });
});

loadOrderSuccess().catch(error => {
  document.querySelector(".order-success-shell").innerHTML = `<section class="profile-panel"><h1>Order unavailable</h1><p>${clean(error.message)}</p></section>`;
});

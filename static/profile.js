const loginButton = document.getElementById("loginButton");
const userButton = document.getElementById("userButton");
const userAvatar = document.getElementById("userAvatar");
const userName = document.getElementById("userName");
const userDropdown = document.getElementById("userDropdown");
const menuButton = document.getElementById("menuButton");
const navCenter = document.querySelector(".nav-center");
const minecraftForm = document.getElementById("minecraftForm");
const minecraftInput = document.getElementById("minecraftInput");
const minecraftMessage = document.getElementById("minecraftMessage");

function formatInr(value) {
  return `Rs. ${Number(value || 0).toLocaleString("en-IN")}`;
}

function formatDate(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function setText(id, value) {
  document.getElementById(id).textContent = value || "-";
}

function renderProfile(profile) {
  const discord = profile.discord;
  const minecraft = profile.minecraft;
  const stats = profile.stats;
  const dates = profile.dates;

  userAvatar.src = discord.avatar;
  userName.textContent = discord.display_name;
  document.getElementById("profileAvatar").src = discord.avatar;
  setText("profileDisplayName", discord.display_name);
  setText("profileUsername", `@${discord.username}`);
  setText("detailDisplayName", discord.display_name);
  setText("detailDiscordUsername", discord.username);
  setText("detailDiscordId", discord.id);
  setText("detailJoined", formatDate(dates.joined));
  setText("detailLastLogin", formatDate(dates.last_login));
  setText("profileOrders", stats.orders);
  setText("profilePurchases", stats.purchases);
  setText("profileSpent", formatInr(stats.money_spent_inr));

  if (minecraft.linked) {
    document.getElementById("minecraftHead").src = minecraft.head_url || minecraft.avatar_url;
    setText("minecraftIgn", minecraft.ign);
    setText("minecraftUuid", minecraft.uuid);
    minecraftInput.value = minecraft.ign;
    minecraftForm.querySelector("button").textContent = "Change Account";
  }
}

async function loadProfile() {
  const response = await fetch("/api/profile", { cache: "no-store" });
  if (response.status === 401) {
    window.location.href = "/login";
    return;
  }
  if (!response.ok) throw new Error("Could not load profile.");
  renderProfile(await response.json());
}

if (minecraftForm) {
  minecraftForm.addEventListener("submit", async event => {
    event.preventDefault();
    minecraftMessage.textContent = "Checking Minecraft account...";
    minecraftMessage.className = "";
    try {
      const response = await fetch("/api/profile/minecraft", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ign: minecraftInput.value.trim() })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not link Minecraft account.");
      renderProfile(data);
      minecraftMessage.textContent = "Minecraft account linked.";
      minecraftMessage.className = "success";
    } catch (error) {
      minecraftMessage.textContent = error.message;
      minecraftMessage.className = "error";
    }
  });
}

if (menuButton && navCenter) {
  menuButton.addEventListener("click", () => {
    const isOpen = navCenter.classList.toggle("open");
    menuButton.classList.toggle("open", isOpen);
    menuButton.setAttribute("aria-expanded", String(isOpen));
  });
}

if (userButton && userDropdown) {
  userButton.addEventListener("click", event => {
    event.stopPropagation();
    const isOpen = userDropdown.hidden;
    userDropdown.hidden = !isOpen;
    userButton.classList.toggle("open", isOpen);
    userButton.setAttribute("aria-expanded", String(isOpen));
  });

  document.addEventListener("click", event => {
    if (!event.target.closest("#authMenu")) {
      userDropdown.hidden = true;
      userButton.classList.remove("open");
      userButton.setAttribute("aria-expanded", "false");
    }
  });

  userDropdown.querySelectorAll("[data-account-action]").forEach(link => {
    link.addEventListener("click", event => {
      event.preventDefault();
      alert("This account section will be connected later.");
    });
  });
}

loadProfile().catch(error => {
  document.querySelector(".profile-shell").innerHTML = `<section class="profile-panel"><h1>Profile unavailable</h1><p>${error.message}</p></section>`;
});

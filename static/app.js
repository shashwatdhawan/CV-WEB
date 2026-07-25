const grid = document.getElementById("productGrid");
const title = document.getElementById("categoryTitle");
const count = document.getElementById("itemCount");
const backdrop = document.getElementById("modalBackdrop");
const policyModal = document.getElementById("policyModal");
const policyTitle = document.getElementById("policyTitle");
const policyUpdated = document.getElementById("policyUpdated");
const policyContent = document.getElementById("policyContent");
const productModal = document.getElementById("productModal");
const cartModal = document.getElementById("cartModal");
const cartButton = document.getElementById("cartButton");
const menuButton = document.getElementById("menuButton");
const navCenter = document.querySelector(".nav-center");
const continueShoppingButton = document.getElementById("continueShoppingButton");
const copyIpButton = document.getElementById("copyIpButton");
const copyIpMessage = document.getElementById("copyIpMessage");
const serverIp = document.getElementById("serverIp");
const loginButton = document.getElementById("loginButton");
const userButton = document.getElementById("userButton");
const userAvatar = document.getElementById("userAvatar");
const userName = document.getElementById("userName");
const userDropdown = document.getElementById("userDropdown");
const adminNav = document.getElementById("adminNav");

let activeCategory = "ranks";
let currentProduct = null;
let storeData = { discordLink: "https://discord.gg/jWDH4GYuns", categories: {}, products: [] };
let cartState = { items: [], subtotal: 0, discount: 0, finalTotal: 0, totalItems: 0 };
let appliedCouponCode = "";

const productBadges = {
  warrior: "New",
  champion: "Popular",
  radiant: "Best Seller",
  daddy: "Popular",
  custom: "Limited",
  "coins-1000": "Popular",
  "coins-2000": "Best Seller",
  "cloud-key": "Popular",
  "matrix-key": "New",
  "amethyst-key": "Sale",
  "special-edition-key": "Limited"
};

function badgeClass(label) {
  return `badge-${label.toLowerCase().replace(/\s+/g, "-")}`;
}

function formatInr(value) {
  return `Rs. ${Number(value || 0).toLocaleString("en-IN")}`;
}

function clean(text) {
  return String(text || "").replace(/[&<>"']/g, char => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  }[char]));
}

function productById(id) {
  return storeData.products.find(product => product.id === id);
}

function art(product) {
  return `<div class="art">${artInner(product)}</div>`;
}

function artInner(product) {
  if (product.artType === "image") {
    return `<img class="product-image ${clean(product.theme)}" src="${clean(product.image)}" alt="${clean(product.name)}">`;
  }
  return `<div class="rank-badge ${clean(product.theme)}" data-text="${clean(product.name.slice(0, 3).toUpperCase())}"></div>`;
}

function openModal(modal) {
  backdrop.hidden = false;
  modal.hidden = false;
}

function closeModals() {
  backdrop.hidden = true;
  productModal.hidden = true;
  cartModal.hidden = true;
  if (policyModal) policyModal.hidden = true;
}

function updateCartButton() {
  cartButton.querySelector("span:last-child").textContent = cartState.totalItems ? `Cart (${cartState.totalItems})` : "Cart";
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (response.status === 401) {
    alert("Please login with Discord before using the cart.");
    window.location.href = "/login";
    throw new Error("Login required.");
  }
  if (!response.ok) {
    throw new Error(data.detail || "Request failed.");
  }
  return data;
}

async function loadStoreData() {
  const [categories, products] = await Promise.all([
    requestJson("/api/categories"),
    requestJson("/api/products")
  ]);
  storeData.categories = Object.fromEntries(categories.map(category => [category.slug, category.name]));
  storeData.products = products;
  if (!storeData.categories[activeCategory]) {
    activeCategory = categories[0]?.slug || "ranks";
  }
  renderCategoryButtons(categories);
  renderProducts();
}

function renderCategoryButtons(categories) {
  const sidebar = document.querySelector(".sidebar");
  sidebar.innerHTML = categories.map(category => `
    <button class="feature-card ${category.slug === activeCategory ? "active" : ""}" data-category="${clean(category.slug)}" type="button">
      <span>${clean(category.name)}</span>
    </button>
  `).join("");

  sidebar.querySelectorAll(".feature-card").forEach(button => {
    button.addEventListener("click", () => {
      activeCategory = button.dataset.category;
      document.querySelectorAll(".feature-card").forEach(item => item.classList.toggle("active", item === button));
      renderProducts();
    });
  });
}

function renderProducts() {
  const items = storeData.products.filter(product => product.category === activeCategory);
  title.textContent = storeData.categories[activeCategory] || "Store";
  count.textContent = `${items.length} items`;
  grid.innerHTML = items.map(product => `
    <article class="product-card" data-id="${clean(product.id)}">
      ${productBadges[product.id] ? `<span class="product-badge ${badgeClass(productBadges[product.id])}">${clean(productBadges[product.id])}</span>` : ""}
      ${art(product)}
      <div class="product-info">
        <h3>${clean(product.name)}</h3>
        <p>${clean(product.subtitle || product.description)}</p>
        <div class="price-row">
          <strong>${formatInr(product.priceInr)}</strong>
          <span>$${clean(product.priceUsd)}</span>
        </div>
      </div>
    </article>
  `).join("");
}

async function loadCart() {
  try {
    cartState = await requestJson("/api/cart");
    updateCartButton();
    renderCart();
  } catch {
    cartState = { items: [], subtotal: 0, discount: 0, finalTotal: 0, totalItems: 0 };
    updateCartButton();
  }
}

async function addToCart(product, quantity = 1) {
  cartState = await requestJson("/api/cart/add", {
    method: "POST",
    body: JSON.stringify({ product_id: product.id, quantity })
  });
  updateCartButton();
  renderCart();
}

function showProduct(product) {
  currentProduct = product;
  document.getElementById("modalArt").innerHTML = artInner(product);
  document.getElementById("modalCategory").textContent = storeData.categories[product.category] || product.category;
  document.getElementById("modalTitle").textContent = product.name;
  document.getElementById("modalDescription").textContent = product.subtitle || product.description;
  document.getElementById("modalFeatures").innerHTML = product.features.map(feature => `<li>${clean(feature)}</li>`).join("");
  document.getElementById("modalPrice").textContent = formatInr(product.priceInr);
  document.getElementById("modalUsd").textContent = `$${product.priceUsd}`;
  openModal(productModal);
}

function renderCart() {
  const cartItems = document.getElementById("cartItems");

  cartItems.innerHTML = cartState.items.length ? cartState.items.map(item => {
    const product = item.product;
    return `
      <div class="cart-line">
        <img class="cart-line-image" src="${clean(product.image)}" alt="${clean(product.name)}">
        <div class="cart-line-info">
          <strong>${clean(product.name)}</strong>
          <span>${formatInr(product.priceInr)} each</span>
        </div>
        <div class="cart-line-actions">
          <button type="button" data-cart-minus="${clean(product.id)}">-</button>
          <span>${item.quantity}</span>
          <button type="button" data-cart-plus="${clean(product.id)}">+</button>
          <button type="button" data-cart-remove="${clean(product.id)}">Remove</button>
        </div>
      </div>
    `;
  }).join("") : `<p class="empty-cart">No items added yet.</p>`;

  document.getElementById("couponMessage").textContent = appliedCouponCode ? `Coupon ready: ${appliedCouponCode}` : "";
  document.getElementById("cartSubtotal").textContent = formatInr(cartState.subtotal);
  document.getElementById("cartDiscount").textContent = formatInr(cartState.discount);
  document.getElementById("cartTotal").textContent = formatInr(cartState.finalTotal);
  document.getElementById("checkoutButton").disabled = cartState.items.length === 0;
}

async function checkout() {
  if (!cartState.items.length) return;
  const button = document.getElementById("checkoutButton");
  button.disabled = true;
  button.textContent = "Creating Order...";
  try {
    const result = await requestJson("/api/checkout", {
      method: "POST",
      body: JSON.stringify({ coupon_code: appliedCouponCode || null })
    });
    window.location.href = `/orders/${encodeURIComponent(result.order.orderId)}/success`;
  } catch (error) {
    if (error.message.includes("Minecraft IGN")) {
      alert("Please link your Minecraft IGN in your profile before checkout.");
      window.location.href = "/profile";
      return;
    }
    alert(error.message);
    button.disabled = false;
    button.textContent = "Proceed to Checkout";
  }
}

async function loadCurrentUser() {
  if (!loginButton || !userButton || !userAvatar || !userName || !userDropdown) return;
  try {
    const response = await fetch("/api/user", { cache: "no-store" });
    const data = response.ok ? await response.json() : { authenticated: false };
    if (!data.authenticated || !data.user) {
      loginButton.hidden = false;
      userButton.hidden = true;
      userDropdown.hidden = true;
      if (adminNav) adminNav.hidden = true;
      cartState = { items: [], subtotal: 0, discount: 0, finalTotal: 0, totalItems: 0 };
      updateCartButton();
      return;
    }

    loginButton.hidden = true;
    userButton.hidden = false;
    if (adminNav) adminNav.hidden = !data.user.is_admin;
    userAvatar.src = data.user.avatar;
    userName.textContent = data.user.username || data.user.discord_username || "Discord User";
    await loadCart();
  } catch {
    loginButton.hidden = false;
    userButton.hidden = true;
    userDropdown.hidden = true;
    if (adminNav) adminNav.hidden = true;
  }
}

const tabPanels = document.querySelectorAll("[data-tab-panel]");
const tabLinks = document.querySelectorAll("[data-tab]");
const validTabs = ["info", "store", "voting", "feedback"];

function showTab(tabName, options = {}) {
  const target = validTabs.includes(tabName) ? tabName : "info";
  tabPanels.forEach(panel => {
    panel.classList.toggle("active", panel.dataset.tabPanel === target);
  });
  tabLinks.forEach(link => {
    link.classList.toggle("active", link.dataset.tab === target);
  });
  if (!options.skipScroll) {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

tabLinks.forEach(link => {
  link.addEventListener("click", event => {
    event.preventDefault();
    const target = link.dataset.tab;
    if (window.location.hash !== `#${target}`) {
      history.pushState(null, "", `#${target}`);
    }
    showTab(target);
  });
});

window.addEventListener("popstate", () => {
  showTab(window.location.hash.replace("#", ""), { skipScroll: true });
});

showTab(window.location.hash.replace("#", ""), { skipScroll: true });

if (menuButton && navCenter) {
  menuButton.addEventListener("click", () => {
    const isOpen = navCenter.classList.toggle("open");
    menuButton.classList.toggle("open", isOpen);
    menuButton.setAttribute("aria-expanded", String(isOpen));
  });

  navCenter.querySelectorAll("a").forEach(link => {
    link.addEventListener("click", () => {
      navCenter.classList.remove("open");
      menuButton.classList.remove("open");
      menuButton.setAttribute("aria-expanded", "false");
    });
  });
}

grid.addEventListener("click", event => {
  const card = event.target.closest(".product-card");
  if (!card) return;
  const product = productById(card.dataset.id);
  if (product) showProduct(product);
});

document.getElementById("addToCartButton").addEventListener("click", async () => {
  if (!currentProduct) return;
  await addToCart(currentProduct);
  closeModals();
  openModal(cartModal);
});

document.getElementById("buyNowButton").addEventListener("click", async () => {
  if (!currentProduct) return;
  await addToCart(currentProduct);
  closeModals();
  openModal(cartModal);
});

cartButton.addEventListener("click", async () => {
  await loadCart();
  openModal(cartModal);
});

document.getElementById("applyCouponButton").addEventListener("click", async () => {
  const input = document.getElementById("couponInput");
  const code = input.value.trim();
  if (!code) {
    appliedCouponCode = "";
    document.getElementById("couponMessage").textContent = "";
    return;
  }
  try {
    const result = await requestJson("/api/coupons/validate", {
      method: "POST",
      body: JSON.stringify({ code })
    });
    if (result.adminRedeemed) {
      document.getElementById("couponMessage").innerHTML = `${clean(result.message)} <a href="/admin">Open Admin</a>`;
      if (adminNav) adminNav.hidden = false;
      input.value = "";
      return;
    }
    appliedCouponCode = result.code;
    cartState.discount = result.discount;
    cartState.finalTotal = result.finalTotal;
    document.getElementById("couponMessage").textContent = `Coupon applied: ${result.code}`;
    renderCart();
  } catch (error) {
    appliedCouponCode = "";
    document.getElementById("couponMessage").textContent = error.message;
  }
});

document.getElementById("checkoutButton").addEventListener("click", checkout);
continueShoppingButton.addEventListener("click", closeModals);

if (copyIpButton && serverIp) {
  copyIpButton.addEventListener("click", async () => {
    const value = serverIp.textContent.trim();
    try {
      await navigator.clipboard.writeText(value);
      copyIpMessage.textContent = "Server IP copied.";
    } catch {
      window.prompt("Copy server IP:", value);
      copyIpMessage.textContent = "Copy the IP from the box.";
    }
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
      alert("This account page will be connected later.");
      userDropdown.hidden = true;
      userButton.classList.remove("open");
      userButton.setAttribute("aria-expanded", "false");
    });
  });
}

document.getElementById("cartItems").addEventListener("click", async event => {
  const minus = event.target.dataset.cartMinus;
  const plus = event.target.dataset.cartPlus;
  const remove = event.target.dataset.cartRemove;
  const item = cartState.items.find(entry => entry.productId === (minus || plus || remove));
  if (!item) return;

  if (minus) {
    cartState = await requestJson("/api/cart/update", {
      method: "PUT",
      body: JSON.stringify({ product_id: minus, quantity: item.quantity - 1 })
    });
  }
  if (plus) {
    cartState = await requestJson("/api/cart/update", {
      method: "PUT",
      body: JSON.stringify({ product_id: plus, quantity: item.quantity + 1 })
    });
  }
  if (remove) {
    cartState = await requestJson("/api/cart/remove", {
      method: "DELETE",
      body: JSON.stringify({ product_id: remove, quantity: 0 })
    });
  }
  updateCartButton();
  renderCart();
});

document.querySelectorAll("[data-close]").forEach(button => button.addEventListener("click", closeModals));
backdrop.addEventListener("click", closeModals);

const policyCopy = {
  terms: {
    title: "Cloudverse Terms & Conditions",
    updated: "Last updated on 23 July 2026.",
    body: `
      <p>These terms explain how purchases and account features work on the Cloudverse Store. By creating an order, you confirm that the Minecraft username and Discord account connected to your profile are correct.</p>
      <p>All products are digital Minecraft server items such as ranks, crate keys, coins and perks. Delivery is completed by Cloudverse staff through Discord tickets until automatic delivery is added later.</p>
      <p>Do not share passwords, payment information or private account details inside tickets. Staff will only ask for information needed to verify and complete your order.</p>
    `
  },
  privacy: {
    title: "Cloudverse Privacy Policy",
    updated: "Last updated on 23 July 2026.",
    body: `
      <p>Cloudverse uses Discord login to identify your account, show your avatar and connect orders to the correct Discord user. Your Discord client secret, bot token and website secrets are never shown in the browser.</p>
      <p>We store basic order details, linked Minecraft username, Minecraft UUID, coupons used and ticket status so staff can provide support and complete purchases.</p>
      <p>You should keep your Discord account and Minecraft account secure. Contact staff through the official Cloudverse Discord if you need help with an order.</p>
    `
  },
  refund: {
    title: "Cloudverse Refund Policy",
    updated: "Last updated on 23 July 2026.",
    body: `
      <p>Digital purchases are reviewed by staff before delivery. If there is a mistake with an order, contact staff in your private Discord ticket as soon as possible.</p>
      <p>Refunds may be reviewed by staff depending on the situation. Completed digital deliveries may not always be refundable.</p>
      <p>Chargebacks, fake payments or abuse can lead to cancellation of purchases and restrictions from Cloudverse services.</p>
    `
  },
  data: {
    title: "Cloudverse Data Usage Policy",
    updated: "How and why we use your data.",
    body: `
      <div class="policy-data-row"><strong>Account Data</strong><span>Discord ID, username, display name and avatar are used for login and support.</span></div>
      <div class="policy-data-row"><strong>Minecraft Data</strong><span>IGN and UUID are used to connect purchases to the correct player.</span></div>
      <div class="policy-data-row"><strong>Order Data</strong><span>Products, coupons, totals and ticket links are used to process purchases.</span></div>
      <div class="policy-data-row"><strong>Support Data</strong><span>Ticket links and order status help staff complete or review purchases.</span></div>
    `
  }
};

function openPolicy(policyKey) {
  if (!policyModal || !policyTitle || !policyContent) return;
  const policy = policyCopy[policyKey] || policyCopy.terms;
  policyTitle.textContent = policy.title;
  policyUpdated.textContent = policy.updated;
  policyContent.innerHTML = policy.body;
  closeModals();
  policyModal.hidden = false;
  backdrop.hidden = false;
}

document.querySelectorAll("[data-policy]").forEach(link => {
  link.addEventListener("click", event => {
    event.preventDefault();
    openPolicy(link.dataset.policy);
  });
});

[document.getElementById("policyCloseButton"), document.getElementById("policyDismissButton")].forEach(button => {
  if (button) button.addEventListener("click", closeModals);
});

loadStoreData().then(loadCurrentUser).catch(error => {
  grid.innerHTML = `<p class="empty-cart">${clean(error.message)}</p>`;
});

setInterval(loadCurrentUser, 60000);

function renderVotingLinks() {
  const votingLinksGrid = document.getElementById("votingLinksGrid");
  if (!votingLinksGrid || typeof votingLinks === "undefined") return;
  votingLinksGrid.innerHTML = votingLinks.map((link, index) => `
    <a class="voting-link-item" href="${clean(link.url)}" target="_blank" rel="noreferrer">
      <span class="voting-link-num">${index + 1}</span>
      <span>${clean(link.name)}</span>
    </a>
  `).join("");
}

renderVotingLinks();



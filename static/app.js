const config = window.CLOUDVERSE_STORE;
const grid = document.getElementById("productGrid");
const title = document.getElementById("categoryTitle");
const count = document.getElementById("itemCount");
const backdrop = document.getElementById("modalBackdrop");
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
const cloudCursor = document.createElement("div");

let activeCategory = "ranks";
let currentProduct = null;
let couponCode = localStorage.getItem("cloudverseCoupon") || "";
let cart = JSON.parse(localStorage.getItem("cloudverseCart") || "[]");
let coupons = [];

const productBadges = {
  warrior: "New",
  aurora: "Popular",
  radiant: "Best Seller",
  daddy: "Popular",
  custom: "Limited",
  "coins-1000": "Popular",
  "coins-5000": "Best Seller",
  "coins-25000": "Limited",
  "cloud-key": "Popular",
  "matrix-key": "New",
  "amethyst-key": "Sale",
  "special-edition-key": "Limited"
};

function badgeClass(label) {
  return `badge-${label.toLowerCase().replace(/\s+/g, "-")}`;
}

function formatInr(value) {
  return `Rs. ${Number(value).toLocaleString("en-IN")}`;
}

function clean(text) {
  return String(text).replace(/[&<>"']/g, char => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  }[char]));
}

function art(product) {
  return `<div class="art">${artInner(product)}</div>`;
}

function artInner(product) {
  if (product.artType === "image") {
    return `<img class="product-image ${product.theme}" src="${product.image}" alt="${clean(product.name)}">`;
  }
  return `<div class="rank-badge ${product.theme}" data-text="${clean(product.name.slice(0, 3).toUpperCase())}"></div>`;
}

function saveCart() {
  localStorage.setItem("cloudverseCart", JSON.stringify(cart));
  cartButton.querySelector("span:last-child").textContent = cart.length ? `Cart (${cart.reduce((sum, item) => sum + item.qty, 0)})` : "Cart";
}

async function loadCoupons() {
  try {
    const response = await fetch("/static/coupons.json", { cache: "no-store" });
    coupons = response.ok ? await response.json() : [];
  } catch {
    coupons = [];
  }
}

function productById(id) {
  return config.products.find(product => product.id === id);
}

function cartSubtotal() {
  return cart.reduce((sum, item) => {
    const product = productById(item.id);
    return product ? sum + product.priceInr * item.qty : sum;
  }, 0);
}

function selectedCoupon() {
  const code = couponCode.trim().toUpperCase();
  return coupons.find(coupon => coupon.code.toUpperCase() === code);
}

function discountAmount(subtotal) {
  const coupon = selectedCoupon();
  if (!coupon || subtotal <= 0) return 0;
  if (coupon.type === "percent") return Math.floor(subtotal * Number(coupon.value) / 100);
  return Math.min(subtotal, Number(coupon.value));
}

function renderProducts() {
  const items = config.products.filter(product => product.category === activeCategory);
  title.textContent = config.categories[activeCategory];
  count.textContent = `${items.length} items`;
  grid.innerHTML = items.map(product => `
    <article class="product-card" data-id="${product.id}">
      ${productBadges[product.id] ? `<span class="product-badge ${badgeClass(productBadges[product.id])}">${clean(productBadges[product.id])}</span>` : ""}
      ${art(product)}
      <div class="product-info">
        <h3>${clean(product.name)}</h3>
        <p>${clean(product.subtitle)}</p>
        <div class="price-row">
          <strong>${formatInr(product.priceInr)}</strong>
          <span>$${clean(product.priceUsd)}</span>
        </div>
      </div>
    </article>
  `).join("");
}

function openModal(modal) {
  backdrop.hidden = false;
  modal.hidden = false;
}

function closeModals() {
  backdrop.hidden = true;
  productModal.hidden = true;
  cartModal.hidden = true;
}

function addToCart(product, qty = 1) {
  const existing = cart.find(item => item.id === product.id);
  if (existing) existing.qty += qty;
  else cart.push({ id: product.id, qty });
  saveCart();
  renderCart();
}

function orderSummary(items = cart) {
  const lines = ["Cloudverse Store Order", ""];
  let subtotal = 0;
  items.forEach(item => {
    const product = productById(item.id);
    if (!product) return;
    const lineTotal = product.priceInr * item.qty;
    subtotal += lineTotal;
    lines.push(`${item.qty}x ${product.name} - ${formatInr(lineTotal)}`);
  });
  const discount = items === cart ? discountAmount(subtotal) : 0;
  if (discount > 0) lines.push(`Coupon ${couponCode.toUpperCase()} - ${formatInr(discount)} off`);
  lines.push("");
  lines.push(`Total: ${formatInr(subtotal - discount)}`);
  return lines.join("\n");
}

function checkout(items = cart) {
  if (!items.length) return;
  const summary = orderSummary(items);
  window.open(config.discordLink, "_blank", "noreferrer");
  window.prompt("Copy this order summary and send it in your Cloudverse Discord ticket:", summary);
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
      return;
    }

    loginButton.hidden = true;
    userButton.hidden = false;
    userAvatar.src = data.user.avatar;
    userName.textContent = data.user.username || data.user.discord_username || "Discord User";
  } catch {
    loginButton.hidden = false;
    userButton.hidden = true;
    userDropdown.hidden = true;
  }
}

function showProduct(product) {
  currentProduct = product;
  document.getElementById("modalArt").innerHTML = artInner(product);
  document.getElementById("modalCategory").textContent = config.categories[product.category];
  document.getElementById("modalTitle").textContent = product.name;
  document.getElementById("modalDescription").textContent = product.subtitle;
  document.getElementById("modalFeatures").innerHTML = product.features.map(feature => `<li>${clean(feature)}</li>`).join("");
  document.getElementById("modalPrice").textContent = formatInr(product.priceInr);
  document.getElementById("modalUsd").textContent = `$${product.priceUsd}`;
  openModal(productModal);
}

function renderCart() {
  const cartItems = document.getElementById("cartItems");
  const subtotal = cartSubtotal();
  const discount = discountAmount(subtotal);
  const coupon = selectedCoupon();

  cartItems.innerHTML = cart.length ? cart.map(item => {
    const product = productById(item.id);
    if (!product) return "";
    return `
      <div class="cart-line">
        <img class="cart-line-image" src="${product.image}" alt="${clean(product.name)}">
        <div class="cart-line-info">
          <strong>${clean(product.name)}</strong>
          <span>${formatInr(product.priceInr)} each</span>
        </div>
        <div class="cart-line-actions">
          <button type="button" data-cart-minus="${item.id}">-</button>
          <span>${item.qty}</span>
          <button type="button" data-cart-plus="${item.id}">+</button>
          <button type="button" data-cart-remove="${item.id}">Remove</button>
        </div>
      </div>
    `;
  }).join("") : `<p class="empty-cart">No items added yet.</p>`;

  document.getElementById("couponInput").value = couponCode;
  document.getElementById("couponMessage").textContent = couponCode
    ? (coupon ? `Coupon applied: ${coupon.label}` : "Invalid coupon code")
    : "";
  document.getElementById("cartSubtotal").textContent = formatInr(subtotal);
  document.getElementById("cartDiscount").textContent = formatInr(discount);
  document.getElementById("cartTotal").textContent = formatInr(subtotal - discount);
  document.getElementById("checkoutButton").disabled = cart.length === 0;
}

document.querySelectorAll(".feature-card").forEach(button => {
  button.addEventListener("click", () => {
    activeCategory = button.dataset.category;
    document.querySelectorAll(".feature-card").forEach(item => item.classList.toggle("active", item === button));
    renderProducts();
  });
});

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

document.getElementById("addToCartButton").addEventListener("click", () => {
  if (!currentProduct) return;
  addToCart(currentProduct);
  closeModals();
  openModal(cartModal);
});

document.getElementById("buyNowButton").addEventListener("click", () => {
  if (!currentProduct) return;
  addToCart(currentProduct);
  closeModals();
  openModal(cartModal);
});

cartButton.addEventListener("click", () => {
  renderCart();
  openModal(cartModal);
});

document.getElementById("applyCouponButton").addEventListener("click", () => {
  couponCode = document.getElementById("couponInput").value.trim();
  localStorage.setItem("cloudverseCoupon", couponCode);
  renderCart();
});

document.getElementById("checkoutButton").addEventListener("click", () => checkout(cart));
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

document.getElementById("cartItems").addEventListener("click", event => {
  const minus = event.target.dataset.cartMinus;
  const plus = event.target.dataset.cartPlus;
  const remove = event.target.dataset.cartRemove;
  if (minus) {
    const item = cart.find(entry => entry.id === minus);
    if (item) item.qty -= 1;
    cart = cart.filter(entry => entry.qty > 0);
  }
  if (plus) {
    const item = cart.find(entry => entry.id === plus);
    if (item) item.qty += 1;
  }
  if (remove) cart = cart.filter(entry => entry.id !== remove);
  saveCart();
  renderCart();
});

const discordUrl = config.discordLink || "https://discord.gg/8ZucR4fXkk";
document.getElementById("discordFooter").href = discordUrl;
document.getElementById("discordNav").href = discordUrl;

document.querySelectorAll("[data-close]").forEach(button => button.addEventListener("click", closeModals));
backdrop.addEventListener("click", closeModals);

document.querySelectorAll("[data-policy]").forEach(link => {
  link.addEventListener("click", event => {
    event.preventDefault();
    alert(`${link.dataset.policy}\n\nEdit this link or page later in index.html.`);
  });
});

loadCoupons().then(() => {
  saveCart();
  renderProducts();
  loadCurrentUser();
});

setInterval(loadCurrentUser, 60000);

if (window.matchMedia("(pointer: fine)").matches) {
  cloudCursor.className = "cloud-cursor";
  cloudCursor.setAttribute("aria-hidden", "true");
  document.body.appendChild(cloudCursor);
  window.addEventListener("mousemove", event => {
    cloudCursor.style.transform = `translate3d(${event.clientX - 8}px, ${event.clientY - 8}px, 0)`;
  });
  window.addEventListener("mousedown", () => cloudCursor.classList.add("is-clicking"));
  window.addEventListener("mouseup", () => cloudCursor.classList.remove("is-clicking"));
  window.addEventListener("mouseleave", () => { cloudCursor.style.opacity = "0"; });
  window.addEventListener("mouseenter", () => { cloudCursor.style.opacity = "1"; });
}

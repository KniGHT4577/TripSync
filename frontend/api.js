const BASE_URL = 'https://tripsync-api.onrender.com';

// ─── Auth Helpers ─────────────────────────────────────────────
function getUserId() { return localStorage.getItem('user_id'); }
function setUserId(id) { localStorage.setItem('user_id', id); }
function setUsername(name) { localStorage.setItem('user_name', name); }
function getUsername() { return localStorage.getItem('user_name') || 'User'; }
function setVerified(val) { localStorage.setItem('is_verified', val ? '1' : '0'); }
function isVerified() { return localStorage.getItem('is_verified') === '1'; }
function setVerificationStatus(s) { localStorage.setItem('verification_status', s); }
function getVerificationStatus() { return localStorage.getItem('verification_status') || 'unverified'; }

function getUserInitials() {
    const name = getUsername();
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

function logout() {
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_name');
    localStorage.removeItem('is_verified');
    localStorage.removeItem('verification_status');
    window.location.href = 'login.html';
}

function checkAuth(redirectIfNotAuth = true) {
    const id = getUserId();
    if (!id && redirectIfNotAuth) window.location.href = 'login.html';
    return id;
}

// ─── Toast System ─────────────────────────────────────────────
function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }
    const icons = { success: 'fa-circle-check', error: 'fa-circle-exclamation', info: 'fa-circle-info' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<i class="fa-solid ${icons[type] || icons.success}"></i> ${message}`;
    container.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 350);
    }, 3500);
}

// ─── API Call ─────────────────────────────────────────────────
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = { method, headers: { 'Content-Type': 'application/json' } };
    if (data) options.body = JSON.stringify(data);
    try {
        const response = await fetch(`${BASE_URL}${endpoint}`, options);
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || result.message || 'Something went wrong');
        return result;
    } catch (e) {
        console.error('[API Error]', e);
        throw e;
    }
}

// ─── Wishlist Helpers ─────────────────────────────────────────
async function getWishlist() {
    const userId = getUserId();
    if (!userId) return new Set();
    try {
        const data = await apiCall(`/wishlist/${userId}`);
        return new Set(data.wishlist || []);
    } catch { return new Set(); }
}

async function toggleWishlist(tripId, btn) {
    const userId = getUserId();
    if (!userId) return;
    const isWishlisted = btn.classList.contains('wishlisted');
    try {
        if (isWishlisted) {
            await apiCall(`/wishlist/${userId}/${tripId}`, 'DELETE');
            btn.classList.remove('wishlisted');
            btn.innerHTML = '<i class="fa-regular fa-heart"></i>';
            showToast('Removed from wishlist', 'info');
        } else {
            await apiCall('/wishlist', 'POST', { user_id: userId, trip_id: tripId });
            btn.classList.add('wishlisted');
            btn.innerHTML = '<i class="fa-solid fa-heart"></i>';
            showToast('Added to wishlist! ❤️');
        }
    } catch (e) { showToast(e.message, 'error'); }
}

// ─── Shared Image & Category Utilities ───────────────────────
const UNSPLASH_MAP = {
    beach: '1507525428034-b723cf961d3e',
    mountain: '1464822759023-fed622ff2c3b',
    city: '1477959858617-67f85cf4f1df',
    japan: '1540959733332-eab4deabeeaf',
    paris: '1499856871958-5b9627545d1a',
    bali: '1537996194471-e657df975ab4',
    goa: '1506905925346-21bda4d32df4',
    himalaya: '1464822759023-fed622ff2c3b',
    forest: '1448375240586-882707db888b',
    desert: '1509316785289-025f5b846b35',
    default: '1488085061851-d521b67a3e3c'
};

function getImageUrl(location) {
    if (!location) return `https://images.unsplash.com/photo-${UNSPLASH_MAP.default}?w=700&h=450&fit=crop&q=80`;
    const key = Object.keys(UNSPLASH_MAP).find(k => location.toLowerCase().includes(k));
    return `https://images.unsplash.com/photo-${UNSPLASH_MAP[key] || UNSPLASH_MAP.default}?w=700&h=450&fit=crop&q=80`;
}

function getCategoryColor(cat) {
    const colors = { adventure: '#f59e0b', beach: '#06b6d4', culture: '#a78bfa', nature: '#10b981', other: '#94a3b8' };
    return colors[cat] || colors.other;
}

function getCategoryIcon(cat) {
    const icons = { adventure: 'fa-mountain', beach: 'fa-umbrella-beach', culture: 'fa-landmark', nature: 'fa-leaf', other: 'fa-globe' };
    return icons[cat] || icons.other;
}

// ─── Trip Duration Helper ─────────────────────────────────────
function getTripDuration(startDate, endDate) {
    if (!startDate || !endDate) return null;
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diff = Math.round((end - start) / (1000 * 60 * 60 * 24));
    if (diff <= 0) return null;
    return diff === 1 ? '1 day' : `${diff} days`;
}

// ─── Share Trip Helper ────────────────────────────────────────
async function shareTrip(title, location) {
    const text = `🌍 Check out this trip on TripSync: "${title}" in ${location}!`;
    const url = window.location.origin + '/find-trips.html';
    if (navigator.share) {
        try { await navigator.share({ title: `TripSync – ${title}`, text, url }); return; }
        catch (e) { if (e.name === 'AbortError') return; }
    }
    // Fallback: copy to clipboard
    try {
        await navigator.clipboard.writeText(`${text}\n${url}`);
        showToast('Link copied to clipboard! 📋', 'info');
    } catch {
        showToast('Share: ' + text, 'info');
    }
}

// ─── Shared Trip Card Builder ─────────────────────────────────
/**
 * Builds the HTML for a trip card.
 * @param {Object} trip - Trip data object
 * @param {Set} wishlistSet - Set of wishlisted trip IDs
 * @param {Object} opts - Options: { showLeave, showJoin, showDetails, onJoin }
 */
function buildTripCard(trip, wishlistSet = new Set(), opts = {}) {
    const {
        showLeave = false,
        showJoin = true,
        actionLabel = null,
        actionClass = '',
        isHostCard = false,
        onJoinCallback = null
    } = opts;

    const isWishlisted = wishlistSet.has(trip._id);
    const cat = trip.category || 'other';
    const catColor = getCategoryColor(cat);
    const catIcon = getCategoryIcon(cat);
    const duration = getTripDuration(trip.date, trip.end_date);
    const spots = trip.max_participants ? `${trip.current_participants || 0}/${trip.max_participants}` : null;
    const fillPct = trip.max_participants ? Math.min(100, ((trip.current_participants || 0) / trip.max_participants) * 100) : 0;
    const isFull = trip.max_participants && (trip.current_participants || 0) >= trip.max_participants;

    const joinBtn = isHostCard
        ? `<span class="btn btn-success" style="flex:1;cursor:default;"><i class="fa-solid fa-crown"></i> Hosting</span>`
        : showLeave
            ? `<button class="btn btn-outline-danger" onclick="handleLeaveTrip('${trip._id}', this)" style="flex:1;background:transparent;border:1px solid rgba(239,68,68,0.4);color:#f87171;"><i class="fa-solid fa-right-from-bracket"></i> Leave</button>`
            : trip.is_joined
                ? `<button disabled class="btn btn-success" style="flex:1;"><i class="fa-solid fa-check"></i> Joined</button>`
                : isFull
                    ? `<button disabled class="btn" style="flex:1;background:#1e293b;color:var(--text-dim);">Full</button>`
                    : `<button onclick="${onJoinCallback || `joinTrip('${trip._id}',${trip.budget})`}" id="btn-${trip._id}" style="flex:1;"><i class="fa-solid fa-handshake"></i> Join</button>`;

    return `
        <div class="trip-card" id="card-${trip._id}">
            <div class="trip-image" style="background-image:url('${getImageUrl(trip.location)}')">
                <div class="trip-image-overlay">
                    <button class="trip-wish-btn ${isWishlisted ? 'wishlisted' : ''}" onclick="handleWishlistToggle('${trip._id}',this)" title="Save trip">
                        <i class="fa-${isWishlisted ? 'solid' : 'regular'} fa-heart"></i>
                    </button>
                    <button class="trip-share-btn" onclick="shareTrip('${trip.title.replace(/'/g,"\\'")}','${trip.location.replace(/'/g,"\\'")}')">
                        <i class="fa-solid fa-share-nodes"></i>
                    </button>
                </div>
                <span class="category-tag" style="color:${catColor};border-color:${catColor}44;">
                    <i class="fa-solid ${catIcon}"></i> ${cat}
                </span>
                ${duration ? `<span class="duration-badge"><i class="fa-regular fa-clock"></i> ${duration}</span>` : ''}
            </div>
            <div class="trip-content">
                <h3>${trip.title}</h3>
                <div class="badge-container">
                    <span class="badge badge-location"><i class="fa-solid fa-location-dot"></i> ${trip.location}</span>
                    <span class="badge badge-date"><i class="fa-regular fa-calendar"></i> ${trip.date}</span>
                    <span class="badge badge-budget"><i class="fa-solid fa-dollar-sign"></i> ${trip.budget > 0 ? '$' + trip.budget : 'Free'}</span>
                </div>
                ${spots ? `
                <div class="trip-participants">
                    <i class="fa-solid fa-users" style="font-size:0.75rem;color:var(--primary-light);"></i>
                    <span>${spots} spots</span>
                    <div class="participants-bar"><div class="participants-fill" style="width:${fillPct}%"></div></div>
                    ${isFull ? '<span style="color:#f87171;font-weight:600;font-size:0.75rem;">Full</span>' : ''}
                </div>` : ''}
                <div class="actions">
                    <button class="btn btn-details" onclick="openModal('${trip._id}')" style="flex:1;">
                        <i class="fa-solid fa-circle-info"></i> Details
                    </button>
                    ${joinBtn}
                </div>
            </div>
        </div>`;
}

// Global wishlist toggle wrapper (for shared card)
async function handleWishlistToggle(tripId, btn) {
    await toggleWishlist(tripId, btn);
}

// ─── Leave Trip Helper ────────────────────────────────────────
async function handleLeaveTrip(tripId, btn) {
    if (!confirm('Are you sure you want to leave this trip?')) return;
    const userId = getUserId();
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
    try {
        await apiCall(`/join/${userId}/${tripId}`, 'DELETE');
        const card = document.getElementById(`card-${tripId}`);
        if (card) {
            card.style.transition = 'all 0.3s ease';
            card.style.opacity = '0';
            card.style.transform = 'scale(0.95)';
            setTimeout(() => card.remove(), 300);
        }
        showToast('You left the trip.', 'info');
    } catch (e) {
        showToast(e.message, 'error');
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-right-from-bracket"></i> Leave';
    }
}

// ─── Navbar Profile Initials ──────────────────────────────────
function renderNavProfile() {
    const el = document.querySelector('.nav-profile-btn');
    if (el) {
        const initials = getUserInitials();
        const verified = isVerified();
        el.innerHTML = `${initials}${verified ? '<span class="verified-dot" title="Verified Host">✓</span>' : ''}`;
    }
}

// ─── Mobile Nav ───────────────────────────────────────────────
function toggleMobileNav() {
    const drawer = document.getElementById('mobile-nav-drawer');
    const overlay = document.getElementById('mobile-nav-overlay');
    if (!drawer) return;
    drawer.classList.toggle('open');
    overlay.classList.toggle('visible');
    document.body.style.overflow = drawer.classList.contains('open') ? 'hidden' : '';
}

function closeMobileNav() {
    const drawer = document.getElementById('mobile-nav-drawer');
    const overlay = document.getElementById('mobile-nav-overlay');
    if (!drawer) return;
    drawer.classList.remove('open');
    overlay.classList.remove('visible');
    document.body.style.overflow = '';
}

// ─── DOMContentLoaded Init ────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Sticky navbar class
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', () => navbar.classList.toggle('scrolled', window.scrollY > 20));
    }
    renderNavProfile();

    // Back to top button
    const btt = document.getElementById('back-to-top');
    if (btt) {
        window.addEventListener('scroll', () => btt.classList.toggle('visible', window.scrollY > 400));
        btt.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
    }

    // Mobile nav overlay close
    const overlay = document.getElementById('mobile-nav-overlay');
    if (overlay) overlay.addEventListener('click', closeMobileNav);
});

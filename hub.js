// Логика страницы /hub. Все заявки хранятся в SQLite и загружаются через API Flask.
const CSRF = document.querySelector('meta[name="csrf-token"]').content;
const IS_ADMIN = document.body.dataset.role === 'admin';
const STATUSES = ['Open', 'In Progress', 'Resolved'];

let tickets = [];
let currentFilter = 'all';
let searchText = '';

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initTheme();
    initForm();
    initFaq();
    initFilters();
    initSearch();
    loadTickets();
    loadStats();
});

// ---------- API ----------
async function api(url, method = 'GET', body = null) {
    const options = { method, headers: { 'X-CSRF-Token': CSRF } };
    if (body) {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(body);
    }
    const response = await fetch(url, options);
    if (response.status === 401) {
        window.location.href = '/login';
        throw new Error('Not authenticated');
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || 'Request failed');
    return data;
}

async function loadTickets() {
    try {
        tickets = await api('/api/tickets');
    } catch (err) {
        tickets = [];
    }
    renderTickets();
}

async function loadStats() {
    try {
        const s = await api('/api/stats');
        document.getElementById('stat-total').textContent = s.total;
        document.getElementById('stat-resolved').textContent = s.resolved;
        document.getElementById('stat-open').textContent = s.open;
    } catch (err) { /* статистика не критична */ }
}

// ---------- Безопасный вывод текста ----------
function esc(value) {
    const div = document.createElement('div');
    div.textContent = value == null ? '' : String(value);
    return div.innerHTML;
}

// ---------- Вкладки ----------
function switchTab(tabId) {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabId);
    });
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.toggle('active', pane.id === `tab-${tabId}`);
    });
}

function initTabs() {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
}

// ---------- Тёмная / светлая тема ----------
function initTheme() {
    const toggleBtn = document.getElementById('theme-toggle');
    if (!toggleBtn) return;
    const store = (v) => { try { localStorage.setItem('edu_theme', v); } catch (e) {} };
    let saved = 'light';
    try { saved = localStorage.getItem('edu_theme') || 'light'; } catch (e) {}

    if (saved === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        toggleBtn.textContent = '☀️';
    }

    toggleBtn.addEventListener('click', () => {
        if (document.documentElement.getAttribute('data-theme') === 'dark') {
            document.documentElement.removeAttribute('data-theme');
            store('light');
            toggleBtn.textContent = '🌙';
        } else {
            document.documentElement.setAttribute('data-theme', 'dark');
            store('dark');
            toggleBtn.textContent = '☀️';
        }
    });
}

// ---------- Заявки ----------
function statusClass(status) {
    if (status === 'Resolved') return 'done';
    if (status === 'In Progress') return 'work';
    return 'open';
}

function renderTickets() {
    const container = document.getElementById('tickets-container');
    const badge = document.getElementById('ticket-badge');
    if (!container) return;

    if (badge) badge.textContent = tickets.length;

    const q = searchText.toLowerCase();
    const filtered = tickets.filter(t =>
        (currentFilter === 'all' || t.status === currentFilter) &&
        (!q || `${t.id} ${t.name} ${t.group} ${t.category} ${t.desc}`.toLowerCase().includes(q))
    );

    if (filtered.length === 0) {
        container.innerHTML = tickets.length === 0
            ? '<div class="empty-state">You have no tickets yet. Create your first one!</div>'
            : '<div class="empty-state">No tickets found.</div>';
        return;
    }

    container.innerHTML = filtered.map(t => `
        <div class="ticket-card">
            <div class="ticket-header">
                <span class="ticket-id">#${t.id}</span>
                <span class="ticket-status ${statusClass(t.status)}">${esc(t.status)}</span>
            </div>
            <div>
                <strong>${esc(t.category)}</strong>
                <p class="ticket-desc">${esc(t.desc)}</p>
            </div>
            ${IS_ADMIN ? `
            <div class="ticket-admin">
                <label for="st-${t.id}">Status:</label>
                <select id="st-${t.id}" data-id="${t.id}" class="status-select">
                    ${STATUSES.map(s => `<option value="${s}" ${s === t.status ? 'selected' : ''}>${s}</option>`).join('')}
                </select>
            </div>` : ''}
            <div class="ticket-footer">
                <span>👤 ${esc(t.name)} (${esc(t.group)})</span>
                <span>📅 ${esc(t.date)}</span>
            </div>
        </div>
    `).join('');

    container.querySelectorAll('.status-select').forEach(sel => {
        sel.addEventListener('change', async () => {
            try {
                const updated = await api(`/api/tickets/${sel.dataset.id}/status`, 'POST', { status: sel.value });
                tickets = tickets.map(t => t.id === updated.id ? updated : t);
                renderTickets();
                loadStats();
            } catch (err) {
                alert(err.message);
                loadTickets();
            }
        });
    });
}

function initForm() {
    const form = document.getElementById('ticket-form');
    if (!form) return;
    const errorBox = document.getElementById('ticket-error');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        errorBox.classList.add('hidden');

        const payload = {
            name: document.getElementById('ticket-name').value,
            group: document.getElementById('ticket-group').value,
            category: document.getElementById('ticket-category').value,
            desc: document.getElementById('ticket-desc').value
        };

        try {
            const created = await api('/api/tickets', 'POST', payload);
            tickets.unshift(created);
            renderTickets();
            loadStats();
            form.reset();
            document.getElementById('ticket-name').value = document.body.dataset.fullname || '';

            document.getElementById('modal-ticket-id').textContent = `#${created.id}`;
            document.getElementById('success-modal').classList.add('active');
        } catch (err) {
            errorBox.textContent = err.message;
            errorBox.classList.remove('hidden');
        }
    });
}

function closeModal() {
    document.getElementById('success-modal').classList.remove('active');
    switchTab('my-tickets');
}

function initFilters() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            renderTickets();
        });
    });
}

// ---------- Поиск (заявки + FAQ) ----------
function initSearch() {
    const input = document.getElementById('global-search');
    if (!input) return;
    input.addEventListener('input', () => {
        searchText = input.value.trim();
        renderTickets();
        const q = searchText.toLowerCase();
        document.querySelectorAll('.faq-item').forEach(item => {
            item.classList.toggle('hidden', q !== '' && !item.textContent.toLowerCase().includes(q));
        });
    });
}

// ---------- FAQ ----------
function initFaq() {
    document.querySelectorAll('.faq-question').forEach(q => {
        q.addEventListener('click', () => q.parentElement.classList.toggle('open'));
    });
}

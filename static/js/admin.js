// Admin Panel JavaScript Utilities

class AdminPanel {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkAuthStatus();
    }

    setupEventListeners() {
        // Global error handler
        window.addEventListener('error', this.handleGlobalError.bind(this));

        // AJAX setup for CSRF protection
        this.setupAjax();
    }

    setupAjax() {
        // Add CSRF token to all AJAX requests if needed
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            // You can add headers here if needed
            return originalFetch.apply(this, args);
        };
    }

    handleGlobalError(event) {
        console.error('Global error:', event.error);
        // You can show user-friendly error messages here
    }

    checkAuthStatus() {
        // Check if user is authenticated on protected pages
        if (!window.location.pathname.includes('/login')) {
            this.verifyAuth();
        }
    }

    async verifyAuth() {
        try {
            const response = await fetch('/api/health');
            if (response.status === 401) {
                window.location.href = '/admin/login';
            }
        } catch (error) {
            console.error('Auth verification failed:', error);
        }
    }

    // Utility methods
    showLoading(element) {
        element.classList.add('loading');
    }

    hideLoading(element) {
        element.classList.remove('loading');
    }

    showNotification(message, type = 'info') {
        // Simple notification implementation
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(alert);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
    }
}

// Utility functions for API calls
const ApiClient = {
    async get(url) {
        try {
            const response = await fetch(url, {
                credentials: 'include'
            });
            return await response.json();
        } catch (error) {
            console.error('GET request failed:', error);
            throw error;
        }
    },

    async post(url, data) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
                credentials: 'include'
            });
            return await response.json();
        } catch (error) {
            console.error('POST request failed:', error);
            throw error;
        }
    },

    async put(url, data) {
        try {
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
                credentials: 'include'
            });
            return await response.json();
        } catch (error) {
            console.error('PUT request failed:', error);
            throw error;
        }
    },

    async delete(url) {
        try {
            const response = await fetch(url, {
                method: 'DELETE',
                credentials: 'include'
            });
            return await response.json();
        } catch (error) {
            console.error('DELETE request failed:', error);
            throw error;
        }
    }
};

function createThemeListItem(theme, currentTheme, dropdownId) {
    const li = document.createElement('li');
    const a = document.createElement('a');
    a.className = 'dropdown-item';
    a.href = '#';
    a.textContent = theme.charAt(0).toUpperCase() + theme.slice(1);

    if (theme === currentTheme) {
        a.classList.add('active');
    }

    a.addEventListener('click', (e) => {
        e.preventDefault();

        localStorage.setItem('theme', theme);
        document.documentElement.setAttribute('data-theme', theme);
        document.getElementById('themeStylesheet').href = `/static/css/themes/${theme}.css`;

        // Обновить активные элементы во всех dropdown'ах
        document.querySelectorAll('.theme-dropdown-item').forEach(el => {
            el.classList.remove('active');
        });
        document.querySelectorAll(`[data-theme="${theme}"]`).forEach(el => {
            el.classList.add('active');
        });

        // Закрыть dropdown после выбора
        const dropdownElement = document.getElementById(dropdownId);
        if (dropdownElement) {
            const dropdown = bootstrap.Dropdown.getInstance(dropdownElement);
            if (dropdown) {
                dropdown.hide();
            }
        }
    });

    // Добавляем data-attribute для легкого обновления активного состояния
    a.setAttribute('data-theme', theme);
    a.classList.add('theme-dropdown-item');

    li.appendChild(a);
    return li;
}

async function loadThemes() {
    try {
        const themeList = document.getElementById('themeList');
        const mobileThemeList = document.getElementById('mobileThemeList');

        if (!themeList && !mobileThemeList) {
            console.error('Элементы themeList не найдены');
            return;
        }

        const res = await fetch('/admin/api/themes');

        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }

        const themes = await res.json();
        const currentTheme = localStorage.getItem('theme') || 'ocean';

        // Заполняем desktop dropdown
        if (themeList) {
            themeList.innerHTML = '';
            themes.forEach(theme => {
                themeList.appendChild(createThemeListItem(theme, currentTheme, 'themeDropdown'));
            });
        }

        // Заполняем mobile dropdown
        if (mobileThemeList) {
            mobileThemeList.innerHTML = '';
            themes.forEach(theme => {
                mobileThemeList.appendChild(createThemeListItem(theme, currentTheme, 'mobileThemeDropdown'));
            });
        }

        console.log('Темы успешно загружены');

    } catch (err) {
        console.error('Ошибка загрузки тем:', err);

        // Fallback темы
        const fallbackThemes = ['dark', 'moonlight'];
        const currentTheme = localStorage.getItem('theme') || 'ocean';

        const themeList = document.getElementById('themeList');
        const mobileThemeList = document.getElementById('mobileThemeList');

        if (themeList) {
            themeList.innerHTML = '';
            fallbackThemes.forEach(theme => {
                themeList.appendChild(createThemeListItem(theme, currentTheme, 'themeDropdown'));
            });
        }

    }
}

function setupLogout() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (!logoutBtn) return;

    logoutBtn.addEventListener('click', async e => {
        e.preventDefault();
        try {
            const res = await fetch('/admin/api/logout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            if (res.ok) window.location.href = '/admin/login';
        } catch (err) {
            console.error('Logout error:', err);
        }
    });
}

function initializeCurrentTheme() {
    const currentTheme = localStorage.getItem('theme') || 'ocean';
    document.documentElement.setAttribute('data-theme', currentTheme);
    document.getElementById('themeStylesheet').href = `/static/css/themes/${currentTheme}.css`;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Сначала инициализируем текущую тему
    initializeCurrentTheme();

    // Затем создаем экземпляр админ-панели
    window.adminPanel = new AdminPanel();
    window.ApiClient = ApiClient;

    // Загружаем темы и настраиваем logout
    loadThemes();
    setupLogout();
});

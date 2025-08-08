// paie/static/js/permissions.js

/**
 * Gestionnaire de permissions côté client pour PaiePro
 * @author PaiePro Team
 * @version 2.0
 */

class PaieProPermissions {
    constructor() {
        this.userPermissions = {};
        this.userInfo = {};
        this.initialized = false;
        
        // URLs des APIs
        this.apiUrls = {
            userInfo: '/paie/api/user-info/',
            permissions: '/paie/api/user-permissions/',
            checkPermission: '/paie/api/check-permission/',
        };
        
        // Cache des vérifications de permissions
        this.permissionCache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
        
        this.init();
    }
    
    /**
     * Initialisation du gestionnaire de permissions
     */
    async init() {
        try {
            console.log('🔐 Initialisation du système de permissions...');
            
            // Charger les informations utilisateur et permissions
            await this.loadUserPermissions();
            
            // Initialiser l'interface selon les permissions
            this.initializeUI();
            
            // Configurer les écouteurs d'événements
            this.setupEventListeners();
            
            this.initialized = true;
            console.log('✅ Système de permissions initialisé');
            
            // Émettre un événement personnalisé
            window.dispatchEvent(new CustomEvent('permissionsReady', {
                detail: { permissions: this.userPermissions, userInfo: this.userInfo }
            }));
            
        } catch (error) {
            console.error('❌ Erreur initialisation permissions:', error);
            this.handlePermissionError(error);
        }
    }
    
    /**
     * Charger les permissions utilisateur depuis l'API
     */
    async loadUserPermissions() {
        try {
            const response = await this.makeAPIRequest(this.apiUrls.permissions);
            
            if (response.success) {
                this.userPermissions = response.permissions;
                this.userInfo = response.user;
                
                // Stocker en session pour les recharges rapides
                sessionStorage.setItem('paiepro_permissions', JSON.stringify(this.userPermissions));
                sessionStorage.setItem('paiepro_user', JSON.stringify(this.userInfo));
                
                console.log('📋 Permissions chargées:', this.userPermissions);
            }
        } catch (error) {
            console.warn('⚠️ Erreur chargement permissions, utilisation cache session');
            
            // Fallback sur le cache session
            const cachedPermissions = sessionStorage.getItem('paiepro_permissions');
            const cachedUser = sessionStorage.getItem('paiepro_user');
            
            if (cachedPermissions && cachedUser) {
                this.userPermissions = JSON.parse(cachedPermissions);
                this.userInfo = JSON.parse(cachedUser);
            }
        }
    }
    
    /**
     * Vérifie si l'utilisateur a une permission spécifique
     * @param {string} permissionName - Nom de la permission
     * @param {Object} options - Options de vérification
     * @returns {boolean}
     */
    hasPermission(permissionName, options = {}) {
        // Vérification immédiate depuis le cache local
        if (this.userPermissions.hasOwnProperty(permissionName)) {
            return this.userPermissions[permissionName];
        }
        
        // Permissions par défaut pour certains rôles
        const roleDefaults = this.getRoleDefaultPermissions();
        if (roleDefaults.hasOwnProperty(permissionName)) {
            return roleDefaults[permissionName];
        }
        
        console.warn(`⚠️ Permission inconnue: ${permissionName}`);
        return false;
    }
    
    /**
     * Vérifie une permission avec l'API (pour les cas complexes)
     * @param {string} permissionName - Nom de la permission
     * @param {Object} targetObject - Objet cible optionnel
     * @returns {Promise<boolean>}
     */
    async checkPermissionAPI(permissionName, targetObject = null) {
        const cacheKey = `${permissionName}_${targetObject ? targetObject.id : 'global'}`;
        
        // Vérifier le cache
        const cached = this.permissionCache.get(cacheKey);
        if (cached && (Date.now() - cached.timestamp < this.cacheTimeout)) {
            return cached.result;
        }
        
        try {
            const requestData = {
                permission: permissionName
            };
            
            if (targetObject) {
                requestData.target_object_id = targetObject.id;
                requestData.target_object_type = targetObject.type || 'employee';
            }
            
            const response = await this.makeAPIRequest(
                this.apiUrls.checkPermission,
                'POST',
                requestData
            );
            
            if (response.success) {
                // Mettre en cache
                this.permissionCache.set(cacheKey, {
                    result: response.has_permission,
                    timestamp: Date.now()
                });
                
                return response.has_permission;
            }
        } catch (error) {
            console.error('❌ Erreur vérification permission API:', error);
        }
        
        return false;
    }
    
    /**
     * Retourne les permissions par défaut selon le rôle
     */
    getRoleDefaultPermissions() {
        const role = this.userInfo.role;
        
        const rolePermissions = {
            'ADMIN': {
                // L'admin a tout par défaut
                'manage_users': true,
                'view_all_employees': true,
                'edit_employees': true,
                'delete_employees': true,
                'view_all_payroll': true,
                'calculate_payroll': true,
                'validate_payroll': true,
                'approve_leaves': true,
                'edit_system_settings': true
            },
            'RH': {
                'manage_users': true,
                'view_all_employees': true,
                'edit_employees': true,
                'view_all_payroll': true,
                'calculate_payroll': true,
                'approve_leaves': true,
                'validate_timesheet': true
            },
            'EMPLOYE': {
                'view_own_data': true,
                'request_leaves': true,
                'view_own_payroll': true,
                'view_own_timesheet': true
            }
        };
        
        return rolePermissions[role] || {};
    }
    
    /**
     * Initialise l'interface selon les permissions
     */
    initializeUI() {
        console.log('🎨 Initialisation UI selon permissions...');
        
        // Masquer/afficher les éléments selon les permissions
        this.toggleElementsByPermission();
        
        // Adapter les menus
        this.adaptMenus();
        
        // Configurer les boutons d'action
        this.setupActionButtons();
        
        // Adapter les tableaux de données
        this.adaptDataTables();
        
        // Configurer l'en-tête utilisateur
        this.setupUserHeader();
    }
    
    /**
     * Masque/affiche les éléments selon les data-permission
     */
    toggleElementsByPermission() {
        const elementsWithPermissions = document.querySelectorAll('[data-permission]');
        
        elementsWithPermissions.forEach(element => {
            const requiredPermission = element.getAttribute('data-permission');
            const requireAll = element.hasAttribute('data-require-all');
            
            let hasAccess = false;
            
            if (requiredPermission.includes(',')) {
                // Permissions multiples
                const permissions = requiredPermission.split(',').map(p => p.trim());
                
                if (requireAll) {
                    hasAccess = permissions.every(perm => this.hasPermission(perm));
                } else {
                    hasAccess = permissions.some(perm => this.hasPermission(perm));
                }
            } else {
                hasAccess = this.hasPermission(requiredPermission);
            }
            
            if (hasAccess) {
                element.style.display = '';
                element.classList.remove('permission-hidden');
            } else {
                element.style.display = 'none';
                element.classList.add('permission-hidden');
            }
        });
        
        console.log(`🔍 ${elementsWithPermissions.length} éléments vérifiés pour les permissions`);
    }
    
    /**
     * Adapte les menus selon les permissions
     */
    adaptMenus() {
        const menuItems = document.querySelectorAll('.nav-link[data-permission]');
        
        menuItems.forEach(item => {
            const permission = item.getAttribute('data-permission');
            
            if (!this.hasPermission(permission)) {
                const listItem = item.closest('li');
                if (listItem) {
                    listItem.style.display = 'none';
                }
            }
        });
    }
    
    /**
     * Configure les boutons d'action
     */
    setupActionButtons() {
        const actionButtons = document.querySelectorAll('.btn[data-permission]');
        
        actionButtons.forEach(button => {
            const permission = button.getAttribute('data-permission');
            
            if (!this.hasPermission(permission)) {
                button.classList.add('disabled');
                button.setAttribute('disabled', 'disabled');
                button.setAttribute('title', `Permission requise: ${permission}`);
                
                // Empêcher les clics
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    this.showPermissionDeniedMessage(permission);
                    return false;
                });
            }
        });
    }
    
    /**
     * Adapte les tableaux de données
     */
    adaptDataTables() {
        // Masquer les colonnes actions si pas de permissions
        const actionColumns = document.querySelectorAll('.table th.actions-column');
        const hasEditPermission = this.hasPermission('edit_employees');
        const hasDeletePermission = this.hasPermission('delete_employees');
        
        if (!hasEditPermission && !hasDeletePermission) {
            actionColumns.forEach(col => {
                const index = Array.from(col.parentNode.children).indexOf(col);
                
                // Masquer la colonne d'en-tête
                col.style.display = 'none';
                
                // Masquer les cellules correspondantes
                const table = col.closest('table');
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const cell = row.children[index];
                    if (cell) {
                        cell.style.display = 'none';
                    }
                });
            });
        }
    }
    
    /**
     * Configure l'en-tête utilisateur
     */
    setupUserHeader() {
        const userNameElement = document.querySelector('.user-name');
        const userRoleElement = document.querySelector('.user-role');
        const userAvatarElement = document.querySelector('.user-avatar');
        
        if (userNameElement) {
            userNameElement.textContent = this.userInfo.full_name || this.userInfo.username;
        }
        
        if (userRoleElement) {
            userRoleElement.textContent = this.userInfo.role_display;
            
            // Classe CSS selon le rôle
            const roleClasses = {
                'ADMIN': 'badge-danger',
                'RH': 'badge-warning',
                'EMPLOYE': 'badge-info'
            };
            
            const roleClass = roleClasses[this.userInfo.role] || 'badge-secondary';
            userRoleElement.className = `badge ${roleClass}`;
        }
        
        if (userAvatarElement && this.userInfo.avatar) {
            userAvatarElement.src = this.userInfo.avatar;
        }
    }
    
    /**
     * Configure les écouteurs d'événements
     */
    setupEventListeners() {
        // Écouter les changements de hash pour les SPAs
        window.addEventListener('hashchange', () => {
            this.toggleElementsByPermission();
        });
        
        // Écouter les mises à jour dynamiques de contenu
        document.addEventListener('contentUpdated', () => {
            this.toggleElementsByPermission();
            this.setupActionButtons();
        });
        
        // Vérification périodique des permissions (toutes les 5 minutes)
        setInterval(() => {
            this.refreshPermissions();
        }, 5 * 60 * 1000);
        
        // Gérer les erreurs de permission des requêtes AJAX
        document.addEventListener('ajaxError', (event) => {
            if (event.detail && event.detail.status === 403) {
                this.handlePermissionDenied(event.detail.response);
            }
        });
    }
    
    /**
     * Actualise les permissions depuis l'API
     */
    async refreshPermissions() {
        try {
            await this.loadUserPermissions();
            this.toggleElementsByPermission();
            console.log('🔄 Permissions actualisées');
        } catch (error) {
            console.warn('⚠️ Impossible d\'actualiser les permissions:', error);
        }
    }
    
    /**
     * Affiche un message d'erreur de permission
     */
    showPermissionDeniedMessage(permission) {
        const message = `Vous n'avez pas la permission "${permission}" pour effectuer cette action.`;
        
        // Utiliser Bootstrap Toast si disponible
        if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
            this.showToast('Accès refusé', message, 'warning');
        } else {
            alert(message);
        }
        
        console.warn(`🚫 Permission refusée: ${permission}`);
    }
    
    /**
     * Gère les erreurs de permission
     */
    handlePermissionDenied(response) {
        let message = 'Accès refusé';
        
        if (response && response.message) {
            message = response.message;
        }
        
        this.showPermissionDeniedModal(message);
    }
    
    /**
     * Affiche une modal d'erreur de permission
     */
    showPermissionDeniedModal(message) {
        const modalHtml = `
            <div class="modal fade" id="permissionDeniedModal" tabindex="-1">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header bg-warning text-dark">
                            <h5 class="modal-title">
                                <i class="fas fa-exclamation-triangle me-2"></i>
                                Accès refusé
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                            <div class="alert alert-info">
                                <strong>Votre rôle actuel:</strong> 
                                <span class="badge bg-info ms-2">${this.userInfo.role_display}</span>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                Fermer
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Supprimer l'ancienne modal si elle existe
        const existingModal = document.getElementById('permissionDeniedModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Ajouter la nouvelle modal
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Afficher la modal
        if (typeof bootstrap !== 'undefined') {
            const modal = new bootstrap.Modal(document.getElementById('permissionDeniedModal'));
            modal.show();
        }
    }
    
    /**
     * Affiche un toast de notification
     */
    showToast(title, message, type = 'info') {
        const toastHtml = `
            <div class="toast align-items-center text-bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        <strong>${title}</strong><br>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                            data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        const toastElement = toastContainer.lastElementChild;
        if (typeof bootstrap !== 'undefined') {
            const toast = new bootstrap.Toast(toastElement);
            toast.show();
        }
    }
    
    /**
     * Utilitaire pour les requêtes API
     */
    async makeAPIRequest(url, method = 'GET', data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        };
        
        // CSRF Token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) {
            options.headers['X-CSRFToken'] = csrfToken.value;
        }
        
        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        
        if (response.status === 403) {
            const errorData = await response.json();
            this.handlePermissionDenied(errorData);
            throw new Error('Permission refusée');
        }
        
        if (response.status === 401) {
            // Redirection vers login
            window.location.href = '/paie/auth/login/';
            return;
        }
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    /**
     * Gère les erreurs de permission
     */
    handlePermissionError(error) {
        console.error('💥 Erreur système permissions:', error);
        
        this.showToast(
            'Erreur Permissions',
            'Impossible de charger les permissions. Certaines fonctionnalités peuvent être limitées.',
            'danger'
        );
    }
    
    /**
     * Méthodes utilitaires publiques
     */
    isAdmin() {
        return this.userInfo.is_admin === true;
    }
    
    isRH() {
        return this.userInfo.is_rh === true;
    }
    
    isEmployee() {
        return this.userInfo.is_employe === true;
    }
    
    isManager() {
        return this.userInfo.is_manager === true;
    }
    
    getUserRole() {
        return this.userInfo.role;
    }
    
    getUserInfo() {
        return this.userInfo;
    }
    
    getAllPermissions() {
        return this.userPermissions;
    }
}

// Instance globale
let paieProPermissions;

// Initialisation automatique au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    paieProPermissions = new PaieProPermissions();
    
    // Exposer globalement pour l'utilisation dans d'autres scripts
    window.PaieProPermissions = paieProPermissions;
});

// Fonctions utilitaires globales pour compatibilité
window.hasPermission = (permission) => {
    return paieProPermissions ? paieProPermissions.hasPermission(permission) : false;
};

window.isAdmin = () => {
    return paieProPermissions ? paieProPermissions.isAdmin() : false;
};

window.isRH = () => {
    return paieProPermissions ? paieProPermissions.isRH() : false;
};

window.isEmployee = () => {
    return paieProPermissions ? paieProPermissions.isEmployee() : false;
};

// Export pour modules ES6 si supportés
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PaieProPermissions;
}
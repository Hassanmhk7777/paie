
/**
 * Gestionnaire SPA amélioré pour éviter les conflits JavaScript
 * Version 2.0 - Avec nettoyage automatique
 */

// Namespace principal
if (typeof window.PAIE_SPA === 'undefined') {
    window.PAIE_SPA = {
        currentPage: null,
        charts: {},
        variables: {},
        initialized: {},
        eventListeners: {},
        intervals: {}
    };
}

class SPAManager {
    constructor() {
        this.currentPage = null;
        this.isLoading = false;
    }

    /**
     * Nettoie complètement une page SPA
     */
    cleanupPage(pageName) {
        const ns = window.PAIE_SPA;
        
        // 1. Détruire les graphiques Chart.js
        if (ns.charts[pageName]) {
            Object.values(ns.charts[pageName]).forEach(chart => {
                if (chart && typeof chart.destroy === 'function') {
                    try {
                        chart.destroy();
                    } catch (e) {
                        console.warn('Erreur lors de la destruction du graphique:', e);
                    }
                }
            });
            delete ns.charts[pageName];
        }

        // 2. Nettoyer les intervalles
        if (ns.intervals[pageName]) {
            Object.values(ns.intervals[pageName]).forEach(intervalId => {
                clearInterval(intervalId);
            });
            delete ns.intervals[pageName];
        }

        // 3. Supprimer les event listeners spécifiques
        if (ns.eventListeners[pageName]) {
            ns.eventListeners[pageName].forEach(listener => {
                try {
                    listener.element.removeEventListener(listener.event, listener.handler);
                } catch (e) {
                    console.warn('Erreur lors de la suppression de listener:', e);
                }
            });
            delete ns.eventListeners[pageName];
        }

        // 4. Nettoyer les variables
        if (ns.variables[pageName]) {
            delete ns.variables[pageName];
        }

        // 5. Marquer comme non initialisé
        ns.initialized[pageName] = false;

        console.log(\`🧹 Page SPA nettoyée: \${pageName}\`);
    }

    /**
     * Charge une nouvelle page SPA avec nettoyage automatique
     */
    loadPage(url, targetElement = '#main-content') {
        if (this.isLoading) {
            console.log('Chargement en cours, ignoré...');
            return;
        }

        this.isLoading = true;
        
        // Nettoyer la page actuelle
        if (this.currentPage) {
            this.cleanupPage(this.currentPage);
        }

        // Afficher le loader
        $(targetElement).html('<div class="text-center p-5"><i class="fas fa-spinner fa-spin fa-2x text-primary"></i><br>Chargement...</div>');

        return $.get(url)
            .done((data) => {
                $(targetElement).html(data);
                
                // Extraire le nom de la page depuis l'URL
                const pageName = this.extractPageName(url);
                this.currentPage = pageName;
                
                // Marquer la page comme chargée
                window.PAIE_SPA.initialized[pageName] = true;
                
                console.log(\`📄 Page SPA chargée: \${pageName}\`);
                
                // Déclencher l'événement de page chargée
                $(document).trigger('spa:pageLoaded', { pageName, url });
            })
            .fail((xhr) => {
                console.error('Erreur lors du chargement SPA:', xhr);
                $(targetElement).html('<div class="alert alert-danger">Erreur lors du chargement de la page. Veuillez réessayer.</div>');
            })
            .always(() => {
                this.isLoading = false;
            });
    }

    /**
     * Extrait le nom de la page depuis l'URL
     */
    extractPageName(url) {
        const match = url.match(/\/spa\/([\w-]+)\/?/);
        return match ? match[1] : 'unknown';
    }

    /**
     * Enregistre un graphique
     */
    registerChart(pageName, chartName, chartInstance) {
        if (!window.PAIE_SPA.charts[pageName]) {
            window.PAIE_SPA.charts[pageName] = {};
        }
        window.PAIE_SPA.charts[pageName][chartName] = chartInstance;
    }

    /**
     * Enregistre un interval
     */
    registerInterval(pageName, intervalName, intervalId) {
        if (!window.PAIE_SPA.intervals[pageName]) {
            window.PAIE_SPA.intervals[pageName] = {};
        }
        window.PAIE_SPA.intervals[pageName][intervalName] = intervalId;
    }

    /**
     * Enregistre un event listener
     */
    registerEventListener(pageName, element, event, handler) {
        if (!window.PAIE_SPA.eventListeners[pageName]) {
            window.PAIE_SPA.eventListeners[pageName] = [];
        }
        window.PAIE_SPA.eventListeners[pageName].push({ element, event, handler });
        element.addEventListener(event, handler);
    }

    /**
     * Sauvegarde une variable de page
     */
    setVariable(pageName, varName, value) {
        if (!window.PAIE_SPA.variables[pageName]) {
            window.PAIE_SPA.variables[pageName] = {};
        }
        window.PAIE_SPA.variables[pageName][varName] = value;
    }

    /**
     * Récupère une variable de page
     */
    getVariable(pageName, varName) {
        return window.PAIE_SPA.variables[pageName] && window.PAIE_SPA.variables[pageName][varName];
    }
}

// Instance globale
window.spaManager = new SPAManager();

// Fonctions raccourcies pour compatibilité
window.registerChart = (pageName, chartName, chartInstance) => {
    window.spaManager.registerChart(pageName, chartName, chartInstance);
};

window.cleanupSPAPage = (pageName) => {
    window.spaManager.cleanupPage(pageName);
};

// Auto-cleanup avant déchargement de la page
window.addEventListener('beforeunload', () => {
    if (window.spaManager.currentPage) {
        window.spaManager.cleanupPage(window.spaManager.currentPage);
    }
});

console.log('✅ SPAManager chargé et prêt!');

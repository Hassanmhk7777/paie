/**
 * Utilitaires pour la gestion SPA
 * Évite les conflits de variables JavaScript lors du rechargement de contenu
 */

// Namespace global pour l'application SPA
if (typeof window.SPA_PAIE === 'undefined') {
    window.SPA_PAIE = {
        charts: {},
        variables: {},
        initialized: {}
    };
}

/**
 * Détruit tous les graphiques Chart.js d'un namespace
 * @param {string} namespace - Le namespace des graphiques à détruire
 */
function destroyCharts(namespace) {
    if (window.SPA_PAIE.charts[namespace]) {
        Object.values(window.SPA_PAIE.charts[namespace]).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        window.SPA_PAIE.charts[namespace] = {};
    }
}

/**
 * Enregistre un graphique dans le namespace global
 * @param {string} namespace - Le namespace (ex: 'dashboard', 'leave')
 * @param {string} chartName - Le nom du graphique
 * @param {Chart} chartInstance - L'instance Chart.js
 */
function registerChart(namespace, chartName, chartInstance) {
    if (!window.SPA_PAIE.charts[namespace]) {
        window.SPA_PAIE.charts[namespace] = {};
    }
    window.SPA_PAIE.charts[namespace][chartName] = chartInstance;
}

/**
 * Nettoie les ressources avant le chargement d'une nouvelle page SPA
 * @param {string} page - Le nom de la page (ex: 'dashboard', 'leave-balances')
 */
function cleanupSPAPage(page) {
    // Détruire les graphiques spécifiques à la page
    destroyCharts(page);
    
    // Nettoyer les event listeners spécifiques
    if (window.SPA_PAIE.initialized[page]) {
        console.log(`Nettoyage de la page SPA: ${page}`);
        window.SPA_PAIE.initialized[page] = false;
    }
}

/**
 * Marque une page SPA comme initialisée
 * @param {string} page - Le nom de la page
 */
function markSPAPageInitialized(page) {
    window.SPA_PAIE.initialized[page] = true;
}

/**
 * Vérifie si une page SPA est déjà initialisée
 * @param {string} page - Le nom de la page
 * @returns {boolean}
 */
function isSPAPageInitialized(page) {
    return window.SPA_PAIE.initialized[page] === true;
}

// Fonction de debug pour inspecter l'état SPA
function debugSPA() {
    console.log('État SPA:', window.SPA_PAIE);
}

// Exposer les fonctions globalement
window.destroyCharts = destroyCharts;
window.registerChart = registerChart;
window.cleanupSPAPage = cleanupSPAPage;
window.markSPAPageInitialized = markSPAPageInitialized;
window.isSPAPageInitialized = isSPAPageInitialized;
window.debugSPA = debugSPA;

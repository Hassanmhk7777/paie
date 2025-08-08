
/**
 * Navigation SPA avec gestion automatique des ressources
 */

$(document).ready(function() {
    
    // Intercepter tous les liens de navigation SPA
    $(document).on('click', 'a[href^="/spa/"], .spa-link', function(e) {
        e.preventDefault();
        
        const url = $(this).attr('href');
        const targetContent = $(this).data('target') || '#main-content';
        
        // Mettre à jour l'URL sans recharger la page
        if (history.pushState) {
            history.pushState(null, null, url);
        }
        
        // Charger la nouvelle page
        window.spaManager.loadPage(url, targetContent);
        
        // Mettre à jour le menu actif
        updateActiveMenu($(this));
    });
    
    // Gestion du bouton retour du navigateur
    window.addEventListener('popstate', function(e) {
        const currentUrl = window.location.pathname;
        if (currentUrl.startsWith('/spa/')) {
            window.spaManager.loadPage(currentUrl);
        }
    });
    
    // Fonction pour mettre à jour le menu actif
    function updateActiveMenu($clickedLink) {
        // Retirer la classe active de tous les liens
        $('.nav-link, .sidebar-link').removeClass('active');
        
        // Ajouter la classe active au lien cliqué
        $clickedLink.addClass('active');
        
        // Ajouter la classe active aux parents si c'est un sous-menu
        $clickedLink.parents('.nav-item').find('.nav-link').addClass('active');
    }
    
    // Auto-refresh pour certaines pages (optionnel)
    $(document).on('spa:pageLoaded', function(e, data) {
        if (data.pageName === 'dashboard') {
            // Rafraîchir le dashboard toutes les 30 secondes
            const refreshInterval = setInterval(() => {
                if (window.spaManager.currentPage === 'dashboard') {
                    // Recharger uniquement les stats sans refaire toute la page
                    refreshDashboardStats();
                } else {
                    clearInterval(refreshInterval);
                }
            }, 30000);
            
            window.spaManager.registerInterval('dashboard', 'auto-refresh', refreshInterval);
        }
    });
});

/**
 * Fonction pour rafraîchir les stats du dashboard
 */
function refreshDashboardStats() {
    $.get('/api/dashboard/stats/')
        .done(function(data) {
            // Mettre à jour les KPIs sans recharger la page
            updateDashboardKPIs(data);
        })
        .fail(function() {
            console.log('Erreur lors du rafraîchissement des stats');
        });
}

/**
 * Met à jour les KPIs du dashboard
 */
function updateDashboardKPIs(data) {
    if (data.employees_count !== undefined) {
        $('#total-employees .kpi-value').text(data.employees_count);
    }
    // Ajouter d'autres KPIs selon les besoins
}

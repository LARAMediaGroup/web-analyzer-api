/**
 * Public JavaScript for the Web Analyzer plugin
 *
 * This handles tracking clicks on links inserted by the plugin.
 */
(function( $ ) {
    'use strict';

    $(function() {
        // Track clicks on links inserted by Web Analyzer
        $('body').on('click', 'a.web-analyzer-tracked-link', function(e) {
            var suggestionId = $(this).data('suggestion-id');
            
            if (!suggestionId) {
                return; // Not a tracked link or missing ID
            }
            
            // Send tracking data to server
            $.ajax({
                url: webAnalyzerData.ajaxUrl,
                type: 'POST',
                data: {
                    action: 'web_analyzer_track_click',
                    nonce: webAnalyzerData.nonce,
                    suggestion_id: suggestionId
                },
                // Use async to avoid delaying the link navigation
                async: true
            });
            
            // Let the default link behavior happen normally
            // No need to prevent default
        });
    });

})( jQuery );
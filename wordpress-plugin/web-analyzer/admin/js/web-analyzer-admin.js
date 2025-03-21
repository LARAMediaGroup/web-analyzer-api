/**
 * Admin JavaScript for the Web Analyzer plugin
 */
(function( $ ) {
    'use strict';

    $(function() {
        // Test connection to API
        $('#web-analyzer-test-connection').on('click', function() {
            var $button = $(this);
            var $status = $('#web-analyzer-connection-status');
            
            // Disable button during test
            $button.prop('disabled', true).text(webAnalyzerL10n.testing);
            
            // Clear previous status
            $status.removeClass('success error').text('');
            
            // Get form values
            var apiUrl = $('#web_analyzer_api_url').val();
            var apiKey = $('#web_analyzer_api_key').val();
            var siteId = $('#web_analyzer_site_id').val();
            
            // Validate inputs
            if (!apiUrl) {
                $status.addClass('error').text(webAnalyzerL10n.missingUrl);
                $button.prop('disabled', false).text(webAnalyzerL10n.testConnection);
                return;
            }
            
            if (!apiKey) {
                $status.addClass('error').text(webAnalyzerL10n.missingKey);
                $button.prop('disabled', false).text(webAnalyzerL10n.testConnection);
                return;
            }
            
            // Test connection
            $.ajax({
                url: apiUrl + '/health',
                type: 'GET',
                headers: {
                    'X-API-Key': apiKey
                },
                timeout: 10000, // 10 second timeout
                success: function(response) {
                    if (response && response.status === 'ok') {
                        $status.addClass('success').text(webAnalyzerL10n.connectionSuccess);
                    } else {
                        $status.addClass('error').text(webAnalyzerL10n.invalidResponse);
                    }
                },
                error: function(xhr, status, error) {
                    if (status === 'timeout') {
                        $status.addClass('error').text(webAnalyzerL10n.connectionTimeout);
                    } else if (xhr.status === 401) {
                        $status.addClass('error').text(webAnalyzerL10n.authError);
                    } else {
                        $status.addClass('error').text(webAnalyzerL10n.connectionError + ': ' + error);
                    }
                },
                complete: function() {
                    $button.prop('disabled', false).text(webAnalyzerL10n.testConnection);
                }
            });
        });
        
        // Classic Editor integration
        if ($('#web-analyzer-classic-editor').length) {
            $('#web-analyzer-analyze').on('click', function() {
                var $button = $(this);
                var $status = $('#web-analyzer-status');
                var postId = $('#post_ID').val();
                
                // Disable button during analysis
                $button.prop('disabled', true).text(webAnalyzerL10n.analyzing);
                
                // Clear previous status
                $status.text('');
                
                // Make API request
                $.ajax({
                    url: webAnalyzerAdmin.apiUrl + '/analyze',
                    type: 'POST',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', webAnalyzerAdmin.apiNonce);
                    },
                    data: JSON.stringify({
                        post_id: postId
                    }),
                    contentType: 'application/json',
                    dataType: 'json',
                    success: function(response) {
                        if (response.success) {
                            // Reload the metabox content to show suggestions
                            location.reload();
                        } else {
                            $status.text(response.message || webAnalyzerL10n.analysisError);
                        }
                    },
                    error: function(xhr, status, error) {
                        $status.text(webAnalyzerL10n.analysisError + ': ' + error);
                    },
                    complete: function() {
                        $button.prop('disabled', false).text(webAnalyzerL10n.analyzeContent);
                    }
                });
            });
            
            // Handle link insertion in classic editor
            $('.insert-link').on('click', function() {
                var anchorText = $(this).data('anchor');
                var url = $(this).data('url');
                
                // Get the WordPress editor
                var wpEditor = window.tinyMCE && window.tinyMCE.get('content');
                
                if (wpEditor && !wpEditor.isHidden()) {
                    // Visual editor active, use TinyMCE
                    wpEditor.execCommand('mceInsertLink', false, {
                        title: anchorText,
                        href: url,
                        target: '_blank',
                        'class': 'web-analyzer-tracked-link',
                        'data-suggestion-id': $(this).data('id')
                    });
                } else {
                    // Text editor active, use plain HTML
                    var textArea = $('#content');
                    var htmlLink = '<a href="' + url + '" class="web-analyzer-tracked-link" data-suggestion-id="' + 
                                  $(this).data('id') + '">' + anchorText + '</a>';
                    
                    // Insert at cursor position or append
                    if (textArea.length) {
                        var cursorPos = textArea[0].selectionStart;
                        var textBefore = textArea.val().substring(0, cursorPos);
                        var textAfter = textArea.val().substring(cursorPos, textArea.val().length);
                        textArea.val(textBefore + htmlLink + textAfter);
                    }
                }
                
                // Mark as applied
                $.ajax({
                    url: webAnalyzerAdmin.apiUrl + '/apply-suggestion/' + $(this).data('id'),
                    type: 'POST',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', webAnalyzerAdmin.apiNonce);
                    }
                });
            });
        }
    });

})( jQuery );
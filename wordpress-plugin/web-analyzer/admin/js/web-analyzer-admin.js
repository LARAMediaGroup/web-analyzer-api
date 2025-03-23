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
        
        // Detailed debugging functionality
        $('#web-analyzer-debug-test').on('click', function() {
            var $button = $(this);
            var $debugResults = $('#web-analyzer-debug-results');
            var $debugSteps = $('.web-analyzer-debug-steps');
            
            // Get form values
            var apiUrl = $('#web_analyzer_api_url').val();
            var apiKey = $('#web_analyzer_api_key').val();
            var siteId = $('#web_analyzer_site_id').val();
            
            // Show debug results panel
            $debugResults.show();
            $debugSteps.show();
            $debugResults.html('Starting detailed connection test...\n');
            
            // Reset step indicators
            $('#web-analyzer-debug-steps-list li').removeClass('success error').addClass('pending');
            
            // Step 1: Check URL format
            $('#step-fetch').removeClass('pending').addClass('in-progress');
            $debugResults.append('Step 1: Validating API URL format...\n');
            
            if (!apiUrl) {
                $('#step-fetch').removeClass('in-progress').addClass('error');
                $debugResults.append('ERROR: Missing API URL\n');
                return;
            }
            
            // Basic URL validation
            try {
                new URL(apiUrl);
                $debugResults.append('URL format is valid: ' + apiUrl + '\n');
                $('#step-fetch').removeClass('in-progress').addClass('success');
            } catch (e) {
                $('#step-fetch').removeClass('in-progress').addClass('error');
                $debugResults.append('ERROR: Invalid URL format: ' + e.message + '\n');
                return;
            }
            
            // Step 2: Check API key
            $('#step-auth').removeClass('pending').addClass('in-progress');
            $debugResults.append('\nStep 2: Checking API key...\n');
            
            if (!apiKey) {
                $('#step-auth').removeClass('in-progress').addClass('error');
                $debugResults.append('ERROR: Missing API key\n');
                return;
            }
            
            $debugResults.append('API key provided (hidden for security)\n');
            $('#step-auth').removeClass('in-progress').addClass('success');
            
            // Step 3: Test health endpoint
            $('#step-health').removeClass('pending').addClass('in-progress');
            $debugResults.append('\nStep 3: Testing API health endpoint...\n');
            
            $.ajax({
                url: apiUrl + '/health',
                type: 'GET',
                headers: {
                    'X-API-Key': apiKey
                },
                timeout: 10000,
                success: function(response) {
                    if (response && response.status === 'ok') {
                        $('#step-health').removeClass('in-progress').addClass('success');
                        $debugResults.append('✓ API health check successful\n');
                        $debugResults.append('Response: ' + JSON.stringify(response, null, 2) + '\n');
                        
                        // Continue to step 4
                        testSiteConfig();
                    } else {
                        $('#step-health').removeClass('in-progress').addClass('error');
                        $debugResults.append('✗ API returned unexpected response\n');
                        $debugResults.append('Response: ' + JSON.stringify(response, null, 2) + '\n');
                    }
                },
                error: function(xhr, status, error) {
                    $('#step-health').removeClass('in-progress').addClass('error');
                    $debugResults.append('✗ API health check failed\n');
                    
                    if (status === 'timeout') {
                        $debugResults.append('ERROR: Connection timed out\n');
                    } else if (xhr.status === 401 || xhr.status === 403) {
                        $debugResults.append('ERROR: Authentication failed (Status ' + xhr.status + ')\n');
                    } else {
                        $debugResults.append('ERROR: ' + status + ' - ' + error + '\n');
                        $debugResults.append('Status code: ' + xhr.status + '\n');
                        
                        if (xhr.responseText) {
                            try {
                                var response = JSON.parse(xhr.responseText);
                                $debugResults.append('Response: ' + JSON.stringify(response, null, 2) + '\n');
                            } catch(e) {
                                $debugResults.append('Response text: ' + xhr.responseText + '\n');
                            }
                        }
                    }
                    
                    // Skip to network troubleshooting suggestions
                    $debugResults.append('\nTroubleshooting suggestions:\n');
                    $debugResults.append('1. Check if the API service is running\n');
                    $debugResults.append('2. Verify the URL is correct (no trailing slash)\n');
                    $debugResults.append('3. Ensure there are no network issues or firewalls blocking access\n');
                    $debugResults.append('4. Check if CORS is properly configured on the API server\n');
                }
            });
            
            // Step 4: Test site configuration
            function testSiteConfig() {
                $('#step-site').removeClass('pending').addClass('in-progress');
                $debugResults.append('\nStep 4: Verifying site configuration...\n');
                
                if (!siteId) {
                    $debugResults.append('WARNING: Site ID not provided. This is required for proper operation.\n');
                    $('#step-site').removeClass('in-progress').addClass('warning');
                    return;
                }
                
                $debugResults.append('Site ID: ' + siteId + '\n');
                
                // Make a test request to verify site configuration
                // Using a fake endpoint for demonstration - in production would use an actual API endpoint
                $.ajax({
                    url: apiUrl + '/analyze/content',
                    type: 'POST',
                    headers: {
                        'X-API-Key': apiKey,
                        'Content-Type': 'application/json'
                    },
                    data: JSON.stringify({
                        content: 'Test content',
                        title: 'Test title',
                        site_id: siteId
                    }),
                    timeout: 15000,
                    success: function(response) {
                        $('#step-site').removeClass('in-progress').addClass('success');
                        $debugResults.append('✓ API accepted the request with site configuration\n');
                        $debugResults.append('\nAll tests passed! The connection is working properly.\n');
                    },
                    error: function(xhr, status, error) {
                        // Check for specific errors that indicate the site config is correct but other issues exist
                        if (xhr.status === 400 && xhr.responseText && xhr.responseText.includes('content')) {
                            // This might be a valid error for empty content, meaning auth worked
                            $('#step-site').removeClass('in-progress').addClass('success');
                            $debugResults.append('✓ Site configuration appears valid (authentication worked)\n');
                            $debugResults.append('Response indicates content validation error, which is expected for test data\n');
                        } else if (xhr.status === 401 || xhr.status === 403) {
                            $('#step-site').removeClass('in-progress').addClass('error');
                            $debugResults.append('✗ Authentication failed with site configuration\n');
                            $debugResults.append('ERROR: API key may not be authorized for this site ID\n');
                            
                            if (xhr.responseText) {
                                try {
                                    var response = JSON.parse(xhr.responseText);
                                    $debugResults.append('Response: ' + JSON.stringify(response, null, 2) + '\n');
                                } catch(e) {
                                    $debugResults.append('Response text: ' + xhr.responseText + '\n');
                                }
                            }
                        } else {
                            $('#step-site').removeClass('in-progress').addClass('warning');
                            $debugResults.append('⚠ Could not verify site configuration\n');
                            $debugResults.append('Status: ' + status + ', Error: ' + error + '\n');
                            
                            if (xhr.responseText) {
                                try {
                                    var response = JSON.parse(xhr.responseText);
                                    $debugResults.append('Response: ' + JSON.stringify(response, null, 2) + '\n');
                                } catch(e) {
                                    $debugResults.append('Response text: ' + xhr.responseText + '\n');
                                }
                            }
                        }
                    }
                });
            }
        });
        
        // Server environment check
        $('#web-analyzer-check-env').on('click', function() {
            var $button = $(this);
            var $debugResults = $('#web-analyzer-debug-results');
            
            $debugResults.show();
            $debugResults.html('Checking server environment...\n');
            
            $.ajax({
                url: webAnalyzerAdmin.ajaxUrl,
                type: 'POST',
                data: {
                    action: 'web_analyzer_check_environment',
                    nonce: webAnalyzerAdmin.nonce
                },
                success: function(response) {
                    if (response.success) {
                        $debugResults.append('Server Environment Information:\n\n');
                        $debugResults.append('PHP Version: ' + response.data.php_version + '\n');
                        $debugResults.append('WordPress Version: ' + response.data.wp_version + '\n');
                        $debugResults.append('cURL Enabled: ' + (response.data.curl_enabled ? 'Yes' : 'No') + '\n');
                        $debugResults.append('JSON Extension: ' + (response.data.json_enabled ? 'Enabled' : 'Disabled') + '\n');
                        $debugResults.append('Memory Limit: ' + response.data.memory_limit + '\n');
                        $debugResults.append('Max Execution Time: ' + response.data.max_execution_time + ' seconds\n');
                        
                        if (response.data.active_plugins) {
                            $debugResults.append('\nActive Plugins:\n');
                            response.data.active_plugins.forEach(function(plugin) {
                                $debugResults.append('- ' + plugin + '\n');
                            });
                        }
                        
                        if (response.data.issues && response.data.issues.length > 0) {
                            $debugResults.append('\nPotential Issues Detected:\n');
                            response.data.issues.forEach(function(issue) {
                                $debugResults.append('⚠ ' + issue + '\n');
                            });
                        } else {
                            $debugResults.append('\n✓ No environment issues detected.\n');
                        }
                    } else {
                        $debugResults.append('Error retrieving environment information: ' + response.data.message);
                    }
                },
                error: function(xhr, status, error) {
                    $debugResults.append('Error checking environment: ' + error);
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
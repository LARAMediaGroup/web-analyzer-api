/**
 * Web Analyzer Advanced Debugging Script
 * 
 * This script provides comprehensive debugging functionality for the Web Analyzer WordPress plugin.
 * It tracks all API calls, displays detailed error information, and provides real-time logging.
 */

(function($) {
    'use strict';

    // Debug state 
    var debugState = {
        isLogging: false,
        lastRequest: null,
        lastResponse: null,
        errors: [],
        apiCalls: [],
        startTime: null
    };

    // Initialize the debug system
    function initDebugSystem() {
        console.log('Web Analyzer Debug System initialized');
        
        // Create debug UI if it doesn't exist
        if ($('#web-analyzer-debug-panel').length === 0) {
            createDebugUI();
        }
        
        // Hook into AJAX calls to track API communication
        hookIntoAjax();
        
        // Enhance existing buttons with debugging
        enhanceExistingButtons();
    }

    // Create the debug UI
    function createDebugUI() {
        var debugHTML = `
        <div id="web-analyzer-debug-panel" class="web-analyzer-debug-panel">
            <div class="debug-panel-header">
                <h3>Web Analyzer Debugging Panel</h3>
                <div class="debug-controls">
                    <button id="wa-debug-clear" class="button">Clear Log</button>
                    <button id="wa-debug-export" class="button">Export Log</button>
                    <label><input type="checkbox" id="wa-debug-verbose" checked> Verbose Logging</label>
                </div>
            </div>
            <div class="debug-panel-content">
                <div class="debug-tabs">
                    <button class="debug-tab-button active" data-tab="log">Live Log</button>
                    <button class="debug-tab-button" data-tab="requests">API Requests</button>
                    <button class="debug-tab-button" data-tab="responses">API Responses</button>
                    <button class="debug-tab-button" data-tab="errors">Errors</button>
                    <button class="debug-tab-button" data-tab="diagnostics">System Diagnostics</button>
                </div>
                <div class="debug-tab-content">
                    <div id="debug-tab-log" class="debug-tab active">
                        <div id="debug-log" class="debug-log"></div>
                    </div>
                    <div id="debug-tab-requests" class="debug-tab">
                        <div id="debug-requests" class="debug-requests"></div>
                    </div>
                    <div id="debug-tab-responses" class="debug-tab">
                        <div id="debug-responses" class="debug-responses"></div>
                    </div>
                    <div id="debug-tab-errors" class="debug-tab">
                        <div id="debug-errors" class="debug-errors"></div>
                    </div>
                    <div id="debug-tab-diagnostics" class="debug-tab">
                        <div id="debug-diagnostics" class="debug-diagnostics"></div>
                    </div>
                </div>
            </div>
            <div class="debug-status-bar">
                <span id="debug-status">Ready</span>
                <span id="debug-api-status">API: Unknown</span>
                <span id="debug-timer">00:00:00</span>
            </div>
        </div>
        `;

        // Add the debug panel to the page
        $('.web-analyzer-settings-section').last().after(debugHTML);
        
        // Initialize event handlers for the debug panel
        initDebugPanelEvents();
        
        // Run system diagnostics
        runSystemDiagnostics();
    }
    
    // Initialize debug panel event handlers
    function initDebugPanelEvents() {
        // Tab switching
        $('.debug-tab-button').on('click', function() {
            var tabId = $(this).data('tab');
            $('.debug-tab-button').removeClass('active');
            $(this).addClass('active');
            $('.debug-tab').removeClass('active');
            $('#debug-tab-' + tabId).addClass('active');
        });
        
        // Clear log button
        $('#wa-debug-clear').on('click', function() {
            clearDebugLog();
        });
        
        // Export log button
        $('#wa-debug-export').on('click', function() {
            exportDebugLog();
        });
        
        // Verbose logging toggle
        $('#wa-debug-verbose').on('change', function() {
            debugState.isVerbose = $(this).is(':checked');
            logDebug('Verbose logging ' + (debugState.isVerbose ? 'enabled' : 'disabled'));
        });
    }
    
    // Hook into AJAX calls to track API communication
    function hookIntoAjax() {
        // Store the original $.ajax function
        var originalAjax = $.ajax;
        
        // Override the $.ajax function
        $.ajax = function(options) {
            // Track the start time
            var requestStartTime = new Date();
            debugState.startTime = requestStartTime;
            
            // Update timer
            startTimer();
            
            // Log the request
            var requestId = 'req-' + Date.now();
            debugState.lastRequest = {
                id: requestId,
                url: options.url,
                type: options.type || 'GET',
                data: options.data || null,
                headers: options.headers || {},
                time: requestStartTime
            };
            
            logDebug('API Request started: ' + options.url, 'info');
            debugState.apiCalls.push(debugState.lastRequest);
            updateRequestsTab();
            
            // Update status
            $('#debug-status').text('Processing Request...');
            
            // Modify the success callback
            var originalSuccess = options.success;
            options.success = function(data, textStatus, jqXHR) {
                var responseTime = new Date();
                var duration = responseTime - requestStartTime;
                
                debugState.lastResponse = {
                    id: requestId,
                    data: data,
                    status: jqXHR.status,
                    statusText: textStatus,
                    time: responseTime,
                    duration: duration
                };
                
                logDebug('API Response received (' + duration + 'ms): Status ' + jqXHR.status, 'success');
                updateResponsesTab();
                
                // Update status
                $('#debug-status').text('Request Completed');
                $('#debug-api-status').text('API: Connected');
                
                // Call the original success callback
                if (originalSuccess) {
                    originalSuccess(data, textStatus, jqXHR);
                }
                
                // Stop timer
                stopTimer();
            };
            
            // Modify the error callback
            var originalError = options.error;
            options.error = function(jqXHR, textStatus, errorThrown) {
                var responseTime = new Date();
                var duration = responseTime - requestStartTime;
                
                var errorObj = {
                    id: requestId,
                    status: jqXHR.status,
                    statusText: textStatus,
                    message: errorThrown || 'Unknown error',
                    time: responseTime,
                    response: jqXHR.responseText || null,
                    duration: duration
                };
                
                debugState.lastResponse = {
                    id: requestId,
                    error: errorObj,
                    time: responseTime,
                    duration: duration
                };
                
                debugState.errors.push(errorObj);
                
                logDebug('API Error (' + duration + 'ms): ' + textStatus + ' - ' + (errorThrown || 'Unknown error'), 'error');
                updateResponsesTab();
                updateErrorsTab();
                
                // Update status
                $('#debug-status').text('Request Failed');
                $('#debug-api-status').text('API: Error');
                
                // Call the original error callback
                if (originalError) {
                    originalError(jqXHR, textStatus, errorThrown);
                }
                
                // Stop timer
                stopTimer();
            };
            
            // Call the original $.ajax with our modified options
            return originalAjax.apply($, arguments);
        };
    }
    
    // Enhance existing buttons with debugging
    function enhanceExistingButtons() {
        // Add debugging to the "Analyze Content" button in classic editor
        $('#web-analyzer-analyze').off('click').on('click', function(e) {
            e.preventDefault();
            
            var $button = $(this);
            var $status = $('#web-analyzer-status');
            var postId = $('#post_ID').val();
            
            // Clear previous status
            $status.text('');
            
            // Log the operation
            logDebug('Starting content analysis for post ID: ' + postId, 'info');
            
            // Create progress indicator
            showProgressIndicator($status, 'Analyzing content...');
            
            // Disable button during analysis
            $button.prop('disabled', true).text(webAnalyzerL10n.analyzing);
            
            // Make API request
            $.ajax({
                url: webAnalyzerAdmin.apiUrl + '/analyze',
                type: 'POST',
                beforeSend: function(xhr) {
                    xhr.setRequestHeader('X-WP-Nonce', webAnalyzerAdmin.apiNonce);
                    logDebug('Sending request with nonce to WordPress REST API', 'info');
                },
                data: JSON.stringify({
                    post_id: postId
                }),
                contentType: 'application/json',
                dataType: 'json',
                success: function(response) {
                    if (response.success) {
                        logDebug('Analysis successful, reloading page to show suggestions', 'success');
                        // Reload the metabox content to show suggestions
                        location.reload();
                    } else {
                        logDebug('Analysis failed: ' + (response.message || 'Unknown error'), 'error');
                        $status.html('<div class="notice notice-error"><p>' + (response.message || webAnalyzerL10n.analysisError) + '</p></div>');
                        hideProgressIndicator($status);
                    }
                },
                error: function(xhr, status, error) {
                    logDebug('AJAX error: ' + status + ' - ' + error, 'error');
                    $status.html('<div class="notice notice-error"><p>' + webAnalyzerL10n.analysisError + ': ' + error + '</p>' +
                                '<div class="error-details"><pre>' + xhr.responseText + '</pre></div></div>');
                    hideProgressIndicator($status);
                },
                complete: function() {
                    $button.prop('disabled', false).text(webAnalyzerL10n.analyzeContent);
                }
            });
        });
        
        // Add debugging to the "Start Analysis" button for bulk processing
        $('#web-analyzer-start-bulk').off('click').on('click', function(e) {
            e.preventDefault();
            
            var $button = $(this);
            var $status = $('#web-analyzer-bulk-status');
            var postType = $('#web_analyzer_bulk_post_type').val();
            var limit = $('#web_analyzer_bulk_limit').val();
            
            // Show the status area
            $status.show();
            
            // Log the operation
            logDebug('Starting bulk analysis for post type: ' + postType + ', limit: ' + limit, 'info');
            
            // Reset progress elements
            $('#job-status-text').text('Starting...');
            $('#job-progress').text('0%');
            $('#progress-bar-inner').css('width', '0%');
            $('#processed-count').text('0');
            $('#total-count').text('0');
            $('#time-elapsed').text('0s');
            $('#view-report-link').hide();
            
            // Disable button during analysis
            $button.prop('disabled', true).text(webAnalyzerL10n.startingAnalysis);
            
            // Make API request
            $.ajax({
                url: webAnalyzerAdmin.apiUrl + '/bulk-analyze',
                type: 'POST',
                beforeSend: function(xhr) {
                    xhr.setRequestHeader('X-WP-Nonce', webAnalyzerAdmin.apiNonce);
                    logDebug('Sending bulk analysis request to WordPress REST API', 'info');
                },
                data: JSON.stringify({
                    post_type: postType,
                    limit: limit
                }),
                contentType: 'application/json',
                dataType: 'json',
                success: function(response) {
                    if (response.success && response.job_id) {
                        logDebug('Bulk analysis job started with ID: ' + response.job_id, 'success');
                        $('#job-status-text').text('Processing');
                        $('#total-count').text(response.total_items || '0');
                        
                        // Store the job ID
                        $status.data('job-id', response.job_id);
                        
                        // Start polling for job status
                        pollJobStatus(response.job_id);
                    } else {
                        logDebug('Failed to start bulk analysis: ' + (response.message || 'Unknown error'), 'error');
                        $('#job-status-text').text('Failed to start');
                        $('#job-status-text').after('<div class="notice notice-error"><p>' + 
                                                  (response.message || 'Failed to start bulk analysis') + '</p></div>');
                    }
                },
                error: function(xhr, status, error) {
                    logDebug('AJAX error starting bulk job: ' + status + ' - ' + error, 'error');
                    $('#job-status-text').text('Error');
                    $('#job-status-text').after('<div class="notice notice-error"><p>Error: ' + error + '</p>' +
                                            '<div class="error-details"><pre>' + xhr.responseText + '</pre></div></div>');
                },
                complete: function() {
                    $button.prop('disabled', false).text(webAnalyzerL10n.startAnalysis);
                }
            });
        });
    }
    
    // Poll for job status
    function pollJobStatus(jobId) {
        if (!jobId) return;
        
        logDebug('Polling for status of job: ' + jobId, 'info');
        
        $.ajax({
            url: webAnalyzerAdmin.apiUrl + '/bulk-status/' + jobId,
            type: 'GET',
            beforeSend: function(xhr) {
                xhr.setRequestHeader('X-WP-Nonce', webAnalyzerAdmin.apiNonce);
            },
            success: function(response) {
                if (response.success) {
                    updateJobStatus(response);
                    
                    // Continue polling if job is still running
                    if (response.status === 'processing') {
                        setTimeout(function() {
                            pollJobStatus(jobId);
                        }, 3000); // Poll every 3 seconds
                    }
                } else {
                    logDebug('Error checking job status: ' + (response.message || 'Unknown error'), 'error');
                    $('#job-status-text').text('Status check failed');
                }
            },
            error: function(xhr, status, error) {
                logDebug('AJAX error checking job: ' + status + ' - ' + error, 'error');
                $('#job-status-text').text('Status check error');
                
                // Try again after a delay
                setTimeout(function() {
                    pollJobStatus(jobId);
                }, 5000); // Longer delay after error
            }
        });
    }
    
    // Update job status in the UI
    function updateJobStatus(data) {
        if (!data) return;
        
        var status = data.status || 'unknown';
        var progress = data.progress || 0;
        var processedItems = data.processed_items || 0;
        var totalItems = data.total_items || 0;
        var elapsedSeconds = data.elapsed_seconds || 0;
        
        // Update status text
        $('#job-status-text').text(status.charAt(0).toUpperCase() + status.slice(1));
        
        // Update progress bar
        $('#job-progress').text(Math.round(progress * 100) + '%');
        $('#progress-bar-inner').css('width', (progress * 100) + '%');
        
        // Update counters
        $('#processed-count').text(processedItems);
        $('#total-count').text(totalItems);
        
        // Update elapsed time
        var minutes = Math.floor(elapsedSeconds / 60);
        var seconds = Math.floor(elapsedSeconds % 60);
        $('#time-elapsed').text(minutes + 'm ' + seconds + 's');
        
        // Log the status update
        logDebug('Job status: ' + status + ', Progress: ' + Math.round(progress * 100) + '%, Items: ' + 
                processedItems + '/' + totalItems, 'info');
        
        // Show report link if completed
        if (status === 'completed' && data.report_path) {
            $('#view-report-link').attr('href', data.report_path).show();
            logDebug('Job completed successfully! Report available', 'success');
        }
        
        // Show error if failed
        if (status === 'failed') {
            logDebug('Job failed: ' + (data.error || 'Unknown error'), 'error');
            $('#job-status-text').after('<div class="notice notice-error"><p>Error: ' + 
                                      (data.error || 'Unknown error occurred during processing') + '</p></div>');
        }
    }
    
    // Show progress indicator
    function showProgressIndicator($container, message) {
        // Create a progress indicator if it doesn't exist
        if ($container.find('.wa-progress-indicator').length === 0) {
            $container.html('<div class="wa-progress-indicator">' +
                          '<div class="wa-spinner"></div>' +
                          '<div class="wa-progress-message">' + message + '</div>' +
                          '<div class="wa-progress-steps"></div>' +
                          '</div>');
        }
    }
    
    // Hide progress indicator
    function hideProgressIndicator($container) {
        $container.find('.wa-progress-indicator').remove();
    }
    
    // Update progress indicator steps
    function updateProgressStep($container, step, status) {
        var $steps = $container.find('.wa-progress-steps');
        var $step = $steps.find('[data-step="' + step + '"]');
        
        if ($step.length === 0) {
            $steps.append('<div class="wa-progress-step" data-step="' + step + '">' +
                        '<span class="step-name">' + step + ':</span> ' +
                        '<span class="step-status">' + status + '</span>' +
                        '</div>');
        } else {
            $step.find('.step-status').text(status);
        }
    }
    
    // Log a debug message
    function logDebug(message, level) {
        level = level || 'debug';
        var timestamp = new Date().toISOString();
        var $log = $('#debug-log');
        
        // Add a class based on the message level
        var logClass = 'log-' + level;
        
        // Create log entry
        var logEntry = '<div class="log-entry ' + logClass + '">' +
                     '<span class="log-time">' + timestamp.split('T')[1].substring(0, 8) + '</span> ' +
                     '<span class="log-level">[' + level.toUpperCase() + ']</span> ' +
                     '<span class="log-message">' + message + '</span>' +
                     '</div>';
        
        // Add to log
        $log.append(logEntry);
        
        // Scroll to bottom
        $log.scrollTop($log[0].scrollHeight);
        
        // Also log to console
        console.log('[Web Analyzer Debug] [' + level.toUpperCase() + '] ' + message);
    }
    
    // Clear the debug log
    function clearDebugLog() {
        $('#debug-log').empty();
        logDebug('Log cleared', 'info');
    }
    
    // Export the debug log
    function exportDebugLog() {
        var logContent = $('#debug-log').text();
        var blob = new Blob([logContent], {type: 'text/plain'});
        var url = URL.createObjectURL(blob);
        
        var a = document.createElement('a');
        a.href = url;
        a.download = 'web-analyzer-debug-log-' + new Date().toISOString().replace(/:/g, '-') + '.txt';
        a.click();
        
        URL.revokeObjectURL(url);
        logDebug('Log exported to file', 'info');
    }
    
    // Update the requests tab with current API calls
    function updateRequestsTab() {
        var $requests = $('#debug-requests');
        $requests.empty();
        
        // Sort API calls by time, newest first
        var sortedCalls = debugState.apiCalls.slice().sort(function(a, b) {
            return b.time - a.time;
        });
        
        // Add each request
        $.each(sortedCalls, function(index, request) {
            var requestTime = request.time.toISOString();
            var requestData = request.data ? JSON.stringify(request.data, null, 2) : 'No data';
            
            var requestHTML = '<div class="debug-request" data-id="' + request.id + '">' +
                            '<div class="request-header">' +
                            '<span class="request-method">' + request.type + '</span> ' +
                            '<span class="request-url">' + request.url + '</span> ' +
                            '<span class="request-time">' + requestTime + '</span>' +
                            '</div>' +
                            '<div class="request-details">' +
                            '<h4>Headers:</h4>' +
                            '<pre>' + JSON.stringify(request.headers, null, 2) + '</pre>' +
                            '<h4>Data:</h4>' +
                            '<pre>' + requestData + '</pre>' +
                            '</div>' +
                            '</div>';
            
            $requests.append(requestHTML);
        });
        
        // No requests message
        if (sortedCalls.length === 0) {
            $requests.html('<p>No API requests recorded yet.</p>');
        }
    }
    
    // Update the responses tab with current API responses
    function updateResponsesTab() {
        var $responses = $('#debug-responses');
        $responses.empty();
        
        // Get all responses from API calls
        var responses = [];
        $.each(debugState.apiCalls, function(index, call) {
            // Find matching response
            var matchingResponse = null;
            if (call.id === debugState.lastResponse?.id) {
                matchingResponse = debugState.lastResponse;
            }
            
            if (matchingResponse) {
                responses.push({
                    request: call,
                    response: matchingResponse
                });
            }
        });
        
        // Sort responses by time, newest first
        responses.sort(function(a, b) {
            return b.response.time - a.response.time;
        });
        
        // Add each response
        $.each(responses, function(index, item) {
            var request = item.request;
            var response = item.response;
            var responseTime = response.time.toISOString();
            var responseData = response.data ? JSON.stringify(response.data, null, 2) : 'No data';
            var responseClass = response.error ? 'response-error' : 'response-success';
            
            var responseHTML = '<div class="debug-response ' + responseClass + '" data-id="' + response.id + '">' +
                             '<div class="response-header">' +
                             '<span class="response-status">' + (response.error ? 'ERROR' : 'SUCCESS') + '</span> ' +
                             '<span class="response-url">' + request.url + '</span> ' +
                             '<span class="response-time">' + responseTime + '</span> ' +
                             '<span class="response-duration">' + response.duration + 'ms</span>' +
                             '</div>' +
                             '<div class="response-details">';
            
            if (response.error) {
                responseHTML += '<h4>Error:</h4>' +
                              '<pre>' + response.error.message + '</pre>' +
                              '<h4>Status:</h4>' +
                              '<pre>' + response.error.status + ' - ' + response.error.statusText + '</pre>' +
                              '<h4>Response:</h4>' +
                              '<pre>' + (response.error.response || 'No response data') + '</pre>';
            } else {
                responseHTML += '<h4>Status:</h4>' +
                              '<pre>' + response.status + ' - ' + response.statusText + '</pre>' +
                              '<h4>Data:</h4>' +
                              '<pre>' + responseData + '</pre>';
            }
            
            responseHTML += '</div></div>';
            
            $responses.append(responseHTML);
        });
        
        // No responses message
        if (responses.length === 0) {
            $responses.html('<p>No API responses recorded yet.</p>');
        }
    }
    
    // Update the errors tab with current errors
    function updateErrorsTab() {
        var $errors = $('#debug-errors');
        $errors.empty();
        
        // Sort errors by time, newest first
        var sortedErrors = debugState.errors.slice().sort(function(a, b) {
            return b.time - a.time;
        });
        
        // Add each error
        $.each(sortedErrors, function(index, error) {
            var errorTime = error.time.toISOString();
            var errorResponse = error.response ? error.response : 'No response data';
            
            var errorHTML = '<div class="debug-error" data-id="' + error.id + '">' +
                          '<div class="error-header">' +
                          '<span class="error-status">' + error.status + '</span> ' +
                          '<span class="error-message">' + error.message + '</span> ' +
                          '<span class="error-time">' + errorTime + '</span>' +
                          '</div>' +
                          '<div class="error-details">' +
                          '<h4>Status:</h4>' +
                          '<pre>' + error.status + ' - ' + error.statusText + '</pre>' +
                          '<h4>Message:</h4>' +
                          '<pre>' + error.message + '</pre>' +
                          '<h4>Response:</h4>' +
                          '<pre>' + errorResponse + '</pre>' +
                          '</div>' +
                          '</div>';
            
            $errors.append(errorHTML);
        });
        
        // No errors message
        if (sortedErrors.length === 0) {
            $errors.html('<p>No errors recorded yet.</p>');
        }
    }
    
    // Run system diagnostics
    function runSystemDiagnostics() {
        var $diagnostics = $('#debug-diagnostics');
        
        // Clear existing diagnostics
        $diagnostics.empty();
        
        // Start diagnostics
        $diagnostics.html('<div class="diagnostics-running">Running system diagnostics...</div>');
        
        // Check browser capabilities
        var browserInfo = {
            userAgent: navigator.userAgent,
            cookiesEnabled: navigator.cookieEnabled,
            language: navigator.language,
            platform: navigator.platform,
            doNotTrack: navigator.doNotTrack,
            windowSize: window.innerWidth + 'x' + window.innerHeight,
            localStorage: typeof localStorage !== 'undefined',
            sessionStorage: typeof sessionStorage !== 'undefined',
            indexedDB: typeof indexedDB !== 'undefined',
            webSockets: typeof WebSocket !== 'undefined'
        };
        
        // Check for common issues
        var issues = [];
        
        // Check for localStorage availability (needed for caching)
        if (!browserInfo.localStorage) {
            issues.push('localStorage is not available - caching may not work properly');
        }
        
        // Check for insecure context (needed for some API features)
        if (window.isSecureContext === false) {
            issues.push('Page is not running in a secure context (HTTPS) - some features may be restricted');
        }
        
        // Check for service worker support (optional but helpful)
        if (!('serviceWorker' in navigator)) {
            issues.push('Service Workers are not supported - offline functionality may be limited');
        }
        
        // Check for network connectivity
        var networkChecks = {
            online: navigator.onLine,
            apiReachable: false,
            wordPressAPIReachable: false
        };
        
        // Ping the API service
        $.ajax({
            url: 'https://web-analyzer-api.onrender.com/health',
            type: 'GET',
            timeout: 5000,
            success: function() {
                networkChecks.apiReachable = true;
                updateDiagnostics();
            },
            error: function() {
                networkChecks.apiReachable = false;
                updateDiagnostics();
            }
        });
        
        // Ping the WordPress REST API
        $.ajax({
            url: webAnalyzerAdmin.apiUrl,
            type: 'GET',
            timeout: 5000,
            success: function() {
                networkChecks.wordPressAPIReachable = true;
                updateDiagnostics();
            },
            error: function() {
                // Even a 401 error means the API is reachable
                networkChecks.wordPressAPIReachable = true;
                updateDiagnostics();
            }
        });
        
        function updateDiagnostics() {
            // Only update once both network checks are complete
            if (networkChecks.apiReachable !== undefined && networkChecks.wordPressAPIReachable !== undefined) {
                // Check for network issues
                if (!networkChecks.online) {
                    issues.push('Browser reports that it is offline - check your internet connection');
                }
                
                if (!networkChecks.apiReachable) {
                    issues.push('Cannot reach the Web Analyzer API service - check if the service is running');
                }
                
                if (!networkChecks.wordPressAPIReachable) {
                    issues.push('Cannot reach the WordPress REST API - check REST API configuration');
                }
                
                // Build diagnostics HTML
                var diagHTML = '<div class="diagnostics-results">';
                
                // Browser Information
                diagHTML += '<div class="diagnostics-section">' +
                          '<h4>Browser Information:</h4>' +
                          '<ul>';
                
                for (var key in browserInfo) {
                    diagHTML += '<li><strong>' + key + ':</strong> ' + browserInfo[key] + '</li>';
                }
                
                diagHTML += '</ul></div>';
                
                // Network Information
                diagHTML += '<div class="diagnostics-section">' +
                          '<h4>Network Information:</h4>' +
                          '<ul>' +
                          '<li><strong>Browser Online:</strong> ' + (networkChecks.online ? 'Yes' : 'No') + '</li>' +
                          '<li><strong>API Service Reachable:</strong> ' + (networkChecks.apiReachable ? 'Yes' : 'No') + '</li>' +
                          '<li><strong>WordPress API Reachable:</strong> ' + (networkChecks.wordPressAPIReachable ? 'Yes' : 'No') + '</li>' +
                          '</ul></div>';
                
                // Configuration Information
                diagHTML += '<div class="diagnostics-section">' +
                          '<h4>Plugin Configuration:</h4>' +
                          '<ul>' +
                          '<li><strong>API URL:</strong> ' + $('#web_analyzer_api_url').val() + '</li>' +
                          '<li><strong>API Key:</strong> ' + (($('#web_analyzer_api_key').val().length > 0) ? '✓ Set' : '✗ Missing') + '</li>' +
                          '<li><strong>Site ID:</strong> ' + $('#web_analyzer_site_id').val() + '</li>' +
                          '<li><strong>Automatic Analysis:</strong> ' + ($('#web_analyzer_enabled').is(':checked') ? 'Enabled' : 'Disabled') + '</li>' +
                          '<li><strong>Enhanced Analysis:</strong> ' + ($('#web_analyzer_use_enhanced').is(':checked') ? 'Enabled' : 'Disabled') + '</li>' +
                          '<li><strong>Max Suggestions:</strong> ' + $('#web_analyzer_max_suggestions').val() + '</li>' +
                          '</ul></div>';
                
                // Issues
                if (issues.length > 0) {
                    diagHTML += '<div class="diagnostics-section diagnostics-issues">' +
                              '<h4>Potential Issues:</h4>' +
                              '<ul>';
                    
                    for (var i = 0; i < issues.length; i++) {
                        diagHTML += '<li>' + issues[i] + '</li>';
                    }
                    
                    diagHTML += '</ul></div>';
                } else {
                    diagHTML += '<div class="diagnostics-section diagnostics-no-issues">' +
                              '<h4>No Issues Detected</h4>' +
                              '<p>All system diagnostics passed successfully.</p>' +
                              '</div>';
                }
                
                diagHTML += '</div>';
                
                // Update the diagnostics tab
                $diagnostics.html(diagHTML);
                
                // Log completion
                logDebug('System diagnostics completed', 'info');
            }
        }
    }
    
    // Timer functions
    var timerInterval;
    
    function startTimer() {
        if (timerInterval) clearInterval(timerInterval);
        
        var startTime = new Date();
        
        timerInterval = setInterval(function() {
            var elapsed = Math.floor((new Date() - startTime) / 1000);
            var hours = Math.floor(elapsed / 3600);
            var minutes = Math.floor((elapsed % 3600) / 60);
            var seconds = elapsed % 60;
            
            var timeString = 
                (hours < 10 ? '0' + hours : hours) + ':' +
                (minutes < 10 ? '0' + minutes : minutes) + ':' +
                (seconds < 10 ? '0' + seconds : seconds);
            
            $('#debug-timer').text(timeString);
        }, 1000);
    }
    
    function stopTimer() {
        if (timerInterval) clearInterval(timerInterval);
    }
    
    // Initialize when DOM is ready
    $(document).ready(function() {
        initDebugSystem();
    });
    
})(jQuery);
/**
 * Direct API access for Web Analyzer
 * This file provides a direct connection to the Web Analyzer API
 * without using the WordPress REST API
 */

(function($) {
    'use strict';

    // When document is ready
    $(function() {
        // Override the Start Processing button to use direct API
        $('#web-analyzer-start-bulk').off('click').on('click', function() {
            var $button = $(this);
            var $status = $('#web-analyzer-bulk-status');
            
            // Get settings from form
            // Hardcoded credentials for TheVou
            var apiUrl = 'https://web-analyzer-api.onrender.com';
            var apiKey = 'thevou_api_key_2025_03_24';
            var siteId = 'thevou';
            var postType = $('#web_analyzer_bulk_post_type').val();
            var limit = $('#web_analyzer_bulk_limit').val();
            var knowledgeMode = $('#web_analyzer_knowledge_mode').val();
            
            // Use knowledge building mode or suggestion mode
            var knowledgeBuilding = (knowledgeMode === 'build');
            
            // No need to validate settings as they are hardcoded
            // Just log a confirmation
            console.log('Using hardcoded credentials for TheVou');
            
            // Disable button during processing
            $button.prop('disabled', true).text('Processing...');
            
            // Show status area
            $status.show();
            $('#job-status-text').text('Starting...');
            $('#job-mode-text').text(knowledgeBuilding ? 'Building Knowledge Database' : 'Generating Link Suggestions');
            $('#job-progress').text('0%');
            $('#progress-bar-inner').css('width', '0%');
            $('#processed-count').text('0');
            $('#total-count').text('0');
            $('#time-elapsed').text('0s');
            $('#view-report-link').hide();
            
            // First, get posts to process
            $.ajax({
                url: ajaxurl,
                type: 'POST',
                data: {
                    action: 'web_analyzer_get_posts',
                    post_type: postType,
                    limit: limit,
                    nonce: webAnalyzerAdmin.nonce
                },
                success: function(response) {
                    if (response.success && response.posts) {
                        var posts = response.posts;
                        $('#total-count').text(posts.length);
                        
                        // Prepare content items for the API
                        var contentItems = [];
                        for (var i = 0; i < posts.length; i++) {
                            contentItems.push({
                                content: posts[i].content,
                                title: posts[i].title,
                                url: posts[i].url,
                                id: posts[i].id
                            });
                        }
                        
                        // Now call the API directly
                        $.ajax({
                            url: apiUrl + '/bulk/process',
                            type: 'POST',
                            headers: {
                                'X-API-Key': apiKey,
                                'Content-Type': 'application/json'
                            },
                            data: JSON.stringify({
                                content_items: contentItems,
                                site_id: siteId,
                                batch_size: 10,
                                knowledge_building: knowledgeBuilding
                            }),
                            success: function(apiResponse) {
                                if (apiResponse && apiResponse.job_id) {
                                    var jobId = apiResponse.job_id;
                                    
                                    // Set up interval to check job status
                                    var startTime = Date.now();
                                    var statusInterval = setInterval(function() {
                                        checkDirectJobStatus(apiUrl, apiKey, jobId, startTime, statusInterval, $button);
                                    }, 2000);
                                } else {
                                    $('#job-status-text').text('Error: Invalid API response');
                                    $button.prop('disabled', false).text('Start Processing');
                                }
                            },
                            error: function(xhr, status, error) {
                                $('#job-status-text').text('API Error: ' + (xhr.responseJSON ? xhr.responseJSON.detail : error));
                                $button.prop('disabled', false).text('Start Processing');
                            }
                        });
                    } else {
                        $('#job-status-text').text('Error: Failed to get posts');
                        $button.prop('disabled', false).text('Start Processing');
                    }
                },
                error: function(xhr, status, error) {
                    $('#job-status-text').text('Error: ' + error);
                    $button.prop('disabled', false).text('Start Processing');
                }
            });
        });
        
        // Function to check job status directly with the API
        function checkDirectJobStatus(apiUrl, apiKey, jobId, startTime, intervalId, $button) {
            $.ajax({
                url: apiUrl + '/bulk/status/' + jobId,
                type: 'GET',
                headers: {
                    'X-API-Key': apiKey
                },
                success: function(job) {
                    // Update status display
                    $('#job-status-text').text(job.status.charAt(0).toUpperCase() + job.status.slice(1));
                    $('#job-progress').text(job.progress + '%');
                    $('#progress-bar-inner').css('width', job.progress + '%');
                    $('#processed-count').text(job.processed_items);
                    
                    // Calculate elapsed time
                    var elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
                    var minutes = Math.floor(elapsedSeconds / 60);
                    var seconds = elapsedSeconds % 60;
                    $('#time-elapsed').text(minutes + 'm ' + seconds + 's');
                    
                    // Update knowledge database stats
                    if (job.knowledge_db && job.knowledge_db.current) {
                        var db = job.knowledge_db.current;
                        $('#knowledge-content-count').text(db.content_count || '0');
                        $('#knowledge-ready').text(db.ready_for_analysis ? 'Yes' : 'No');
                        $('#knowledge-minimum').text(db.minimum_required || '100');
                        
                        // Update progress bar
                        var progress = 0;
                        if (db.minimum_required > 0 && db.content_count > 0) {
                            progress = Math.min(100, Math.floor((db.content_count / db.minimum_required) * 100));
                        }
                        $('#knowledge-progress-bar').css('width', progress + '%');
                    }
                    
                    // Check if job is completed
                    if (job.status === 'completed' || job.status === 'error') {
                        clearInterval(intervalId);
                        $button.prop('disabled', false).text('Start Processing');
                    }
                },
                error: function(xhr, status, error) {
                    $('#job-status-text').text('Error: ' + (xhr.responseJSON ? xhr.responseJSON.detail : error));
                }
            });
        }
    });
})(jQuery);
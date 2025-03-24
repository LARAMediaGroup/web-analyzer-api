<?php
/**
 * Direct Bulk Processing Test
 * This file tests the bulk processing functionality directly
 */

// Output as HTML
header('Content-Type: text/html; charset=utf-8');
?>
<!DOCTYPE html>
<html>
<head>
    <title>Direct Bulk Processing Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        h1 { color: #333; }
        .success { color: green; font-weight: bold; }
        .error { color: red; font-weight: bold; }
        .info { color: blue; }
        pre { background: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }
        button { padding: 10px 20px; font-size: 16px; cursor: pointer; }
        #response { margin-top: 20px; }
    </style>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
</head>
<body>
    <h1>Direct Bulk Processing Test</h1>
    
    <div>
        <p>This tool tests the bulk processing endpoint directly using AJAX to the direct-api.php file.</p>
        <p>These are the working credentials being used:</p>
        <ul>
            <li><strong>API URL:</strong> https://web-analyzer-api.onrender.com</li>
            <li><strong>API Key:</strong> development_key_only_for_testing</li>
            <li><strong>Site ID:</strong> default</li>
        </ul>
        
        <button id="test-bulk">Test Bulk Processing</button>
        <button id="clear-results">Clear Results</button>
    </div>
    
    <div id="response"></div>
    
    <script>
        $(document).ready(function() {
            $('#test-bulk').on('click', function() {
                const $button = $(this);
                const $response = $('#response');
                
                // Show loading
                $response.html('<p class="info">Testing bulk processing...</p>');
                $button.prop('disabled', true);
                
                // Create test data
                const testData = {
                    content_items: [
                        {
                            content: 'This is a test article about fashion trends in 2023. Sustainable fashion is becoming more popular.',
                            title: 'Test Fashion Article',
                            url: 'https://thevou.com/test-fashion-article',
                            id: '12345'
                        }
                    ],
                    knowledge_building: true,
                    site_id: 'default'
                };
                
                // First test - Use direct-api.php
                $.ajax({
                    url: 'direct-api.php?op=api_request&endpoint=bulk/process&method=POST',
                    type: 'POST',
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify(testData),
                    success: function(data) {
                        $response.html('<h2>Test Results</h2>');
                        $response.append('<p class="success">Bulk processing test successful!</p>');
                        $response.append('<pre>' + JSON.stringify(data, null, 2) + '</pre>');
                        
                        // If we got a job ID, check its status
                        if (data && data.job_id) {
                            $response.append('<h3>Job ID: ' + data.job_id + '</h3>');
                            $response.append('<p>Checking job status in 2 seconds...</p>');
                            
                            setTimeout(function() {
                                checkJobStatus(data.job_id);
                            }, 2000);
                        }
                    },
                    error: function(xhr, status, error) {
                        $response.html('<h2>Test Results</h2>');
                        $response.append('<p class="error">Bulk processing test failed!</p>');
                        
                        if (xhr.responseJSON) {
                            $response.append('<pre>' + JSON.stringify(xhr.responseJSON, null, 2) + '</pre>');
                        } else {
                            $response.append('<p>Error: ' + error + '</p>');
                            $response.append('<p>Status: ' + status + '</p>');
                            $response.append('<p>Response Text: ' + xhr.responseText + '</p>');
                        }
                    },
                    complete: function() {
                        $button.prop('disabled', false);
                    }
                });
            });
            
            // Function to check job status
            function checkJobStatus(jobId) {
                const $response = $('#response');
                
                $response.append('<p class="info">Checking job status...</p>');
                
                $.ajax({
                    url: 'direct-api.php?op=api_request&endpoint=bulk/jobs/' + jobId + '&method=GET',
                    type: 'GET',
                    dataType: 'json',
                    success: function(data) {
                        $response.append('<p class="success">Job status check successful!</p>');
                        $response.append('<pre>' + JSON.stringify(data, null, 2) + '</pre>');
                    },
                    error: function(xhr, status, error) {
                        $response.append('<p class="error">Job status check failed!</p>');
                        
                        if (xhr.responseJSON) {
                            $response.append('<pre>' + JSON.stringify(xhr.responseJSON, null, 2) + '</pre>');
                        } else {
                            $response.append('<p>Error: ' + error + '</p>');
                            $response.append('<p>Status: ' + status + '</p>');
                            $response.append('<p>Response Text: ' + xhr.responseText + '</p>');
                        }
                    }
                });
            }
            
            // Clear results button
            $('#clear-results').on('click', function() {
                $('#response').empty();
            });
        });
    </script>
</body>
</html> 
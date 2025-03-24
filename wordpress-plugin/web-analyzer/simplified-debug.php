<?php
/**
 * Simplified Debug Tool for Web Analyzer
 */

// Load WordPress environment
define('WP_USE_THEMES', false);
require_once('../../../../wp-load.php');

// Set error reporting
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Output as HTML
header('Content-Type: text/html; charset=utf-8');
?>
<!DOCTYPE html>
<html>
<head>
    <title>Simplified Debug Tool</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        h1 { color: #333; }
        .success { color: green; font-weight: bold; }
        .error { color: red; font-weight: bold; }
        pre { background: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>Simplified Debug Tool</h1>
    
    <h2>Basic PHP Check</h2>
    <p>PHP version: <?php echo phpversion(); ?></p>
    
    <?php
    // API credentials
    $api_url = 'https://web-analyzer-api.onrender.com';
    $api_key = 'development_key_only_for_testing';
    $site_id = 'default';
    
    echo "<h2>API Credentials</h2>";
    echo "<p><strong>API URL:</strong> " . htmlspecialchars($api_url) . "</p>";
    echo "<p><strong>API Key:</strong> " . htmlspecialchars($api_key) . "</p>";
    echo "<p><strong>Site ID:</strong> " . htmlspecialchars($site_id) . "</p>";
    
    // Test 1: Health endpoint
    echo "<h2>Health Endpoint Test</h2>";
    
    try {
        $response = wp_remote_get(
            "$api_url/health",
            [
                'timeout' => 15,
                'headers' => [
                    'X-API-Key' => $api_key
                ]
            ]
        );
        
        if (is_wp_error($response)) {
            echo "<p class='error'>Error: " . $response->get_error_message() . "</p>";
        } else {
            $status_code = wp_remote_retrieve_response_code($response);
            $body = wp_remote_retrieve_body($response);
            
            echo "<p><strong>Status code:</strong> $status_code</p>";
            echo "<pre>" . htmlspecialchars($body) . "</pre>";
            
            if ($status_code == 200) {
                echo "<p class='success'>Health endpoint test successful!</p>";
            } else {
                echo "<p class='error'>Health endpoint test failed.</p>";
            }
        }
    } catch (Exception $e) {
        echo "<p class='error'>Error: " . $e->getMessage() . "</p>";
    }
    
    // Test 2: Bulk endpoint
    echo "<h2>Bulk Processing Test</h2>";
    
    try {
        $data = [
            'content_items' => [
                [
                    'content' => 'Test content about fashion trends',
                    'title' => 'Test Title',
                    'url' => 'https://thevou.com/test',
                    'id' => '12345'
                ]
            ],
            'knowledge_building' => true,
            'site_id' => $site_id
        ];
        
        $response = wp_remote_post(
            "$api_url/bulk/process",
            [
                'timeout' => 30,
                'headers' => [
                    'X-API-Key' => $api_key,
                    'Content-Type' => 'application/json'
                ],
                'body' => json_encode($data)
            ]
        );
        
        if (is_wp_error($response)) {
            echo "<p class='error'>Error: " . $response->get_error_message() . "</p>";
        } else {
            $status_code = wp_remote_retrieve_response_code($response);
            $body = wp_remote_retrieve_body($response);
            
            echo "<p><strong>Status code:</strong> $status_code</p>";
            echo "<pre>" . htmlspecialchars($body) . "</pre>";
            
            if ($status_code == 200) {
                echo "<p class='success'>Bulk processing test successful!</p>";
            } else {
                echo "<p class='error'>Bulk processing test failed.</p>";
            }
        }
    } catch (Exception $e) {
        echo "<p class='error'>Error: " . $e->getMessage() . "</p>";
    }
    ?>
    
    <h2>WordPress Test</h2>
    <p>WordPress version: <?php echo get_bloginfo('version'); ?></p>
    <p>Plugin version: <?php echo defined('WEB_ANALYZER_VERSION') ? WEB_ANALYZER_VERSION : 'Not defined'; ?></p>
    
</body>
</html> 
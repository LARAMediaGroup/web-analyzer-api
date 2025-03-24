<?php
/**
 * API Credential Test for Web Analyzer
 * 
 * This file tests the API credentials to verify they work correctly.
 * Upload this file to your WordPress plugins/web-analyzer/ directory
 * and access it via: https://your-site.com/wp-content/plugins/web-analyzer/test-credential.php
 */

// Security headers to prevent caching
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
header('Pragma: no-cache');
header('Expires: 0');

// Output as HTML
header('Content-Type: text/html; charset=utf-8');

echo '<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Analyzer API Credential Test</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; }
        .success { color: green; font-weight: bold; }
        .error { color: red; font-weight: bold; }
        .info { color: blue; }
        pre { background: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>Web Analyzer API Credential Test</h1>';

// Set API Information - Hardcoded for testing
$api_url = 'https://web-analyzer-api.onrender.com';
$api_key = 'development_key_only_for_testing';
$site_id = 'default';

// Display API Information
echo "<h3>API Information</h3>";
echo "<p><strong>API URL:</strong> $api_url</p>";
echo "<p><strong>API Key:</strong> $api_key</p>";
echo "<p><strong>Site ID:</strong> $site_id</p>";

// Test 1: Health endpoint (no auth required)
echo "<h2>Test 1: Health Endpoint</h2>";
echo "<p>Testing health endpoint...</p>";

$health_url = $api_url . '/health';
$response = wp_remote_get($health_url, [
    'timeout' => 15
]);

if (is_wp_error($response)) {
    echo "<p class='error'>Error: " . $response->get_error_message() . "</p>";
} else {
    $status_code = wp_remote_retrieve_response_code($response);
    $body = wp_remote_retrieve_body($response);
    
    if ($status_code == 200) {
        echo "<p class='success'>Health endpoint is working! Status: $status_code</p>";
        echo "<pre>" . htmlspecialchars($body) . "</pre>";
    } else {
        echo "<p class='error'>Health endpoint failed with status $status_code</p>";
        echo "<pre>" . htmlspecialchars($body) . "</pre>";
    }
}

// Test 2: Auth with API key
echo "<h2>Test 2: API Key Authentication</h2>";
echo "<p>Testing authentication with API key...</p>";

$auth_url = $api_url . '/bulk/jobs';
$response = wp_remote_get($auth_url, [
    'timeout' => 15,
    'headers' => [
        'X-API-Key' => $api_key
    ]
]);

if (is_wp_error($response)) {
    echo "<p class='error'>Error: " . $response->get_error_message() . "</p>";
} else {
    $status_code = wp_remote_retrieve_response_code($response);
    $body = wp_remote_retrieve_body($response);
    
    if ($status_code == 200) {
        echo "<p class='success'>API key authentication successful! Status: $status_code</p>";
        echo "<pre>" . htmlspecialchars($body) . "</pre>";
    } else {
        echo "<p class='error'>API key authentication failed with status $status_code</p>";
        echo "<pre>" . htmlspecialchars($body) . "</pre>";
    }
}

// Test 3: Site configuration
echo "<h2>Test 3: Site Configuration</h2>";
echo "<p>Testing site configuration...</p>";

$test_data = [
    'content' => 'This is a test content',
    'title' => 'Test Title',
    'site_id' => $site_id
];

$response = wp_remote_post($api_url . '/analyze/content', [
    'timeout' => 30,
    'headers' => [
        'X-API-Key' => $api_key,
        'Content-Type' => 'application/json'
    ],
    'body' => json_encode($test_data)
]);

if (is_wp_error($response)) {
    echo "<p class='error'>Error: " . $response->get_error_message() . "</p>";
} else {
    $status_code = wp_remote_retrieve_response_code($response);
    $body = wp_remote_retrieve_body($response);
    
    // Either 200 or 422 is OK (422 means validation error with the content, which is expected)
    if ($status_code == 200 || $status_code == 422) {
        echo "<p class='success'>Site configuration is valid! Status: $status_code</p>";
        echo "<pre>" . htmlspecialchars($body) . "</pre>";
    } else {
        echo "<p class='error'>Site configuration failed with status $status_code</p>";
        echo "<pre>" . htmlspecialchars($body) . "</pre>";
    }
}

// Test alternate API key
$alternate_key = "u1HG8J0uUenblA7KJuUhVlTX";
echo "<h2>Test with Alternate API Key</h2>";
echo "<p>Testing authentication with alternate API key ($alternate_key)...</p>";

$auth_url = $api_url . '/bulk/jobs';
$response = wp_remote_get($auth_url, [
    'timeout' => 15,
    'headers' => [
        'X-API-Key' => $alternate_key
    ]
]);

if (is_wp_error($response)) {
    echo "<p class='error'>Error: " . $response->get_error_message() . "</p>";
} else {
    $status_code = wp_remote_retrieve_response_code($response);
    $body = wp_remote_retrieve_body($response);
    
    if ($status_code == 200) {
        echo "<p class='success'>Alternate API key authentication successful! Status: $status_code</p>";
        echo "<pre>" . htmlspecialchars($body) . "</pre>";
    } else {
        echo "<p class='error'>Alternate API key authentication failed with status $status_code</p>";
        echo "<pre>" . htmlspecialchars($body) . "</pre>";
    }
}

// Test with latest WordPress settings
$wp_api_url = get_option('web_analyzer_api_url', '');
$wp_api_key = get_option('web_analyzer_api_key', '');
$wp_site_id = get_option('web_analyzer_site_id', '');

echo "<h2>WordPress Settings</h2>";
echo "<p><strong>WordPress API URL:</strong> " . ($wp_api_url ? $wp_api_url : 'Not set') . "</p>";
echo "<p><strong>WordPress API Key:</strong> " . ($wp_api_key ? $wp_api_key : 'Not set') . "</p>";
echo "<p><strong>WordPress Site ID:</strong> " . ($wp_site_id ? $wp_site_id : 'Not set') . "</p>";

if ($wp_api_url && $wp_api_key) {
    echo "<h2>Test with WordPress Settings</h2>";
    echo "<p>Testing authentication with WordPress settings...</p>";
    
    $auth_url = $wp_api_url . '/bulk/jobs';
    $response = wp_remote_get($auth_url, [
        'timeout' => 15,
        'headers' => [
            'X-API-Key' => $wp_api_key
        ]
    ]);
    
    if (is_wp_error($response)) {
        echo "<p class='error'>Error: " . $response->get_error_message() . "</p>";
    } else {
        $status_code = wp_remote_retrieve_response_code($response);
        $body = wp_remote_retrieve_body($response);
        
        if ($status_code == 200) {
            echo "<p class='success'>WordPress settings authentication successful! Status: $status_code</p>";
            echo "<pre>" . htmlspecialchars($body) . "</pre>";
        } else {
            echo "<p class='error'>WordPress settings authentication failed with status $status_code</p>";
            echo "<pre>" . htmlspecialchars($body) . "</pre>";
        }
    }
}

echo '</body>
</html>';
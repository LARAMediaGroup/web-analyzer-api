<?php
// Minimal debug file - no WordPress dependencies
header('Content-Type: text/plain');
echo "PHP is working correctly\n\n";

// Set error reporting
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Working credentials
$api_url = 'https://web-analyzer-api.onrender.com';
$api_key = 'development_key_only_for_testing';
$site_id = 'default';

echo "Testing with these credentials:\n";
echo "API URL: $api_url\n";
echo "API Key: $api_key\n";
echo "Site ID: $site_id\n\n";

// Basic function test
function test_api() {
    global $api_url, $api_key;
    
    echo "Testing health endpoint...\n";
    
    // Use curl for API request (no WordPress dependencies)
    $ch = curl_init($api_url . '/health');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'X-API-Key: ' . $api_key
    ]);
    
    $response = curl_exec($ch);
    $status_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    echo "Status Code: $status_code\n";
    echo "Response: $response\n\n";
    
    // Test bulk endpoint
    echo "Testing bulk endpoint...\n";
    
    $data = [
        'content_items' => [
            [
                'content' => 'Test content about fashion',
                'title' => 'Test Title',
                'url' => 'https://thevou.com/test',
                'id' => '12345'
            ]
        ],
        'knowledge_building' => true,
        'site_id' => $site_id
    ];
    
    $ch = curl_init($api_url . '/bulk/process');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 15);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'X-API-Key: ' . $api_key,
        'Content-Type: application/json'
    ]);
    
    $response = curl_exec($ch);
    $status_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    echo "Status Code: $status_code\n";
    echo "Response: $response\n";
}

// Simple error handling
try {
    test_api();
    echo "\nDiagnostic completed successfully";
} catch (Exception $e) {
    echo "\nError: " . $e->getMessage();
} 
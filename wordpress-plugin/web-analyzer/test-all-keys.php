<?php
// Test file to try all known API keys
header('Content-Type: text/plain');
echo "Testing all known API keys against bulk endpoint\n\n";

// API endpoint
$api_url = 'https://web-analyzer-api.onrender.com';
$site_id = 'thevou';

// All known API keys to test
$api_keys = [
    'New Key' => 'p6fHDUXqGRgV4SNIXrxLG-Z01TVXVjtIk5ODiMmj6F8',
    'Development Key' => 'development_key_only_for_testing',
    'TheVou Dev Key' => 'development_key_thevou',
    'Old Key' => 'j75x+z5imUKNHIyLk7zTNSTF/juUlwf4',
    'Previous Key' => 'u1HG8J0uUenblA7KJuUhVlTX'
];

echo "API URL: $api_url\n";
echo "Site ID: $site_id\n\n";

// Test each key against health endpoint and bulk endpoint
foreach ($api_keys as $key_name => $api_key) {
    echo "=== Testing Key: $key_name ===\n";
    echo "Key value: $api_key\n\n";
    
    // Test health endpoint
    echo "Testing health endpoint...\n";
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
    
    // Test bulk endpoint with minimal data
    echo "Testing bulk/process endpoint...\n";
    $data = [
        'content_items' => [
            [
                'content' => 'This is a test article about fashion.',
                'title' => 'Test Article',
                'url' => 'https://thevou.com/test-article',
                'id' => '12345'
            ]
        ],
        'knowledge_building' => true,
        'site_id' => $site_id
    ];
    
    $ch = curl_init($api_url . '/bulk/process');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
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
    echo "Response: $response\n\n";
    
    // If we got an error, also try with a different site_id
    if ($status_code >= 400) {
        $alternate_site_ids = ['default', 'thevou_new', 'testsite'];
        foreach ($alternate_site_ids as $alt_site_id) {
            echo "Trying with alternate site_id: $alt_site_id\n";
            $data['site_id'] = $alt_site_id;
            
            $ch = curl_init($api_url . '/bulk/process');
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_TIMEOUT, 30);
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
            echo "Response: $response\n\n";
            
            // If we got a successful response, stop trying
            if ($status_code < 400) {
                break;
            }
        }
    }
    
    echo "\n\n";
}

echo "All tests complete."; 
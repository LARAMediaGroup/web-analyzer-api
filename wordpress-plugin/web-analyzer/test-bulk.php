<?php
// Test file for bulk processing API
header('Content-Type: text/plain');
echo "Testing bulk processing API\n\n";

// API credentials
$api_url = 'https://web-analyzer-api.onrender.com';
$api_key = 'p6fHDUXqGRgV4SNIXrxLG-Z01TVXVjtIk5ODiMmj6F8';
$site_id = 'thevou';

echo "Using API: $api_url\n";
echo "Using key: $api_key\n";
echo "Site ID: $site_id\n\n";

// Create a simple test payload
$data = [
    'content_items' => [
        [
            'content' => 'This is a test article about fashion trends in 2023. Sustainable fashion is becoming more important.',
            'title' => 'Test Fashion Article',
            'url' => 'https://thevou.com/test-fashion-article',
            'id' => '12345'
        ]
    ],
    'knowledge_building' => true,
    'site_id' => $site_id
];

// Make the API request
$ch = curl_init($api_url . '/bulk/process');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'X-API-Key: ' . $api_key,
    'Content-Type: application/json'
]);

echo "Sending request to /bulk/process...\n";
$response = curl_exec($ch);
$status_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

echo "Status Code: $status_code\n";
echo "Response: $response\n\n";

// If we get a job ID, check its status
if ($status_code == 202 && !empty($response)) {
    $response_data = json_decode($response, true);
    if (isset($response_data['job_id'])) {
        $job_id = $response_data['job_id'];
        echo "Got job ID: $job_id\n";
        echo "Checking job status...\n\n";
        
        // Check job status
        $ch = curl_init($api_url . '/bulk/jobs/' . $job_id);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 10);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'X-API-Key: ' . $api_key
        ]);
        
        $response = curl_exec($ch);
        $status_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        echo "Job Status Code: $status_code\n";
        echo "Job Status Response: $response\n";
    }
}

// Let's also check the knowledge database status
echo "\nChecking Knowledge Database Status...\n";

$ch = curl_init($api_url . '/knowledge');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 10);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'X-API-Key: ' . $api_key
]);

$response = curl_exec($ch);
$status_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

echo "Knowledge DB Status Code: $status_code\n";
echo "Knowledge DB Response: $response\n"; 
<?php
// Simple API test - minimal version
header('Content-Type: text/plain');
echo "PHP is working correctly\n\n";

// API credentials
$api_url = 'https://web-analyzer-api.onrender.com';
$api_key = 'p6fHDUXqGRgV4SNIXrxLG-Z01TVXVjtIk5ODiMmj6F8';

echo "Testing connection to: $api_url\n";
echo "Using API key: $api_key\n\n";

// Test with curl
$ch = curl_init($api_url . '/health');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 10);
curl_setopt($ch, CURLOPT_HTTPHEADER, ['X-API-Key: ' . $api_key]);
$response = curl_exec($ch);
$status_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

echo "Status Code: $status_code\n";
echo "Response: $response\n"; 
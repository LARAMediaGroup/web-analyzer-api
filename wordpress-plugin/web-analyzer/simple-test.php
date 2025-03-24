<?php
// Simple API test script
header('Content-Type: text/html');
?>
<!DOCTYPE html>
<html>
<head>
    <title>Simple API Test</title>
</head>
<body>
    <h1>Simple API Test</h1>
    
    <?php
    // API credentials
    $api_url = 'https://web-analyzer-api.onrender.com';
    $api_key = 'p6fHDUXqGRgV4SNIXrxLG-Z01TVXVjtIk5ODiMmj6F8';
    $site_id = 'thevou';
    
    echo "<p>Testing API with these credentials:</p>";
    echo "<ul>";
    echo "<li>API URL: " . htmlspecialchars($api_url) . "</li>";
    echo "<li>API Key: " . htmlspecialchars($api_key) . "</li>";
    echo "<li>Site ID: " . htmlspecialchars($site_id) . "</li>";
    echo "</ul>";
    
    // Test health endpoint
    echo "<h2>Health Endpoint Test</h2>";
    
    try {
        $ch = curl_init($api_url . '/health');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 10);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'X-API-Key: ' . $api_key
        ]);
        
        $response = curl_exec($ch);
        $status_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        echo "<p>Status Code: " . $status_code . "</p>";
        echo "<p>Response: " . htmlspecialchars($response) . "</p>";
        
        if ($status_code == 200) {
            echo "<p style='color:green;font-weight:bold;'>Health endpoint test successful!</p>";
        } else {
            echo "<p style='color:red;font-weight:bold;'>Health endpoint test failed.</p>";
        }
    } catch (Exception $e) {
        echo "<p style='color:red;'>Error: " . htmlspecialchars($e->getMessage()) . "</p>";
    }
    ?>
</body>
</html> 
<?php
/**
 * Fired when the plugin is uninstalled.
 *
 * @since      1.0.0
 * @package    Web_Analyzer
 */

// If uninstall not called from WordPress, exit.
if (!defined('WP_UNINSTALL_PLUGIN')) {
    exit;
}

// Delete options
delete_option('web_analyzer_api_url');
delete_option('web_analyzer_api_key');
delete_option('web_analyzer_site_id');
delete_option('web_analyzer_enabled');
delete_option('web_analyzer_max_suggestions');
delete_option('web_analyzer_version');

// Drop custom tables
global $wpdb;
$wpdb->query("DROP TABLE IF EXISTS {$wpdb->prefix}web_analyzer_suggestions");
$wpdb->query("DROP TABLE IF EXISTS {$wpdb->prefix}web_analyzer_analytics");
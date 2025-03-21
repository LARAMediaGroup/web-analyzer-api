<?php
/**
 * Fired during plugin activation.
 *
 * This class defines all code necessary to run during the plugin's activation.
 *
 * @since      1.0.0
 * @package    Web_Analyzer
 * @subpackage Web_Analyzer/includes
 */

class Web_Analyzer_Activator {

    /**
     * Initialize plugin settings and tables on activation.
     *
     * @since    1.0.0
     */
    public static function activate() {
        // Add default settings
        add_option('web_analyzer_api_url', '');
        add_option('web_analyzer_api_key', '');
        add_option('web_analyzer_site_id', '');
        add_option('web_analyzer_enabled', true);
        add_option('web_analyzer_max_suggestions', 5);
        
        // Create database tables for storing analytics
        self::create_tables();
        
        // Set plugin version
        update_option('web_analyzer_version', WEB_ANALYZER_VERSION);
        
        // Schedule weekly cleanup
        if (!wp_next_scheduled('web_analyzer_weekly_cleanup')) {
            wp_schedule_event(time(), 'weekly', 'web_analyzer_weekly_cleanup');
        }
    }
    
    /**
     * Create database tables for storing analytics data.
     *
     * @since    1.0.0
     */
    private static function create_tables() {
        global $wpdb;
        
        $charset_collate = $wpdb->get_charset_collate();
        
        // Table for storing link suggestions
        $table_name = $wpdb->prefix . 'web_analyzer_suggestions';
        $sql = "CREATE TABLE $table_name (
            id mediumint(9) NOT NULL AUTO_INCREMENT,
            post_id mediumint(9) NOT NULL,
            target_url varchar(2083) NOT NULL,
            anchor_text text NOT NULL,
            context text NOT NULL,
            confidence float NOT NULL,
            paragraph_index int NOT NULL,
            created_at datetime DEFAULT CURRENT_TIMESTAMP NOT NULL,
            applied tinyint(1) DEFAULT 0 NOT NULL,
            PRIMARY KEY (id)
        ) $charset_collate;";
        
        // Table for storing suggestion analytics
        $table_name_analytics = $wpdb->prefix . 'web_analyzer_analytics';
        $sql_analytics = "CREATE TABLE $table_name_analytics (
            id mediumint(9) NOT NULL AUTO_INCREMENT,
            suggestion_id mediumint(9) NOT NULL,
            clicks int DEFAULT 0 NOT NULL,
            impressions int DEFAULT 0 NOT NULL,
            last_clicked datetime DEFAULT NULL,
            last_updated datetime DEFAULT CURRENT_TIMESTAMP NOT NULL,
            PRIMARY KEY (id),
            KEY suggestion_id (suggestion_id)
        ) $charset_collate;";
        
        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql);
        dbDelta($sql_analytics);
    }
}
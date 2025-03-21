<?php
/**
 * Fired during plugin deactivation.
 *
 * This class defines all code necessary to run during the plugin's deactivation.
 *
 * @since      1.0.0
 * @package    Web_Analyzer
 * @subpackage Web_Analyzer/includes
 */

class Web_Analyzer_Deactivator {

    /**
     * Clean up when plugin is deactivated.
     *
     * @since    1.0.0
     */
    public static function deactivate() {
        // Clear scheduled events
        wp_clear_scheduled_hook('web_analyzer_weekly_cleanup');
        
        // We don't delete options or tables on deactivation
        // This ensures settings and data persist if plugin is reactivated
        // For complete removal, the uninstall.php file would handle deletion
    }
}
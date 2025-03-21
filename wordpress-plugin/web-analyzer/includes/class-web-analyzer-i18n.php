<?php
/**
 * Define the internationalization functionality.
 *
 * @since      1.0.0
 * @package    Web_Analyzer
 * @subpackage Web_Analyzer/includes
 */

class Web_Analyzer_i18n {

    /**
     * Load the plugin text domain for translation.
     *
     * @since    1.0.0
     */
    public function load_plugin_textdomain() {
        load_plugin_textdomain(
            'web-analyzer',
            false,
            dirname(dirname(plugin_basename(__FILE__))) . '/languages/'
        );
    }
}
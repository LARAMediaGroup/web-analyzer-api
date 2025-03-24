<?php
/**
 * Provide a admin area view for the plugin
 *
 * This file is used to markup the admin-facing aspects of the plugin.
 *
 * @since      1.0.0
 * @package    Web_Analyzer
 * @subpackage Web_Analyzer/admin/partials
 */

// Ensure this file is being included by a parent file
if (!defined('WPINC')) {
    die;
}
?>

<div class="wrap">
    <h1><?php echo esc_html(get_admin_page_title()); ?></h1>
    
    <div class="web-analyzer-admin-header">
        <div class="web-analyzer-header-info">
            <h2><?php _e('Web Analyzer for Internal Linking', 'web-analyzer'); ?></h2>
            <p><?php _e('Configure your connection to the Web Analyzer API for intelligent internal linking suggestions.', 'web-analyzer'); ?></p>
        </div>
    </div>
    
    <div class="web-analyzer-admin-content">
        <div class="web-analyzer-settings-container">
            <form method="post" action="options.php">
                <?php
                settings_fields($this->plugin_name);
                do_settings_sections($this->plugin_name);
                ?>
                
                <div class="web-analyzer-settings-section">
                    <h2><?php _e('API Configuration', 'web-analyzer'); ?></h2>
                    <p><?php _e('Enter your Web Analyzer API credentials to connect to the service.', 'web-analyzer'); ?></p>
                    
                    <table class="form-table">
                        <tbody>
                            <tr>
                                <th scope="row">
                                    <label for="web_analyzer_api_url"><?php _e('API URL', 'web-analyzer'); ?></label>
                                </th>
                                <td>
                                    <input type="url" id="web_analyzer_api_url" name="web_analyzer_api_url" 
                                           class="regular-text" 
                                           value="<?php echo esc_attr(get_option('web_analyzer_api_url')); ?>" 
                                           placeholder="https://api.example.com" />
                                    <p class="description">
                                        <?php _e('The URL of the Web Analyzer API.', 'web-analyzer'); ?>
                                    </p>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row">
                                    <label for="web_analyzer_api_key"><?php _e('API Key', 'web-analyzer'); ?></label>
                                </th>
                                <td>
                                    <input type="password" id="web_analyzer_api_key" name="web_analyzer_api_key" 
                                           class="regular-text" 
                                           value="<?php echo esc_attr(get_option('web_analyzer_api_key')); ?>" />
                                    <p class="description">
                                        <?php _e('Your API key for authentication.', 'web-analyzer'); ?>
                                    </p>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row">
                                    <label for="web_analyzer_site_id"><?php _e('Site ID', 'web-analyzer'); ?></label>
                                </th>
                                <td>
                                    <input type="text" id="web_analyzer_site_id" name="web_analyzer_site_id" 
                                           class="regular-text" 
                                           value="<?php echo esc_attr(get_option('web_analyzer_site_id')); ?>" 
                                           placeholder="thevou" />
                                    <p class="description">
                                        <?php _e('Your site identifier.', 'web-analyzer'); ?>
                                    </p>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <div class="web-analyzer-settings-section">
                    <h2><?php _e('Plugin Settings', 'web-analyzer'); ?></h2>
                    <p><?php _e('Configure how the Web Analyzer works with your content.', 'web-analyzer'); ?></p>
                    
                    <table class="form-table">
                        <tbody>
                            <tr>
                                <th scope="row">
                                    <label for="web_analyzer_enabled"><?php _e('Enable Automatic Analysis', 'web-analyzer'); ?></label>
                                </th>
                                <td>
                                    <input type="checkbox" id="web_analyzer_enabled" name="web_analyzer_enabled" 
                                           value="1" <?php checked(get_option('web_analyzer_enabled', true)); ?> />
                                    <p class="description">
                                        <?php _e('Automatically analyze content when saving posts.', 'web-analyzer'); ?>
                                    </p>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row">
                                    <label for="web_analyzer_use_enhanced"><?php _e('Use Enhanced Analysis', 'web-analyzer'); ?></label>
                                </th>
                                <td>
                                    <input type="checkbox" id="web_analyzer_use_enhanced" name="web_analyzer_use_enhanced" 
                                           value="1" <?php checked(get_option('web_analyzer_use_enhanced', false)); ?> />
                                    <p class="description">
                                        <?php _e('Use advanced analysis with improved entity recognition and semantic understanding.', 'web-analyzer'); ?>
                                    </p>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row">
                                    <label for="web_analyzer_max_suggestions"><?php _e('Maximum Suggestions', 'web-analyzer'); ?></label>
                                </th>
                                <td>
                                    <input type="number" id="web_analyzer_max_suggestions" name="web_analyzer_max_suggestions" 
                                           class="small-text" 
                                           value="<?php echo esc_attr(get_option('web_analyzer_max_suggestions', 5)); ?>" 
                                           min="1" max="20" />
                                    <p class="description">
                                        <?php _e('Maximum number of link suggestions to show in the editor.', 'web-analyzer'); ?>
                                    </p>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <div class="web-analyzer-settings-section">
                    <h2><?php _e('Bulk Processing', 'web-analyzer'); ?></h2>
                    <p><?php _e('Analyze multiple posts at once to generate link suggestions.', 'web-analyzer'); ?></p>
                    
                    <table class="form-table">
                        <tbody>
                            <tr>
                                <th scope="row">
                                    <label for="web_analyzer_bulk_post_type"><?php _e('Post Type', 'web-analyzer'); ?></label>
                                </th>
                                <td>
                                    <select id="web_analyzer_bulk_post_type" name="web_analyzer_bulk_post_type">
                                        <?php
                                        $post_types = get_post_types(array('public' => true), 'objects');
                                        $selected_post_type = get_option('web_analyzer_bulk_post_type', 'post');
                                        
                                        foreach ($post_types as $post_type) {
                                            echo '<option value="' . esc_attr($post_type->name) . '" ' . selected($selected_post_type, $post_type->name, false) . '>' . esc_html($post_type->label) . '</option>';
                                        }
                                        ?>
                                    </select>
                                    <p class="description">
                                        <?php _e('Post type to analyze in bulk.', 'web-analyzer'); ?>
                                    </p>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row">
                                    <label for="web_analyzer_bulk_limit"><?php _e('Limit', 'web-analyzer'); ?></label>
                                </th>
                                <td>
                                    <input type="number" id="web_analyzer_bulk_limit" name="web_analyzer_bulk_limit" 
                                           class="small-text" 
                                           value="<?php echo esc_attr(get_option('web_analyzer_bulk_limit', 10)); ?>" 
                                           min="1" max="100" />
                                    <p class="description">
                                        <?php _e('Maximum number of posts to analyze in a single batch (1-100).', 'web-analyzer'); ?>
                                    </p>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row">
                                    <label for="web_analyzer_knowledge_mode"><?php _e('Knowledge Database Mode', 'web-analyzer'); ?></label>
                                </th>
                                <td>
                                    <select id="web_analyzer_knowledge_mode" name="web_analyzer_knowledge_mode">
                                        <option value="suggest" <?php selected(get_option('web_analyzer_knowledge_mode', 'suggest'), 'suggest'); ?>>
                                            <?php _e('Generate Link Suggestions', 'web-analyzer'); ?>
                                        </option>
                                        <option value="build" <?php selected(get_option('web_analyzer_knowledge_mode', 'suggest'), 'build'); ?>>
                                            <?php _e('Build Knowledge Database', 'web-analyzer'); ?>
                                        </option>
                                    </select>
                                    <p class="description">
                                        <?php _e('Choose whether to build the knowledge database or generate link suggestions.', 'web-analyzer'); ?>
                                    </p>
                                    <div id="knowledge-db-info" style="margin-top: 10px; background: #f8f9fa; padding: 10px; border-left: 4px solid #2271b1;">
                                        <h4 style="margin-top: 0;"><?php _e('Knowledge Database Status', 'web-analyzer'); ?></h4>
                                        <div id="knowledge-db-loading"><?php _e('Loading...', 'web-analyzer'); ?></div>
                                        <div id="knowledge-db-status" style="display: none;">
                                            <p><strong><?php _e('Content Items:', 'web-analyzer'); ?></strong> <span id="knowledge-content-count">0</span></p>
                                            <p><strong><?php _e('Ready for Analysis:', 'web-analyzer'); ?></strong> <span id="knowledge-ready">No</span></p>
                                            <p><strong><?php _e('Minimum Required:', 'web-analyzer'); ?></strong> <span id="knowledge-minimum">100</span> <?php _e('items', 'web-analyzer'); ?></p>
                                            <div class="progress-bar" style="background: #f0f0f0; height: 10px; width: 100%; border-radius: 3px; margin: 5px 0;">
                                                <div id="knowledge-progress-bar" style="background: #2271b1; height: 100%; width: 0%; border-radius: 3px;"></div>
                                            </div>
                                            <p><em><?php _e('Note: You need to process at least the minimum required content items in "Build Knowledge Database" mode before suggestions will work.', 'web-analyzer'); ?></em></p>
                                        </div>
                                        <button type="button" id="web-analyzer-refresh-knowledge" class="button button-secondary" style="margin-top: 10px;">
                                            <?php _e('Refresh Status', 'web-analyzer'); ?>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                            
                            <tr>
                                <th scope="row">
                                    <?php _e('Start Bulk Analysis', 'web-analyzer'); ?>
                                </th>
                                <td>
                                    <button type="button" id="web-analyzer-start-bulk" class="button button-primary">
                                        <?php _e('Start Processing', 'web-analyzer'); ?>
                                    </button>
                                    <div id="web-analyzer-bulk-status" style="margin-top: 10px; display: none;">
                                        <p><strong><?php _e('Job Status:', 'web-analyzer'); ?></strong> <span id="job-status-text">-</span></p>
                                        <p><strong><?php _e('Mode:', 'web-analyzer'); ?></strong> <span id="job-mode-text">-</span></p>
                                        <p><strong><?php _e('Progress:', 'web-analyzer'); ?></strong> <span id="job-progress">0%</span></p>
                                        <div class="progress-bar" style="background: #f0f0f0; height: 20px; width: 100%; border-radius: 3px; margin-top: 5px;">
                                            <div id="progress-bar-inner" style="background: #2271b1; height: 100%; width: 0%; border-radius: 3px;"></div>
                                        </div>
                                        <p><strong><?php _e('Items Processed:', 'web-analyzer'); ?></strong> <span id="processed-count">0</span>/<span id="total-count">0</span></p>
                                        <p><strong><?php _e('Time Elapsed:', 'web-analyzer'); ?></strong> <span id="time-elapsed">0s</span></p>
                                        <p>
                                            <button type="button" id="web-analyzer-stop-job" class="button button-secondary">
                                                <?php _e('Stop Job', 'web-analyzer'); ?>
                                            </button>
                                            <a href="#" id="view-report-link" style="margin-left: 10px; display: none;">
                                                <?php _e('View Report', 'web-analyzer'); ?>
                                            </a>
                                        </p>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <div class="web-analyzer-settings-section">
                    <h2><?php _e('Connection Test', 'web-analyzer'); ?></h2>
                    <p><?php _e('Test your connection to the Web Analyzer API.', 'web-analyzer'); ?></p>
                    
                    <div class="web-analyzer-connection-test">
                        <button type="button" id="web-analyzer-test-connection" class="button button-secondary">
                            <?php _e('Test Connection', 'web-analyzer'); ?>
                        </button>
                        <span id="web-analyzer-connection-status"></span>
                    </div>
                    
                    <div class="web-analyzer-debug-section" style="margin-top: 15px; border-top: 1px solid #ddd; padding-top: 15px;">
                        <h3><?php _e('Debug Information', 'web-analyzer'); ?></h3>
                        <p><?php _e('This section helps diagnose connection issues.', 'web-analyzer'); ?></p>
                        
                        <div class="web-analyzer-debug-controls">
                            <button type="button" id="web-analyzer-debug-test" class="button button-secondary">
                                <?php _e('Run Detailed Test', 'web-analyzer'); ?>
                            </button>
                            <button type="button" id="web-analyzer-check-env" class="button button-secondary" style="margin-left: 5px;">
                                <?php _e('Check Server Environment', 'web-analyzer'); ?>
                            </button>
                        </div>
                        
                        <div id="web-analyzer-debug-results" style="margin-top: 15px; display: none; background: #f8f8f8; padding: 10px; border: 1px solid #ddd; border-radius: 3px; white-space: pre-wrap; font-family: monospace; max-height: 300px; overflow-y: auto;">
                        </div>
                        
                        <div class="web-analyzer-debug-steps" style="margin-top: 15px; display: none;">
                            <h4><?php _e('Connection Steps', 'web-analyzer'); ?></h4>
                            <ol id="web-analyzer-debug-steps-list">
                                <li id="step-fetch" class="pending"><?php _e('Fetching API endpoint', 'web-analyzer'); ?></li>
                                <li id="step-auth" class="pending"><?php _e('Testing authentication', 'web-analyzer'); ?></li>
                                <li id="step-health" class="pending"><?php _e('Checking API health', 'web-analyzer'); ?></li>
                                <li id="step-site" class="pending"><?php _e('Verifying site configuration', 'web-analyzer'); ?></li>
                            </ol>
                        </div>
                    </div>
                </div>
                
                <?php submit_button(__('Save Settings', 'web-analyzer'), 'primary', 'submit', true); ?>
            </form>
        </div>
        
        <div class="web-analyzer-sidebar">
            <div class="web-analyzer-sidebar-box">
                <h3><?php _e('How It Works', 'web-analyzer'); ?></h3>
                <ol>
                    <li><?php _e('Configure your API connection settings above', 'web-analyzer'); ?></li>
                    <li><?php _e('Web Analyzer will appear in your post editor', 'web-analyzer'); ?></li>
                    <li><?php _e('Click "Analyze Content" to get link suggestions', 'web-analyzer'); ?></li>
                    <li><?php _e('Insert suggested links with one click', 'web-analyzer'); ?></li>
                </ol>
            </div>
            
            <div class="web-analyzer-sidebar-box">
                <h3><?php _e('Need Help?', 'web-analyzer'); ?></h3>
                <p><?php _e('If you need assistance with this plugin, please contact our support team.', 'web-analyzer'); ?></p>
                <a href="https://thevou.com/support" class="button button-secondary" target="_blank">
                    <?php _e('Get Support', 'web-analyzer'); ?>
                </a>
            </div>
        </div>
    </div>
</div>
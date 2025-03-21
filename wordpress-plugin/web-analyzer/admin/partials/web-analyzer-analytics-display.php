<?php
/**
 * Provide a admin area view for the plugin analytics
 *
 * This file is used to markup the admin-facing analytics page of the plugin.
 *
 * @since      1.0.0
 * @package    Web_Analyzer
 * @subpackage Web_Analyzer/admin/partials
 */

// Ensure this file is being included by a parent file
if (!defined('WPINC')) {
    die;
}

// Get analytics data
global $wpdb;
$table_name_suggestions = $wpdb->prefix . 'web_analyzer_suggestions';
$table_name_analytics = $wpdb->prefix . 'web_analyzer_analytics';

// Get total suggestions
$total_suggestions = $wpdb->get_var("SELECT COUNT(*) FROM $table_name_suggestions");

// Get applied suggestions
$applied_suggestions = $wpdb->get_var("SELECT COUNT(*) FROM $table_name_suggestions WHERE applied = 1");

// Get total clicks
$total_clicks = $wpdb->get_var("SELECT SUM(clicks) FROM $table_name_analytics");
$total_clicks = $total_clicks ? $total_clicks : 0;

// Get recent suggestions
$recent_suggestions = $wpdb->get_results(
    "SELECT s.*, p.post_title, a.clicks 
    FROM $table_name_suggestions s
    LEFT JOIN $wpdb->posts p ON s.post_id = p.ID
    LEFT JOIN $table_name_analytics a ON s.id = a.suggestion_id
    ORDER BY s.created_at DESC
    LIMIT 10",
    ARRAY_A
);

// Get most clicked links
$popular_links = $wpdb->get_results(
    "SELECT s.*, p.post_title, a.clicks 
    FROM $table_name_analytics a
    JOIN $table_name_suggestions s ON a.suggestion_id = s.id
    LEFT JOIN $wpdb->posts p ON s.post_id = p.ID
    WHERE a.clicks > 0
    ORDER BY a.clicks DESC
    LIMIT 10",
    ARRAY_A
);

?>

<div class="wrap">
    <h1><?php echo esc_html(get_admin_page_title()); ?></h1>
    
    <div class="web-analyzer-admin-header">
        <div class="web-analyzer-header-info">
            <h2><?php _e('Web Analyzer Analytics', 'web-analyzer'); ?></h2>
            <p><?php _e('Track performance of your internal linking strategy.', 'web-analyzer'); ?></p>
        </div>
    </div>
    
    <div class="web-analyzer-analytics-content">
        <div class="web-analyzer-analytics-summary">
            <div class="web-analyzer-card">
                <h3><?php _e('Total Suggestions', 'web-analyzer'); ?></h3>
                <div class="web-analyzer-stat"><?php echo number_format($total_suggestions); ?></div>
            </div>
            
            <div class="web-analyzer-card">
                <h3><?php _e('Applied Links', 'web-analyzer'); ?></h3>
                <div class="web-analyzer-stat"><?php echo number_format($applied_suggestions); ?></div>
                <?php if ($total_suggestions > 0) : ?>
                    <div class="web-analyzer-percentage">
                        <?php echo round(($applied_suggestions / $total_suggestions) * 100); ?>%
                    </div>
                <?php endif; ?>
            </div>
            
            <div class="web-analyzer-card">
                <h3><?php _e('Total Clicks', 'web-analyzer'); ?></h3>
                <div class="web-analyzer-stat"><?php echo number_format($total_clicks); ?></div>
                <?php if ($applied_suggestions > 0) : ?>
                    <div class="web-analyzer-avg">
                        <?php printf(__('Avg: %s per link', 'web-analyzer'), number_format($total_clicks / $applied_suggestions, 1)); ?>
                    </div>
                <?php endif; ?>
            </div>
        </div>
        
        <div class="web-analyzer-analytics-tables">
            <div class="web-analyzer-analytics-recent">
                <h3><?php _e('Recent Link Suggestions', 'web-analyzer'); ?></h3>
                
                <?php if (empty($recent_suggestions)) : ?>
                    <p><?php _e('No suggestions found.', 'web-analyzer'); ?></p>
                <?php else : ?>
                    <table class="widefat">
                        <thead>
                            <tr>
                                <th><?php _e('Date', 'web-analyzer'); ?></th>
                                <th><?php _e('Post', 'web-analyzer'); ?></th>
                                <th><?php _e('Anchor Text', 'web-analyzer'); ?></th>
                                <th><?php _e('Target URL', 'web-analyzer'); ?></th>
                                <th><?php _e('Status', 'web-analyzer'); ?></th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($recent_suggestions as $suggestion) : ?>
                                <tr>
                                    <td><?php echo date_i18n(get_option('date_format'), strtotime($suggestion['created_at'])); ?></td>
                                    <td>
                                        <a href="<?php echo get_edit_post_link($suggestion['post_id']); ?>">
                                            <?php echo esc_html($suggestion['post_title']); ?>
                                        </a>
                                    </td>
                                    <td><?php echo esc_html($suggestion['anchor_text']); ?></td>
                                    <td>
                                        <a href="<?php echo esc_url($suggestion['target_url']); ?>" target="_blank">
                                            <?php echo esc_url($suggestion['target_url']); ?>
                                        </a>
                                    </td>
                                    <td>
                                        <?php if ($suggestion['applied']) : ?>
                                            <span class="web-analyzer-status applied"><?php _e('Applied', 'web-analyzer'); ?></span>
                                        <?php else : ?>
                                            <span class="web-analyzer-status pending"><?php _e('Pending', 'web-analyzer'); ?></span>
                                        <?php endif; ?>
                                    </td>
                                </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                <?php endif; ?>
            </div>
            
            <div class="web-analyzer-analytics-popular">
                <h3><?php _e('Most Clicked Links', 'web-analyzer'); ?></h3>
                
                <?php if (empty($popular_links)) : ?>
                    <p><?php _e('No click data available yet.', 'web-analyzer'); ?></p>
                <?php else : ?>
                    <table class="widefat">
                        <thead>
                            <tr>
                                <th><?php _e('Clicks', 'web-analyzer'); ?></th>
                                <th><?php _e('Post', 'web-analyzer'); ?></th>
                                <th><?php _e('Anchor Text', 'web-analyzer'); ?></th>
                                <th><?php _e('Target URL', 'web-analyzer'); ?></th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($popular_links as $link) : ?>
                                <tr>
                                    <td><strong><?php echo number_format($link['clicks']); ?></strong></td>
                                    <td>
                                        <a href="<?php echo get_edit_post_link($link['post_id']); ?>">
                                            <?php echo esc_html($link['post_title']); ?>
                                        </a>
                                    </td>
                                    <td><?php echo esc_html($link['anchor_text']); ?></td>
                                    <td>
                                        <a href="<?php echo esc_url($link['target_url']); ?>" target="_blank">
                                            <?php echo esc_url($link['target_url']); ?>
                                        </a>
                                    </td>
                                </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                <?php endif; ?>
            </div>
        </div>
    </div>
</div>
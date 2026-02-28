<?php
/**
 * Plugin Name: WP AI Ops Meta Bridge
 * Description: Expose whitelisted SEO meta keys via REST for api-bot only.
 * Version: 0.2.0
 * Author: Local
 */

if (!defined('ABSPATH')) {
    exit;
}

function wp_aiops_meta_bridge_allowed_keys() {
    return apply_filters('wp_aiops_meta_bridge_allowed_keys', array(
        'rank_math_title',
        'rank_math_description',
        'rank_math_focus_keyword',
    ));
}

function wp_aiops_meta_bridge_bot_user() {
    return apply_filters('wp_aiops_meta_bridge_bot_user', 'api-bot');
}

function wp_aiops_meta_bridge_auth($allowed, $meta_key, $object_id, $user_id, $cap, $caps) {
    $user = get_userdata($user_id);
    if (!$user) {
        return false;
    }

    if ($user->user_login !== wp_aiops_meta_bridge_bot_user()) {
        return false;
    }

    return user_can($user_id, 'edit_post', $object_id);
}

function wp_aiops_meta_bridge_register_meta() {
    $keys = wp_aiops_meta_bridge_allowed_keys();

    foreach ($keys as $key) {
        register_post_meta('post', $key, array(
            'type' => 'string',
            'single' => true,
            'show_in_rest' => true,
            'auth_callback' => 'wp_aiops_meta_bridge_auth',
            'sanitize_callback' => 'sanitize_text_field',
        ));
        register_post_meta('page', $key, array(
            'type' => 'string',
            'single' => true,
            'show_in_rest' => true,
            'auth_callback' => 'wp_aiops_meta_bridge_auth',
            'sanitize_callback' => 'sanitize_text_field',
        ));
    }
}
add_action('init', 'wp_aiops_meta_bridge_register_meta');

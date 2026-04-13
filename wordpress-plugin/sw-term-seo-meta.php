<?php
/**
 * Snippet: sw-term-seo-meta
 * REST endpoint to write Rank Math meta for WooCommerce product categories (terms).
 *
 * POST /wp-json/sw/v1/set-term-meta
 * Body: { "term_id": 61, "title": "...", "description": "...", "keyword": "..." }
 * Header: X-SW-Token: <SW_SEO_BRIDGE_TOKEN>
 */
add_action('rest_api_init', function () {
    register_rest_route('sw/v1', '/set-term-meta', [
        'methods'             => 'POST',
        'callback'            => 'sw_set_term_seo_meta',
        'permission_callback' => '__return_true',
    ]);
});

function sw_set_term_seo_meta(WP_REST_Request $request) {
    $token    = defined('SW_SEO_BRIDGE_TOKEN') ? SW_SEO_BRIDGE_TOKEN : 'sw_seo_meta_k8x2';
    $provided = $request->get_header('X-SW-Token');
    if ($provided !== $token) {
        return new WP_Error('forbidden', 'Invalid token', ['status' => 403]);
    }

    $term_id     = intval($request->get_param('term_id'));
    $title       = sanitize_text_field($request->get_param('title') ?? '');
    $description = sanitize_textarea_field($request->get_param('description') ?? '');
    $keyword     = sanitize_text_field($request->get_param('keyword') ?? '');

    if (!$term_id) {
        return new WP_Error('missing_param', 'term_id is required', ['status' => 400]);
    }

    $updated = [];
    if ($title)       { update_term_meta($term_id, 'rank_math_title', $title);             $updated[] = 'title'; }
    if ($description) { update_term_meta($term_id, 'rank_math_description', $description); $updated[] = 'description'; }
    if ($keyword)     { update_term_meta($term_id, 'rank_math_focus_keyword', $keyword);   $updated[] = 'keyword'; }

    return rest_ensure_response([
        'success'  => true,
        'term_id'  => $term_id,
        'updated'  => $updated,
    ]);
}

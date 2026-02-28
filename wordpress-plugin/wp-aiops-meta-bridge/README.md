# WP AI Ops Meta Bridge

Minimal plugin to expose selected SEO meta keys in WordPress REST API with strict write control.

## Default exposed keys

- `rank_math_title`
- `rank_math_description`
- `rank_math_focus_keyword`

## Permission model

- Only user login `api-bot` (filterable) can write
- User must still pass `edit_post` capability checks
- Registered for `post` and `page`

## Optional: enable Yoast keys

Add this in a site snippet/plugin:

```php
add_filter('wp_aiops_meta_bridge_allowed_keys', function ($keys) {
    return array_merge($keys, array(
        'yoast_wpseo_title',
        '_yoast_wpseo_title',
        'yoast_wpseo_metadesc',
        '_yoast_wpseo_metadesc',
        'yoast_wpseo_focuskw',
        '_yoast_wpseo_focuskw',
    ));
});
```


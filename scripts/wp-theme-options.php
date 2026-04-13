<?php
/**
 * wp-theme-options.php — Flatsome theme options read/write bridge
 *
 * ⚠️  SECURITY:
 *   - Requires WP_THEME_OPTIONS_TOKEN env var set in server environment
 *   - Only accepts POST for writes; GET for reads (both require token)
 *   - Token transmitted as HTTP header X-Bridge-Token (not in URL/query string)
 *   - Writes are ALWAYS preceded by an automatic snapshot saved to disk
 *   - Rollback endpoint restores the most recent snapshot
 *   - Only operates on 'theme_mods_flatsome-child' — no other wp_options touched
 *
 * ⚠️  DEPLOY:
 *   - Upload to ~/public_html/wp-theme-options.php
 *   - Set WP_THEME_OPTIONS_TOKEN in cPanel Environment Variables (or .htaccess SetEnv)
 *   - Verify: curl -s -H "X-Bridge-Token: <token>" https://sweetsworld.com.au/wp-theme-options.php
 *     → should return {"ok":true,"action":"read","count":N}
 *
 * Actions (passed as ?action=<name>):
 *   read       GET  — return current theme_mods_flatsome-child as JSON
 *   write      POST — merge provided keys into theme_mods_flatsome-child (snapshot first)
 *   snapshot   GET  — save current options to disk, return snapshot filename
 *   rollback   POST — restore from latest snapshot (or ?snapshot=<filename>)
 *   list       GET  — list available snapshot files
 */

// ─── Bootstrap ───────────────────────────────────────────────────────────────

// Load WordPress (must be in ~/public_html)
$wp_load = __DIR__ . '/wp-load.php';
if (!file_exists($wp_load)) {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'wp-load.php not found — bridge must be in WP root']);
    exit;
}
require_once $wp_load;

header('Content-Type: application/json; charset=utf-8');

// ─── Auth ────────────────────────────────────────────────────────────────────

$expected_token = getenv('WP_THEME_OPTIONS_TOKEN');
if (empty($expected_token)) {
    http_response_code(503);
    echo json_encode(['ok' => false, 'error' => 'WP_THEME_OPTIONS_TOKEN not configured on server']);
    exit;
}

$provided_token = $_SERVER['HTTP_X_BRIDGE_TOKEN'] ?? '';
if (!hash_equals($expected_token, $provided_token)) {
    http_response_code(403);
    echo json_encode(['ok' => false, 'error' => 'Forbidden — invalid token']);
    exit;
}

// ─── Constants ───────────────────────────────────────────────────────────────

define('BRIDGE_OPTION_NAME', 'theme_mods_flatsome-child');
define('BRIDGE_SNAPSHOT_DIR', WP_CONTENT_DIR . '/uploads/skin-snapshots');

// Ensure snapshot directory exists (not web-accessible via .htaccess in uploads)
if (!is_dir(BRIDGE_SNAPSHOT_DIR)) {
    wp_mkdir_p(BRIDGE_SNAPSHOT_DIR);
    // Deny direct access
    file_put_contents(BRIDGE_SNAPSHOT_DIR . '/.htaccess', 'Deny from all');
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function bridge_read_options(): array {
    $opts = get_option(BRIDGE_OPTION_NAME, []);
    return is_array($opts) ? $opts : [];
}

function bridge_save_snapshot(string $reason = 'auto'): string {
    $ts = gmdate('Ymd\THis\Z');
    $filename = "snapshot_{$ts}_{$reason}.json";
    $path = BRIDGE_SNAPSHOT_DIR . '/' . $filename;
    $data = [
        'timestamp'     => $ts,
        'reason'        => $reason,
        'option_name'   => BRIDGE_OPTION_NAME,
        'site_url'      => get_site_url(),
        'options'       => bridge_read_options(),
    ];
    file_put_contents($path, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    return $filename;
}

function bridge_list_snapshots(): array {
    $files = glob(BRIDGE_SNAPSHOT_DIR . '/snapshot_*.json') ?: [];
    rsort($files); // newest first
    return array_map('basename', $files);
}

function bridge_load_snapshot(string $filename): array {
    // Prevent path traversal
    $filename = basename($filename);
    if (!preg_match('/^snapshot_[0-9T_Z]+.*\.json$/', $filename)) {
        return [];
    }
    $path = BRIDGE_SNAPSHOT_DIR . '/' . $filename;
    if (!file_exists($path)) {
        return [];
    }
    $data = json_decode(file_get_contents($path), true);
    return is_array($data) ? $data : [];
}

// ─── Router ──────────────────────────────────────────────────────────────────

$action = $_GET['action'] ?? 'read';
$method = $_SERVER['REQUEST_METHOD'];

switch ($action) {

    // ── READ ────────────────────────────────────────────────────────────────
    case 'read':
        $opts = bridge_read_options();
        echo json_encode([
            'ok'          => true,
            'action'      => 'read',
            'option_name' => BRIDGE_OPTION_NAME,
            'count'       => count($opts),
            'options'     => $opts,
        ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
        break;

    // ── SNAPSHOT ────────────────────────────────────────────────────────────
    case 'snapshot':
        $reason   = preg_replace('/[^a-z0-9_-]/', '', strtolower($_GET['reason'] ?? 'manual'));
        $filename = bridge_save_snapshot($reason ?: 'manual');
        echo json_encode([
            'ok'       => true,
            'action'   => 'snapshot',
            'filename' => $filename,
            'count'    => count(bridge_read_options()),
        ]);
        break;

    // ── LIST ────────────────────────────────────────────────────────────────
    case 'list':
        echo json_encode([
            'ok'        => true,
            'action'    => 'list',
            'snapshots' => bridge_list_snapshots(),
        ]);
        break;

    // ── WRITE ───────────────────────────────────────────────────────────────
    case 'write':
        if ($method !== 'POST') {
            http_response_code(405);
            echo json_encode(['ok' => false, 'error' => 'write requires POST']);
            break;
        }

        $body = file_get_contents('php://input');
        $payload = json_decode($body, true);

        if (!is_array($payload) || empty($payload['keys'])) {
            http_response_code(400);
            echo json_encode(['ok' => false, 'error' => 'payload must be JSON with "keys" object']);
            break;
        }

        $new_keys = $payload['keys'];

        // Validate: only known confirmed keys are accepted
        $allowed_keys = [
            'color_primary', 'color_alert', 'color_checkout',
            'type_nav_color', 'type_nav_color_hover', 'type_nav_bottom_color',
            'nav_position_bg', 'header_shop_bg_color', 'footer_2_bg_color',
            'header_bg', 'html_custom_css', 'html_custom_css_mobile', 'html_custom_css_tablet',
        ];
        $rejected = array_diff(array_keys($new_keys), $allowed_keys);
        if (!empty($rejected)) {
            http_response_code(400);
            echo json_encode([
                'ok'       => false,
                'error'    => 'Unknown/disallowed keys — add to allowlist in bridge first',
                'rejected' => array_values($rejected),
                'allowed'  => $allowed_keys,
            ]);
            break;
        }

        // ⚠️  MANDATORY: snapshot BEFORE any write
        $snapshot_filename = bridge_save_snapshot('pre_write');

        // Merge (patch, not replace)
        $current = bridge_read_options();
        $before  = array_intersect_key($current, $new_keys); // values being overwritten
        foreach ($new_keys as $k => $v) {
            $current[$k] = $v;
        }
        update_option(BRIDGE_OPTION_NAME, $current);

        echo json_encode([
            'ok'                => true,
            'action'            => 'write',
            'keys_written'      => array_keys($new_keys),
            'pre_write_values'  => $before,
            'snapshot_before'   => $snapshot_filename,
        ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
        break;

    // ── ROLLBACK ────────────────────────────────────────────────────────────
    case 'rollback':
        if ($method !== 'POST') {
            http_response_code(405);
            echo json_encode(['ok' => false, 'error' => 'rollback requires POST']);
            break;
        }

        $body    = file_get_contents('php://input');
        $payload = json_decode($body, true);

        // If no specific snapshot named, use latest
        $snapshots = bridge_list_snapshots();
        if (empty($snapshots)) {
            http_response_code(409);
            echo json_encode(['ok' => false, 'error' => 'No snapshots available to rollback to']);
            break;
        }
        $target_file = $payload['snapshot'] ?? $snapshots[0]; // newest
        $snapshot_data = bridge_load_snapshot($target_file);

        if (empty($snapshot_data['options'])) {
            http_response_code(404);
            echo json_encode(['ok' => false, 'error' => "Snapshot not found or empty: {$target_file}"]);
            break;
        }

        // Snapshot the current state BEFORE rollback (so rollback itself is reversible)
        $safety_snapshot = bridge_save_snapshot('pre_rollback');

        update_option(BRIDGE_OPTION_NAME, $snapshot_data['options']);

        echo json_encode([
            'ok'                    => true,
            'action'                => 'rollback',
            'restored_from'         => $target_file,
            'restored_timestamp'    => $snapshot_data['timestamp'],
            'safety_snapshot'       => $safety_snapshot,
            'keys_restored'         => count($snapshot_data['options']),
        ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
        break;

    default:
        http_response_code(400);
        echo json_encode(['ok' => false, 'error' => "Unknown action: {$action}", 'valid_actions' => ['read', 'write', 'snapshot', 'rollback', 'list']]);
        break;
}

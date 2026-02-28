<?php
/**
 * Plugin Name: Newcastle Hub Page Beautifier
 * Description: Reusable landing page skins (A/B), conditional asset loading, FAQ interaction and SVG icon sprite.
 * Version: 0.1.0
 * Author: Newcastle Hub
 */

if (!defined('ABSPATH')) {
    exit;
}

const NHPB_VERSION = '0.1.0';

function nhpb_is_test_page(): bool {
    if (!is_page()) {
        return false;
    }
    $post = get_queried_object();
    if (!$post || empty($post->post_name)) {
        return false;
    }
    return in_array($post->post_name, array('home-style', 'new-template'), true);
}

function nhpb_current_skin(): string {
    if (!is_page()) {
        return 'a';
    }
    $post = get_queried_object();
    if ($post && isset($post->post_name) && $post->post_name === 'new-template') {
        return 'b';
    }
    return 'a';
}

function nhpb_enqueue_assets(): void {
    if (!nhpb_is_test_page() && !has_shortcode(get_post_field('post_content', get_the_ID()), 'nhpb_landing')) {
        return;
    }

    $base = plugin_dir_url(__FILE__) . 'assets/';
    $skin = nhpb_current_skin();

    wp_enqueue_style('nhpb-beauty-' . $skin, $base . 'beauty-' . strtoupper($skin) . '.css', array(), NHPB_VERSION);
    wp_enqueue_script('nhpb-beauty-js', $base . 'beauty.js', array(), NHPB_VERSION, true);
}
add_action('wp_enqueue_scripts', 'nhpb_enqueue_assets');

function nhpb_script_defer($tag, $handle, $src) {
    if ($handle !== 'nhpb-beauty-js') {
        return $tag;
    }
    return '<script src="' . esc_url($src) . '" defer></script>';
}
add_filter('script_loader_tag', 'nhpb_script_defer', 10, 3);

function nhpb_preload_hero(): void {
    if (!nhpb_is_test_page()) {
        return;
    }
    $skin = nhpb_current_skin();
    $hero = plugin_dir_url(__FILE__) . 'assets/hero-' . $skin . '.svg';
    echo '<link rel="preload" as="image" href="' . esc_url($hero) . '" fetchpriority="high" />' . "\n";
}
add_action('wp_head', 'nhpb_preload_hero', 2);

function nhpb_render_icons_sprite(): void {
    if (!nhpb_is_test_page()) {
        return;
    }
    $path = plugin_dir_path(__FILE__) . 'assets/icons.svg';
    if (file_exists($path)) {
        echo file_get_contents($path); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
    }
}
add_action('wp_footer', 'nhpb_render_icons_sprite', 5);

function nhpb_icon($name): string {
    return '<svg class="nhpb-icon" aria-hidden="true"><use href="#nhpb-icon-' . esc_attr($name) . '"></use></svg>';
}

function nhpb_render_landing(string $skin): string {
    $hero = plugin_dir_url(__FILE__) . 'assets/hero-' . ($skin === 'b' ? 'b' : 'a') . '.svg';
    ob_start();
    ?>
    <div class="nhpb-root nhpb-skin-<?php echo esc_attr($skin); ?>">
      <div class="nhpb-wrap">
        <section class="nhpb-sec nhpb-hero nhpb-reveal">
          <div class="nhpb-hero-grid">
            <div>
              <span class="nhpb-badge">Newcastle Growth System</span>
              <h1 class="nhpb-title">Turn Your Website Into a Reliable Lead Engine</h1>
              <p class="nhpb-subtitle">Unified setup for website, SEO, and local conversion flow. Same brand voice, cleaner UX, faster action.</p>
              <div class="nhpb-btns">
                <a class="nhpb-btn nhpb-btn-primary" href="/free-newcastle-business-audit/">Get Free Audit</a>
                <a class="nhpb-btn nhpb-btn-secondary" href="/contact/">Book Strategy Call</a>
              </div>
            </div>
            <div>
              <img class="nhpb-hero-media" src="<?php echo esc_url($hero); ?>" width="1280" height="720" alt="Landing page layout preview" loading="eager" fetchpriority="high" decoding="async" />
            </div>
          </div>
        </section>

        <section class="nhpb-sec nhpb-reveal">
          <div class="nhpb-grid-4">
            <div class="nhpb-proof"><strong>4.9/5</strong><span>Client Satisfaction</span></div>
            <div class="nhpb-proof"><strong>120+</strong><span>Projects Delivered</span></div>
            <div class="nhpb-proof"><strong>38%</strong><span>Avg. Lead Lift</span></div>
            <div class="nhpb-proof"><strong>7 Days</strong><span>Typical Rollout</span></div>
          </div>
        </section>

        <section class="nhpb-sec nhpb-reveal">
          <h2 class="nhpb-title">What We Improve</h2>
          <div class="nhpb-grid-3">
            <article class="nhpb-card"><?php echo nhpb_icon('website'); ?><h3>Website UX</h3><p>Sharper hierarchy, cleaner section rhythm, better CTA visibility.</p></article>
            <article class="nhpb-card"><?php echo nhpb_icon('seo'); ?><h3>Local SEO</h3><p>Service intent structure, schema-ready blocks, and internal linking.</p></article>
            <article class="nhpb-card"><?php echo nhpb_icon('pos'); ?><h3>System Integration</h3><p>POS/booking/contact flow aligned with your sales operations.</p></article>
            <article class="nhpb-card"><?php echo nhpb_icon('support'); ?><h3>Support Layer</h3><p>Ongoing content tune-ups and conversion improvements each month.</p></article>
            <article class="nhpb-card"><?php echo nhpb_icon('shield'); ?><h3>Safe Deployment</h3><p>Plan-only preview, confirm gate, snapshots, and rollback support.</p></article>
            <article class="nhpb-card"><?php echo nhpb_icon('chat'); ?><h3>Sales Messaging</h3><p>Clearer value proposition for higher-quality inbound enquiries.</p></article>
          </div>
        </section>

        <section class="nhpb-sec nhpb-reveal">
          <h2 class="nhpb-title">How It Works</h2>
          <div class="nhpb-steps">
            <div class="nhpb-step"><h3>Audit</h3><p>Baseline UX, SEO, and conversion path review.</p></div>
            <div class="nhpb-step"><h3>Design</h3><p>Apply consistent module system and CTA strategy.</p></div>
            <div class="nhpb-step"><h3>Implement</h3><p>Deploy content updates with safety checks.</p></div>
            <div class="nhpb-step"><h3>Optimize</h3><p>Track, iterate, and keep improving page performance.</p></div>
          </div>
        </section>

        <section class="nhpb-sec nhpb-reveal">
          <h2 class="nhpb-title">Recent Outcomes</h2>
          <div class="nhpb-cases">
            <article class="nhpb-case"><div class="meta"><span class="delta">+41% Leads</span><h3>Restaurant Setup Page</h3><p>Improved CTA framing and support proof.</p></div></article>
            <article class="nhpb-case"><div class="meta"><span class="delta">+29% Calls</span><h3>Service Landing Revamp</h3><p>Simplified hero and tighter section flow.</p></div></article>
            <article class="nhpb-case"><div class="meta"><span class="delta">+35% Form Starts</span><h3>Audit Funnel Upgrade</h3><p>Clearer process and stronger final CTA.</p></div></article>
          </div>
        </section>

        <section class="nhpb-sec nhpb-reveal">
          <h2 class="nhpb-title">FAQ</h2>
          <div class="nhpb-faq">
            <?php
              $faqs = array(
                array('How fast can this go live?', 'Most pages are completed in 3-7 days depending on scope.'),
                array('Will this match our current brand?', 'Yes. Skin A is home-style aligned; Skin B is modern but brand-safe.'),
                array('Do you use heavy animations?', 'No. Only lightweight opacity/transform transitions.'),
                array('Can we reuse these modules?', 'Yes. Components are reusable across landing and long-form pages.'),
                array('Will this hurt page speed?', 'No. Assets are conditionally loaded, and JS stays minimal.'),
                array('Do we get rollback safety?', 'Yes. All writes are snapshot-backed and can be rolled back.')
              );
              foreach ($faqs as $faq) {
                echo '<div class="nhpb-faq-item"><button class="nhpb-faq-q" type="button" aria-expanded="false">' . esc_html($faq[0]) . '</button><div class="nhpb-faq-a"><p>' . esc_html($faq[1]) . '</p></div></div>';
              }
            ?>
          </div>
        </section>

        <section class="nhpb-sec nhpb-final nhpb-reveal">
          <h2 class="nhpb-title">Ready To Beautify Your Core Pages?</h2>
          <p>Get a practical rollout plan tailored to your current website and conversion goals.</p>
          <div class="nhpb-btns">
            <a class="nhpb-btn nhpb-btn-primary" href="/free-newcastle-business-audit/">Start Free Audit</a>
            <a class="nhpb-btn nhpb-btn-secondary" href="/contact/">Talk With Us</a>
          </div>
        </section>
      </div>
    </div>
    <?php
    return (string) ob_get_clean();
}

function nhpb_shortcode($atts): string {
    $atts = shortcode_atts(array('skin' => 'a'), $atts, 'nhpb_landing');
    $skin = strtolower((string) $atts['skin']) === 'b' ? 'b' : 'a';
    return nhpb_render_landing($skin);
}
add_shortcode('nhpb_landing', 'nhpb_shortcode');

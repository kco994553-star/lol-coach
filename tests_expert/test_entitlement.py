"""Small authored HTML fixtures; no provider calls, videos or full transcripts."""
import datetime as dt
import hashlib
import unittest

from coach_v1.expert_entitlement import verify_free_entitlement


MODEL = "gemini-3.8-flash"
BASE = "https://ai.google.dev/gemini-api/docs/"
PRICING = '''<article><div class="models-section"><div class="heading-group">
<h2 id="gemini-3.8-flash">Gemini 3.8 Flash</h2>
<em><a href="/gemini-api/docs/models/gemini-3.8-flash"><code>gemini-3.8-flash</code></a></em>
</div></div><div><devsite-selector><section><h3>Standard</h3>
<table class="pricing-table"><thead><tr><th></th><th>Free Tier</th><th>Paid Tier, per 1M tokens in USD</th></tr></thead><tbody>
<tr><td>Input price</td><td>Free of charge</td><td>$0.75</td></tr>
<tr><td>Output price (including thinking tokens)</td><td>Free of charge</td><td>$3.75</td></tr>
</tbody></table></section><section><h3>Batch</h3><table class="pricing-table"><tr><td>Not available</td></tr></table></section>
</devsite-selector></div><h2 id="other-model">Other</h2></article>'''
VIDEO = '''<article><h3 id="youtube">Pass YouTube URLs</h3>
<aside class="preview"><strong>Preview:</strong><span>The YouTube URL feature is in preview and is available at no charge.
Pricing and rate limits are likely to change.</span></aside>
<div><devsite-selector><section><h3>Python</h3><pre>Example omitted</pre></section></devsite-selector></div>
<p><strong>Limitations:</strong></p><ul>
<li>For the free tier, you can&#39;t upload more than 8 hours of YouTube video per day.</li>
<li>You can only upload public videos (not private or unlisted videos).</li></ul>
<h2 id="other-section">Other</h2></article>'''
MODELS = '''<article><h3 id="gemini-3-stable">Stable</h3><div>
<a href="/gemini-api/docs/models/gemini-3.8-flash" class="gemini-card-centered">
<h3 id="gemini-3.8-flash">Gemini 3.8 Flash</h3>
<p class="status-subtext"><span class="gemini-api-new">New</span> Stable</p></a>
</div></article>'''


class FreeEntitlementTests(unittest.TestCase):
    def verify(self, *, pricing=PRICING, video=VIDEO, models=MODELS, override=None):
        pages = dict(zip(("pricing", "video-understanding", "models"), (pricing, video, models)))
        self.calls = []
        def transport(url, *, timeout, max_bytes):
            self.calls.append((url, timeout, max_bytes))
            response = {"status": 200, "body": pages[url.rsplit("/", 1)[1]].encode(),
                        "url": url, "content_type": "text/html; charset=utf-8"}
            if override:
                response.update(override)
            return response
        return verify_free_entitlement(transport=transport,
            clock=lambda: dt.datetime(2026, 10, 12, 1, tzinfo=dt.timezone.utc))

    def test_verified_exact_scopes_and_fresh_utc_date(self):
        result = self.verify()
        self.assertEqual(result["status"], "VERIFIED_FREE")
        self.assertEqual(result["checked_at"], "2026-10-12")
        self.assertEqual(result["model"], MODEL)
        self.assertEqual(result["reasons"], ["DOCUMENTED_FREE_ENTITLEMENT"])
        self.assertEqual(set(result), {"status", "checked_at", "model", "sources", "reasons"})
        for receipt, (path, source) in zip(result["sources"],
                (("pricing", PRICING), ("video-understanding", VIDEO), ("models", MODELS))):
            self.assertEqual(receipt, {"url": BASE + path,
                "sha256": hashlib.sha256(source.encode()).hexdigest()})
        self.assertEqual(self.calls, [(BASE + p, 10, 2 * 1024 * 1024)
            for p in ("pricing", "video-understanding", "models")])

    def test_free_column_is_selected_by_header_even_when_reordered(self):
        pricing = PRICING.replace('<th>Free Tier</th><th>Paid Tier, per 1M tokens in USD</th>',
            '<th>Paid Tier, per 1M tokens in USD</th><th>Free Tier</th>')
        pricing = pricing.replace('<td>Free of charge</td><td>$0.75</td>', '<td>$0.75</td><td>Free of charge</td>')
        pricing = pricing.replace('<td>Free of charge</td><td>$3.75</td>', '<td>$3.75</td><td>Free of charge</td>')
        self.assertEqual(self.verify(pricing=pricing)["status"], "VERIFIED_FREE")

    def test_known_positive_free_tier_price_blocks_payment(self):
        for charge in ("$0.10", "$10", "$1.00 per 1M tokens"):
            with self.subTest(charge=charge):
                result = self.verify(pricing=PRICING.replace("Free of charge", charge, 1))
                self.assertEqual(result["status"], "PAID_REQUIRED")
                self.assertEqual(result["reasons"], ["FREE_TIER_POSITIVE_PRICE"])

    def test_unknown_or_zero_price_is_not_inferred_free(self):
        for cell in ("Not available", "$0.00", "Free", "$1 for selected users", "€0.10"):
            with self.subTest(cell=cell):
                self.assertEqual(self.verify(pricing=PRICING.replace("Free of charge", cell, 1))["status"], "UNKNOWN")

    def test_other_models_batch_paid_and_script_cannot_supply_evidence(self):
        variants = [PRICING.replace('id="gemini-3.8-flash"', 'id="other"'),
            PRICING.replace('<h3>Standard</h3>', '<h3>Batch</h3>'),
            PRICING.replace('<th>Free Tier</th>', '<th>Priority Tier</th>'),
            PRICING.replace('Free of charge', 'Not available') + '<script>Free of charge</script>',
            PRICING.replace('<code>gemini-3.8-flash</code>', '<code>gemini-3.6-flash</code>')]
        for pricing in variants:
            with self.subTest(pricing=pricing):
                self.assertEqual(self.verify(pricing=pricing)["status"], "UNKNOWN")

    def test_duplicate_pricing_scope_headers_rows_or_cells_are_unknown(self):
        for pricing in (PRICING + PRICING,
            PRICING.replace('<th>Free Tier</th>', '<th>Free Tier</th><th>Free Tier</th>'),
            PRICING.replace('</tbody>', '<tr><td>Input price</td><td>Free of charge</td><td>$0.75</td></tr></tbody>'),
            PRICING.replace('<td>$0.75</td>', '<td colspan="2">$0.75</td>')):
            with self.subTest(pricing=pricing):
                self.assertEqual(self.verify(pricing=pricing)["status"], "UNKNOWN")

    def test_youtube_notice_limits_and_public_scope_all_required(self):
        variants = [VIDEO.replace('id="youtube"', 'id="other"'),
            VIDEO.replace('available at no charge', 'available for a fee'),
            VIDEO.replace('8 hours', '10 hours'),
            VIDEO.replace('only upload public videos', 'upload any videos'), VIDEO + VIDEO,
            VIDEO.replace('<ul>', '<h2>Outside scope</h2><ul>')]
        for video in variants:
            with self.subTest(video=video):
                self.assertEqual(self.verify(video=video)["status"], "UNKNOWN")

    def test_matching_model_card_must_uniquely_say_stable(self):
        for models in (MODELS.replace('> Stable</p>', '> Preview</p>'),
            MODELS.replace('models/gemini-3.8-flash', 'models/gemini-3.6-flash'),
            MODELS.replace('id="gemini-3.8-flash"', 'id="other"'), MODELS + MODELS):
            with self.subTest(models=models):
                self.assertEqual(self.verify(models=models)["status"], "UNKNOWN")

    def test_http_redirect_nonhtml_utf8_oversize_fail_closed(self):
        for override in ({"status": 503}, {"status": 302}, {"url": "https://evil.invalid/"},
            {"content_type": "application/json"}, {"content_type": "text/html; charset=latin1"},
            {"body": b"\xff"}, {"body": b"x" * (2 * 1024 * 1024 + 1)}):
            with self.subTest(override={k: type(v).__name__ for k, v in override.items()}):
                self.assertEqual(self.verify(override=override)["status"], "UNKNOWN")

    def test_scope_failure_takes_precedence_over_positive_price(self):
        self.assertEqual(self.verify(pricing=PRICING.replace('Free of charge', '$0.10', 1),
            video=VIDEO.replace('8 hours', '10 hours'))["status"], "UNKNOWN")

    def test_transport_failure_is_safe_unknown(self):
        def transport(*args, **kwargs):
            raise OSError('sensitive-provider-message')
        result = verify_free_entitlement(transport=transport,
            clock=lambda: dt.datetime(2026, 10, 12, tzinfo=dt.timezone.utc))
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertNotIn('sensitive', str(result))
        self.assertEqual(result["sources"], [])

    def test_document_node_and_depth_limits(self):
        for prefix in ('<div>' * 130, '<br>' * 100_001):
            self.assertEqual(self.verify(pricing=prefix + PRICING)["status"], "UNKNOWN")

    def test_official_navigation_duplicate_analytics_attributes_are_irrelevant(self):
        nav = '<nav><a data-label="Tab" data-label="Responsive Tab" href="/">Menu</a></nav>'
        self.assertEqual(self.verify(pricing=nav + PRICING, video=nav + VIDEO,
            models=nav + MODELS)["status"], "VERIFIED_FREE")
        self.assertEqual(self.verify(pricing=PRICING.replace('id="gemini-3.8-flash"',
            'id="other" id="gemini-3.8-flash"'))["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()

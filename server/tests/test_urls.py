from app.providers import parse_product_url
def test_amazon(): assert parse_product_url("https://www.amazon.in/dp/B0ABC12345?tag=x")==("amazon_in","B0ABC12345")
def test_flipkart(): assert parse_product_url("https://www.flipkart.com/item/p/itmabc?pid=ABC123")==("flipkart","ABC123")
def test_reject():
    import pytest
    with pytest.raises(ValueError): parse_product_url("https://example.com/item")


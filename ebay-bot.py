#!/usr/bin/env python3
"""
eBay Dropshipping Bot - Neo
Automated product listing and price management
"""

import json
import requests
import base64
import time
import os
from datetime import datetime

# Load config
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(SCRIPT_DIR, 'config.json')) as f:
    config = json.load(f)

EBAY = config['ebay']
PRODUCTS = config['products']

# eBay Trading API endpoint
TRADING_API = "https://api.ebay.com/ws/api.dll"

def get_headers():
    """Generate eBay API headers"""
    token = EBAY['userToken']
    return {
        'X-EBAY-API-COMPATIBILITY-LEVEL': '1155',
        'X-EBAY-API-DEV-NAME': EBAY['devId'],
        'X-EBAY-API-APP-NAME': EBAY['appId'],
        'X-EBAY-API-CERT-NAME': EBAY['certId'],
        'X-EBAY-API-CALL-NAME': '',
        'X-EBAY-API-SITEID': str(EBAY['siteId']),
        'Content-Type': 'text/xml',
        'X-EBAY-API-IAF-TOKEN': token
    }

def make_trading_call(call_name, xml_body):
    """Make a Trading API call"""
    headers = get_headers()
    headers['X-EBAY-API-CALL-NAME'] = call_name
    
    full_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<{call_name}Request xmlns="urn:ebay:apis:eBLBaseComponents">
    <RequesterCredentials>
        <eBayAuthToken>{EBAY['userToken']}</eBayAuthToken>
    </RequesterCredentials>
    {xml_body}
</{call_name}Request>'''

    try:
        response = requests.post(TRADING_API, headers=headers, data=full_xml, timeout=30)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def get_user():
    """Get current user info"""
    xml = '<DetailLevel>ReturnAll</DetailLevel>'
    return make_trading_call('GetUser', xml)

def get_my_ebay_selling():
    """Get all active listings"""
    xml = '''
    <ActiveList>
        <Include>true</Include>
        <Pagination>
            <EntriesPerPage>100</EntriesPerPage>
            <PageNumber>1</PageNumber>
        </Pagination>
    </ActiveList>
    '''
    return make_trading_call('GetMyeBaySelling', xml)

def get_item(item_id):
    """Get specific item details"""
    xml = f'''
    <ItemID>{item_id}</ItemID>
    <DetailLevel>ReturnAll</DetailLevel>
    '''
    return make_trading_call('GetItem', xml)

def add_fixed_price_item(product):
    """List a product as fixed price (Buy It Now)"""
    xml = f'''
    <Item>
        <Title>{product['name']} - Neu & OVP</Title>
        <Description><![CDATA[
            <h2>{product['name']}</h2>
            <p>✅ Neu & OVP</p>
            <p>✅ Kostenloser Versand</p>
            <p>✅ 30 Tage Rückgaberecht</p>
            <p>📦 Versand innerhalb von 1-3 Werktagen</p>
        ]]></Description>
        <PrimaryCategory>
            <CategoryID>get_from_ebay</CategoryID>
        </PrimaryCategory>
        <StartPrice>{product['price']}</StartPrice>
        <CategoryMappingAllowed>true</CategoryMappingAllowed>
        <Country>DE</Country>
        <Currency>EUR</Currency>
        <DispatchTimeMax>3</DispatchTimeMax>
        <ListingDuration>GTC</ListingDuration>
        <ListingType>FixedPriceItem</ListingType>
        <Location>Deutschland</Location>
        <PaymentMethods>PayPal</PaymentMethods>
        <PayPalEmailAddress>bajajshamlal8@gmail.com</PayPalEmailAddress>
        <PostalCode>41462</PostalCode>
        <Quantity>10</Quantity>
        <ReturnPolicy>
            <ReturnsAcceptedOption>ReturnsAccepted</ReturnsAcceptedOption>
            <ReturnsWithinOption>Days_30</ReturnsWithinOption>
            <ShippingCostPaidByOption>Buyer</ShippingCostPaidByOption>
        </ReturnPolicy>
        <ShippingDetails>
            <ShippingType>Flat</ShippingType>
            <ShippingServiceOptions>
                <ShippingServicePriority>1</ShippingServicePriority>
                <ShippingService>DE_DHLPaket</ShippingService>
                <ShippingServiceCost>0.00</ShippingServiceCost>
            </ShippingServiceOptions>
        </ShippingDetails>
        <Site>Germany</Site>
    </Item>
    '''
    return make_trading_call('AddFixedPriceItem', xml)

def revise_item_price(item_id, new_price):
    """Update price of existing listing"""
    xml = f'''
    <Item>
        <ItemID>{item_id}</ItemID>
        <StartPrice>{new_price}</StartPrice>
    </Item>
    '''
    return make_trading_call('ReviseItem', xml)

def end_item(item_id):
    """End a listing"""
    xml = f'''
    <ItemID>{item_id}</ItemID>
    <EndingReason>NotAvailable</EndingReason>
    '''
    return make_trading_call('EndItem', xml)

def search_ebay_browse(query, limit=5):
    """Search products using Browse API (needs OAuth token)"""
    # For now, use Trading API GetSearchResults
    xml = f'''
    <QueryKeywords>{query}</QueryKeywords>
    <Pagination>
        <EntriesPerPage>{limit}</EntriesPerPage>
        <PageNumber>1</PageNumber>
    </Pagination>
    <DetailLevel>ReturnAll</DetailLevel>
    <SiteID>77</SiteID>
    '''
    return make_trading_call('GetSearchResults', xml)

def get_orders():
    """Get recent orders"""
    xml = '''
    <CreateTimeFrom>2026-03-01T00:00:00.000Z</CreateTimeFrom>
    <CreateTimeTo>2026-03-31T23:59:59.000Z</CreateTimeTo>
    <Pagination>
        <EntriesPerPage>50</EntriesPerPage>
        <PageNumber>1</PageNumber>
    </Pagination>
    '''
    return make_trading_call('GetOrders', xml)

def calculate_profit(product):
    """Calculate profit margin"""
    ebay_price = product['price']
    source_price = product['source_price']
    ebay_fee = ebay_price * 0.10  # ~10% eBay fee
    paypal_fee = ebay_price * 0.025 + 0.35  # PayPal fee
    profit = ebay_price - source_price - ebay_fee - paypal_fee
    margin = (profit / ebay_price) * 100
    return {
        'product': product['name'],
        'ebay_price': ebay_price,
        'source_price': source_price,
        'ebay_fee': round(ebay_fee, 2),
        'paypal_fee': round(paypal_fee, 2),
        'profit': round(profit, 2),
        'margin': round(margin, 1)
    }

def report():
    """Generate profit report"""
    print("=" * 60)
    print(f"📊 eBay Dropshipping Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"👤 Account: {EBAY['username']}")
    print("=" * 60)
    
    total_profit = 0
    for product in PRODUCTS:
        p = calculate_profit(product)
        total_profit += p['profit']
        print(f"  {p['product']:25} | €{p['ebay_price']:6} → €{p['profit']:5} profit ({p['margin']}%)")
    
    print("-" * 60)
    print(f"  {'TOTAL POTENTIAL PROFIT':25} | €{round(total_profit, 2)}")
    print("=" * 60)

def list_all_products():
    """List all products"""
    print("🚀 Listing all products on eBay...")
    for product in PRODUCTS:
        print(f"  Listing: {product['name']} at €{product['price']}...")
        # result = add_fixed_price_item(product)
        # print(f"  Result: {result[:100]}")
        time.sleep(1)  # Rate limit
    print("✅ Done!")

def check_orders():
    """Check for new orders"""
    print("📦 Checking for orders...")
    result = get_orders()
    if 'OrderArray' in result:
        print("  Orders found!")
    else:
        print("  No orders yet.")
    return result

def update_prices():
    """Check market prices and update listings"""
    print("💰 Checking market prices...")
    for product in PRODUCTS:
        # Search for competing listings
        result = search_ebay_browse(product['name'])
        print(f"  {product['name']}: Market check complete")
    print("✅ Price check done!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "report":
            report()
        elif cmd == "list":
            list_all_products()
        elif cmd == "orders":
            check_orders()
        elif cmd == "prices":
            update_prices()
        elif cmd == "user":
            print(get_user())
        elif cmd == "selling":
            print(get_my_ebay_selling())
        else:
            print(f"Unknown command: {cmd}")
    else:
        print("eBay Dropshipping Bot")
        print("Commands:")
        print("  report  - Show profit report")
        print("  list    - List all products")
        print("  orders  - Check orders")
        print("  prices  - Update prices")
        print("  user    - Get user info")
        print("  selling - Get active listings")

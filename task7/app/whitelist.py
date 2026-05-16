_ALLOWED = {
'products': ['id','category_id','sku','name','price','stock'],
'customers': ['id','email','full_name','phone'],
'orders': ['id','customer_id','created_at','status'],
'order_items': ['id','order_id','product_id','quantity','unit_price'],
'categories': ['id','name']
}
def get_allowed_columns():
    return _ALLOWED